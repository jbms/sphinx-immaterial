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
import shutil
import subprocess
import tempfile

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
    # Generated files
    "material",
    # mkdocs-specific files
    "src/*.py",
    "src/mkdocs_theme.yml",
    "src/404.html",
    "mkdocs.yml",
    # Unneeded files
    "typings/lunr",
    "src/assets/javascripts/browser/worker",
    "src/assets/javascripts/integrations/search/worker",
    # Files specific to mkdocs' own documentation
    "src/overrides",
    "src/assets/images/favicon.png",
    "src/.icons/logo.*",
    "docs",
    "LICENSE",
    "CHANGELOG",
    "package-lock.json",
    "*.md",
    "giscus.json",
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


def _create_adjusted_tree(ref: str, temp_workdir: str) -> str:
    print(f"Checking out {source_ref} -> {temp_workdir}")
    subprocess.run(
        ["git", "worktree", "add", "--detach", temp_workdir, ref],
        cwd=clone_dir,
        check=True,
    )
    subprocess.run(
        ["git", "rm", "--quiet", "-r"] + MKDOCS_EXCLUDE_PATTERNS,
        cwd=temp_workdir,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    _fix_package_json(pathlib.Path(temp_workdir) / "package.json")
    try:
        subprocess.run(
            ["git", "commit", "--no-verify", "-a", "-m", "Exclude files"],
            cwd=temp_workdir,
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        # `git commit` fails if user info not in `git config` -> provide verbosity
        raise RuntimeError(str(exc.stderr, encoding="utf-8")) from exc
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=temp_workdir,
        check=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
    ).stdout.strip()


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
    return updated, conflicts


def main():
    resolved_source_ref = _resolve_ref(args.source_ref)
    print(f"SHA for source_ref {args.source_ref} is {resolved_source_ref}")

    print("\nGetting mkdocs-material repo ready")
    with _temp_worktree_path() as temp_workdir:
        new_tree_commit = _create_adjusted_tree(resolved_source_ref, temp_workdir)

    patch_path = os.path.abspath(args.patch_output)
    if not os.path.exists(patch_path):
        os.makedirs(patch_path)
    patch_path += os.sep + "patch_info.diff"

    print("\nGetting sphinx-immaterial repo ready")
    with _temp_worktree_path() as temp_workdir:
        print("    creating a temp workspace")
        old_tree_commit = _create_adjusted_tree(merge_base, temp_workdir)
        subprocess.run(
            ["git", "rm", "-r", "."],
            cwd=temp_workdir,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print("    copying files to the temp workspace.")
        shutil.copytree(
            script_dir,
            temp_workdir,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns(
                ".git",
                "node_modules",
                ".icons",
                "_build",
            ),
        )
        print("    creating a local-only commit")
        subprocess.run(
            ["git", "add", "-A", "--force", "."],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=temp_workdir,
            check=True,
        )
        subprocess.run(
            ["git", "commit", "--no-verify", "-a", "-m", "Working changes"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=temp_workdir,
            check=True,
        )

        print("\nCreating a diff report")
        with tempfile.NamedTemporaryFile(mode="wb") as patch_f:
            subprocess.run(
                ["git", "diff", f"{old_tree_commit}..{new_tree_commit}"],
                cwd=clone_dir,
                stdout=patch_f,
                check=True,
            )
            patch_f.flush()

            try:
                print("\nCreating a patch report")
                subprocess.run(
                    ["git", "apply", "--3way", patch_f.name],
                    check=True,
                    cwd=temp_workdir,
                    capture_output=True,
                )
            except subprocess.CalledProcessError as exc:
                # provide a verbose coherent output from `git apply` when problematic.
                output = str(exc.stdout, encoding="utf-8").replace("\n", "\n   ")
                output += str(exc.stderr, encoding="utf-8").replace("\n", "\n   ")
                print(f"`{' '.join(exc.cmd)}` returned {exc.returncode}\n   {output}")

        with open(patch_path, "wb") as patch_f:
            subprocess.run(
                ["git", "diff", "HEAD"], check=True, cwd=temp_workdir, stdout=patch_f
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
        print("\nStaging non-conflicting files.")
        subprocess.run(["git", "add", "--"] + updated_files, check=True, cwd=script_dir)
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
