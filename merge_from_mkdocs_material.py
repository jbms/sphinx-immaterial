#!/usr/bin/env python3
"""Applies changes from mkdocs-material to the current directory.

The upstream mkdocs-material revision on which the current directory is based is
assumed to be stored in the MKDOCS_MATERIAL_MERGE_BASE file.

This script computes the differences between that revision and the current
master branch, and then applies them to the current directory via 3-way merge.
If there are conflicts, conflict markers are left in modified files.

Files without conflicts are staged automatically via `git add`.

.. note::
    This script must be run in a Linux shell because:

    1. The use of `git apply` within a context manager (`with` block) results in an
       error saying "Permission Denied". This because git is trying to open a file that
       is already opened by the python interpreter. This is a common obstacle when using
       `tempfile` module on Windows.
    2. There is no `patch` CLI tool native to Windows. Alternatively, we could try using
       a port from the `gnuwin32 <http://gnuwin32.sourceforge.net/packages/patch.htm>`_
       project, but it requires an extra install on user's behalf.
"""

import argparse
import contextlib
import json
import os
import pathlib
import subprocess
import tempfile
from typing import Optional

MKDOCS_EXCLUDE_PATTERNS = [
    # mkdocs-specific configuration files
    ".gitignore",
    ".gitattributes",
    ".github",
    ".browserslistrc",
    ".dockerignore",
    "requirements.txt",
    "setup.py",
    "Dockerfile",
    "MANIFEST.in",
    ".vscode",
    ".devcontainer",
    # Generated files
    "material",
    # mkdocs-specific files
    "src/**/*.py",
    "src/mkdocs_theme.yml",
    "src/404.html",
    "mkdocs.yml",
    # Unneeded files
    "typings/lunr",
    "src/assets/javascripts/browser/worker",
    "src/templates/assets/javascripts/browser/worker",
    "src/assets/javascripts/integrations/search/worker",
    "src/templates/assets/javascripts/integrations/search/worker",
    # Files specific to mkdocs' own documentation
    "src/overrides",
    "src/assets/images/favicon.png",
    "src/templates/assets/images/favicon.png",
    "src/.icons/logo*",
    "src/templates/.icons/logo*",
    "docs",
    "LICENSE",
    "CHANGELOG",
    "package-lock.json",
    "*.md",
    "giscus.json",
    "pyproject.toml",
]

ap = argparse.ArgumentParser()
ap.add_argument(
    "--clone-dir",
    default="/tmp/mkdocs-material",
    help="Temporary directory used for pristine checkout of mkdocs-material.  "
    "This remains as a cache after this script completes even if "
    "`--keep-temp` is not specified.",
)
ap.add_argument(
    "--patch-output",
    default="/tmp/mkdocs-material-patch",
    help="Path where patch is written.",
)
ap.add_argument("--source-ref", default="origin/master")
ap.add_argument("--keep-temp", action="store_true", help="Keep temporary workdir")
ap.add_argument(
    "--dry-run", action="store_true", help="Just print the patch but do not apply."
)
args = ap.parse_args()
source_ref = args.source_ref

script_dir = os.path.dirname(__file__)

merge_base_path = os.path.join(script_dir, "MKDOCS_MATERIAL_MERGE_BASE")
merge_base = pathlib.Path(merge_base_path).read_text(encoding="utf-8").strip()

clone_dir = args.clone_dir

if not os.path.exists(clone_dir):
    subprocess.run(
        ["git", "clone", "https://github.com/squidfunk/mkdocs-material", clone_dir],
        check=True,
    )
else:
    subprocess.run(
        ["git", "fetch", "origin"],
        cwd=clone_dir,
        check=True,
    )


def _fix_package_json(path: pathlib.Path) -> None:
    content = json.loads(path.read_text(encoding="utf-8"))
    content.pop("version", None)
    content["dependencies"].pop("lunr")
    content["dependencies"].pop("fuzzaldrin-plus")
    content["dependencies"].pop("lunr-languages")
    content["devDependencies"].pop("@types/lunr")
    content["devDependencies"].pop("@types/fuzzaldrin-plus")
    path.write_text(json.dumps(content, indent=2) + "\n", encoding="utf-8")


