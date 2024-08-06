import os
import logging
import pathlib
import re
import sys
from typing import Optional, List, cast
import nox

ci_logger = logging.getLogger("CI logger")
ci_handler = logging.StreamHandler(stream=sys.stdout)
ci_handler.formatter = logging.Formatter("%(msg)s")
ci_logger.handlers.append(ci_handler)
ci_logger.propagate = False

nox.options.reuse_existing_virtualenvs = True
nox.options.sessions = [
    "ruff_format",
    "ruff_lint",
    "mypy",
    "check_yaml",
    "check_json",
    "check_toml",
    "check_eof",
    "check_trailing_space",
    "check_lf",
]

SUPPORTED_PY_VER = list(f"3.{x}" for x in range(9, 13))


@nox.session
def ruff_format(session: nox.Session):
    """Checks formatting with ruff"""
    session.install("-r", "requirements/dev-ruff.txt")
    session.run("ruff", "format", "--diff")


@nox.session
def ruff_lint(session: nox.Session):
    """Run ruff as linter"""
    session.install("-r", "requirements/dev-ruff.txt")
    session.run("ruff", "check")


@nox.session(python=False)
def mypy(session: nox.Session):
    """Run mypy using in default env"""
    session.run("pip", "install", "-r", "requirements/dev-mypy.txt")
    session.run("mypy")


PRE_EXCLUDE = re.compile(
    "|".join(
        [
            "\\.git/",
            "^\\.(?:mypy|ruff|pytest|eslint)_?cache",
            "^(?:\\.nox|\\.?env|\\.?venv)",
            "^\\.coverage.*",
            "^htmlcov/",
            "__pycache__",
            "^src",
            "^sphinx_immaterial/(?:\\.icons|bundles|static|.*\\.html)",
            "^tests/issue_134/.*(?:/build|\\.egg\\-info)",
            "^node_modules",
            "^docs/(?:_build|\\w+_apigen_generated)",
            ".*\\.(?:woff2?|ico|xcf|gif|jpg|png)$",
        ]
    )
)


def get_file_list(ext: str, exclude: Optional[re.Pattern] = None) -> List[str]:
    """Get a list of file using the specified extension relative to the working dir.

    :param ext: A glob pattern used as the file extension.
    :param exclude: A compiled regular expression used as an exclusion filter.

    :returns:
        A list of strings that represent paths relative to working dir.

        .. note::
            These paths use posix path delimiters (``/``) despite the OS.
            This allows for easier regex patterns passed to ``exclude``.
    """
    files = [
        x.as_posix()
        for x in pathlib.Path().glob(f"**/*.{ext}")
        if PRE_EXCLUDE.search(x.as_posix()) is None and (x.is_file() or x.is_symlink())
    ]
    if exclude is not None:
        files = list(filter(lambda x: exclude.search(x) is None, files))
    return files


@nox.session
def check_yaml(session: nox.Session):
    """Check for yaml syntax errors."""
    session.install("-r", "requirements/dev-pre_commit_hooks.txt")
    yml_exclude = re.compile("^tests/snapshots")
    yaml_files = get_file_list("yaml", exclude=yml_exclude)
    yaml_files += get_file_list("yml", exclude=yml_exclude)
    session.run("check-yaml", *yaml_files)


@nox.session
def check_json(session: nox.Session):
    """Check for json syntax errors."""
    session.install("-r", "requirements/dev-pre_commit_hooks.txt")
    json_files = get_file_list("json", re.compile("^tsconfig.json$"))
    session.run("check-json", *json_files)


@nox.session
def check_toml(session: nox.Session):
    """Check for toml syntax errors."""
    session.install("-r", "requirements/dev-pre_commit_hooks.txt")
    toml_files = get_file_list("toml")
    session.run("check-toml", *toml_files)


@nox.session
def check_eof(session: nox.Session):
    """Ensure EoF is a single blank line."""
    session.install("-r", "requirements/dev-pre_commit_hooks.txt")
    eof_exclude = re.compile("^typings/.*|tests/snapshots/.*|^tsconfig.json$|.*\\.svg$")
    eof_files = get_file_list("*", exclude=eof_exclude)
    # error output is super long and unhelpful; we only need the stdout in case of error
    ret = session.run(
        "end-of-file-fixer", *eof_files, silent=True, success_codes=[0, 1]
    )
    if ret:
        session.error("\n" + ret)