def _resolve_ref(ref: str) -> str:
    return subprocess.run(
        ["git", "rev-parse", ref],
        encoding="utf-8",
        cwd=clone_dir,
        check=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()


@contextlib.contextmanager
def _temp_worktree_path():
    if args.keep_temp:
        temp_workdir = tempfile.mkdtemp()
        yield temp_workdir
        return
    with tempfile.TemporaryDirectory() as temp_workdir:
        try:
            yield temp_workdir
        finally:
            subprocess.run(
                ["git", "worktree", "remove", "--force", temp_workdir],
                cwd=clone_dir,
                check=True,
            )


def _create_adjusted_commit(
    ref: str, temp_workdir: str, message: str, parent: Optional[str] = None
) -> str:
    print(f"Checking out {source_ref} -> {temp_workdir}")
    subprocess.run(
        ["git", "worktree", "add", "--detach", temp_workdir, ref],
        cwd=clone_dir,
        check=True,
    )
    exclude = []
    # filter out exclude patterns for paths that don't exist in the temp_workdir
    for pattern in MKDOCS_EXCLUDE_PATTERNS:
        for file in pathlib.Path(temp_workdir).rglob(pattern):
            exclude.append(str(file))
    subprocess.run(
        ["git", "rm", "--quiet", "-r"] + exclude,
        cwd=temp_workdir,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    _fix_package_json(pathlib.Path(temp_workdir) / "package.json")
    subprocess.run(["git", "update-index"], cwd=temp_workdir, check=True)
    tree = subprocess.run(
        ["git", "write-tree"],
        cwd=temp_workdir,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    ).stdout.strip()
    commit = subprocess.run(
        ["git", "commit-tree", tree, "-m", message]
        + (["-p", parent] if parent is not None else []),
        cwd=temp_workdir,
        stdout=subprocess.PIPE,
        check=True,
        text=True,
    ).stdout.strip()
    subprocess.run(["git", "reset", "--hard", commit], cwd=temp_workdir, check=True)
    return commit


def _get_git_status(workdir: str):
    status_output = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", "--no-renames"],
        stdout=subprocess.PIPE,
        check=True,
        text=True,
        cwd=workdir,
    ).stdout
    result = {}
    for line in status_output.split("\x00"):
        if not line:
            continue
        status_code = line[:2]
        filename = line[3:]
        result[filename] = status_code
    return result


def _characterize_git_status(file_status):
    conflicts = []
    updated = []
    for filename, status in file_status.items():
        if "U" in status:
            conflicts.append(filename)
            continue
        if status != "  ":
            updated.append(filename)
        else:
            print(filename, "has unexpected status", repr(status))
    return updated, conflicts


def main():
    resolved_source_ref = _resolve_ref(args.source_ref)
    print(f"SHA for source_ref {args.source_ref} is {resolved_source_ref}")

    patch_path = os.path.abspath(args.patch_output)
    if not os.path.exists(patch_path):
        os.makedirs(patch_path)
    patch_path = os.path.join(patch_path, "patch_info.diff")

    with _temp_worktree_path() as temp_workdir:
        print(f"\nCreating adjusted commit for original upstream {merge_base}")
        old_tree_commit = _create_adjusted_commit(
            merge_base,
            temp_workdir,
            message=f"Original upstream {merge_base} (adjusted)",
        )

        print("\nCreating adjusted commit for sphinx-immaterial")
        subprocess.run(
            ["git", "remote", "rm", "local-sphinx-immaterial"],
            cwd=temp_workdir,
            check=False,
        )
        subprocess.run(
            ["git", "remote", "add", "local-sphinx-immaterial", script_dir],
            cwd=temp_workdir,
            check=True,
        )
        subprocess.run(
            ["git", "fetch", "local-sphinx-immaterial", "HEAD"],
            cwd=temp_workdir,
            check=True,
        )
        sphinx_immaterial_commit = subprocess.run(
            [
                "git",
                "commit-tree",
                "FETCH_HEAD^{tree}",
                "-p",
                old_tree_commit,
                "-m",
                "Adjusted sphinx-immaterial",
            ],
            cwd=temp_workdir,
            stdout=subprocess.PIPE,
            text=True,
            check=True,
        ).stdout.strip()
        subprocess.run(
            ["git", "reset", "--hard", sphinx_immaterial_commit],
            cwd=temp_workdir,
            check=True,
        )

        print(f"\nCreating adjusted commit for updated upstream {resolved_source_ref}")
        with _temp_worktree_path() as temp_workdir2:
            new_tree_commit = _create_adjusted_commit(
                resolved_source_ref,
                temp_workdir2,
                message=f"Updated upstream {resolved_source_ref} (adjusted)",
                parent=old_tree_commit,
            )

        print("\nRebasing")
        subprocess.run(["git", "rebase", new_tree_commit, "HEAD"], cwd=temp_workdir)

        with open(patch_path, "wb") as patch_f:
            subprocess.run(
                ["git", "diff", sphinx_immaterial_commit],
                check=True,
                cwd=temp_workdir,
                stdout=patch_f,
            )
        file_status = _get_git_status(temp_workdir)

    updated_files, conflict_files = _characterize_git_status(file_status)

    print("Patch in: " + patch_path)

    if not args.dry_run:
        print("\nApplying patch file to sphinx-immaterial repo.")
        # LINUX ONLY - the `patch` cmd doesn't have a native equivalent on Windows.
        with open(patch_path, "rb") as std_in_file:
            subprocess.run(
                ["patch", "-p1"], stdin=std_in_file, check=True, cwd=script_dir
            )
        if updated_files:
            print("\nStaging non-conflicting files.")
            subprocess.run(
                ["git", "add", "--"] + updated_files, check=True, cwd=script_dir
            )
        else:
            print("There are no files to update.")
        pathlib.Path(merge_base_path).write_text(
            resolved_source_ref + "\n", encoding="utf-8"
        )
    else:
        print(pathlib.Path(patch_path).read_text(encoding="utf-8"))

    if conflict_files:
        print("File with conflicts:")
        for filename in conflict_files:
            print(f"{file_status[filename]} {filename}")


if __name__ == "__main__":
    main()