@nox.session
def check_trailing_space(session: nox.Session):
    """Ensure no trailing whitespace."""
    session.install("-r", "requirements/dev-pre_commit_hooks.txt")
    all_files = get_file_list("*", exclude=re.compile("tests/snapshots/.*"))
    # error output is super long and unhelpful; we only need the stdout in case of error
    ret = session.run(
        "trailing-whitespace-fixer", *all_files, silent=True, success_codes=[0, 1]
    )
    if ret:
        session.error("\n" + ret)


@nox.session
def check_lf(session: nox.Session):
    """ensure LF used."""
    session.install("-r", "requirements/dev-pre_commit_hooks.txt")
    all_files = get_file_list("*")
    # error output is super long and unhelpful; we only need the stdout in case of error
    ret = session.run(
        "mixed-line-ending", "--fix=lf", *all_files, silent=True, success_codes=[0, 1]
    )
    if ret:
        session.error("\n" + ret)


@nox.session(python=False)
@nox.parametrize(
    "cmd",
    ["sdist", "bdist_wheel", "--version"],
    ids=["src", "wheel", "version"],
)
def dist(session: nox.Session, cmd: str):
    """Create distributions."""
    session.run("pip", "install", "wheel", "setuptools_scm", "setuptools>=42")
    github_output = os.environ.get("GITHUB_OUTPUT", None)
    if cmd == "--version":
        version = cast(str, session.run("python", "setup.py", "--version", silent=True))
        version = version.splitlines()[-1].strip()
        if github_output is not None:
            with open(github_output, "a", encoding="utf-8") as output:
                output.write(f"version={version}\n")
        session.log("Package version: %s", version)
        return
    session.run("python", "setup.py", cmd)
    if cmd == "bdist_wheel":
        deployable = list(pathlib.Path().glob("dist/*.whl"))[0]
        if github_output is not None:
            with open(github_output, "a", encoding="utf-8") as output:
                output.write(f"wheel={deployable}\n")
    else:
        deployable = list(pathlib.Path().glob("dist/*.tar.*"))[0]
    session.log("Created distribution: %s", deployable)


@nox.session(python=False)
@nox.parametrize(
    "builder", ["html", "dirhtml", "latex"], ids=["html", "dirhtml", "latex"]
)
def docs(session: nox.Session, builder: str):
    """Build docs."""
    ci_logger.info(f"::group::Using {builder} builder")
    session.run("pip", "install", "-r", "docs/requirements.txt")
    session.run(
        "sphinx-build",
        "-b",
        builder,
        "-W",
        "--keep-going",
        "-T",
        "docs",
        f"docs/_build/{builder}",
    )
    ci_logger.info("::endgroup::")


SUPPORTED_SPHINX = [4, 5, 6, 7, 8]


@nox.session
@nox.parametrize(
    "python,sphinx",
    [
        (py, sphinx)
        for py in SUPPORTED_PY_VER
        for sphinx in SUPPORTED_SPHINX
        if (sphinx, py) != (8, "3.9")  # python v3.9 support dropped in sphinx v8
    ],
)
def tests(session: nox.Session, sphinx: int):
    """Run unit tests and collect code coverage analysis."""
    ci_logger.info(f"::group::Using sphinx v{sphinx} and python v{session.python}")
    if not pathlib.Path("node_modules").exists():
        session.run("npm", "install", external=True)
    if not list(pathlib.Path().glob("sphinx_immaterial/*.html")):
        session.run("npm", "run", "build", external=True)
    sphinx_version = "sphinx>={},<{}".format(
        str(sphinx) if sphinx > 4 else "4.5", sphinx + 1
    )
    session.install(sphinx_version)
    if sphinx < 5:
        # sphinxcontrib deps that dropped support for sphinx v4.x
        session.install("-r", "tests/requirements-sphinx4.txt")
    session.install("-r", "tests/requirements.txt")
    session.run("coverage", "run", "-m", "pytest", "-vv", "-s", "--durations=5")
    # session.notify("docs") <- only calls docs(html), not dirhtml or latex builders
    ci_logger.info("::endgroup::")


@nox.session
def coverage(session: nox.Session):
    """Create coverage report."""
    session.install("coverage[toml]>=7.0")
    session.run("coverage", "combine")
    total = int(
        cast(str, session.run("coverage", "report", "--format=total", silent=True))
    )
    md = session.run("coverage", "report", "--format=markdown", silent=True)
    pathlib.Path(".coverage_.md").write_text(
        f"<details><summary>Coverage is {total}%</summary>\n\n{md}\n\n</details>",
        encoding="utf-8",
    )
    session.run("coverage", "xml")
    session.log("Coverage is %d%%", total)
