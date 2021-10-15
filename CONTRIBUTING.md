# General Procedure

1. Check all issues (open and closed) to see if your query has been previously raised, mentioned or discussed at all.
2. Open an issue if your query has not been previously addressed.
3. If a solution is found, and requires changes to this repository, then submit a Pull Request.

## Unwanted changes

Anything contained within the _src_ folder is meant to be marged from the upstream mkdocs-material repo. As such, it is discouraged from making any changes that might cause a merge conflict when new changes are pulled from the upstream repository.

There is no intention to support any mkdocs extensions in this theme because this theme is designed for the Sphinx documentation generator. You will often find that most of the extensions available for mkdocs are natively implemented in Sphinx or available in the form of a Sphinx extension.

## Code style

We use linters to keep our code style conventional. Thus, this repository is setup to use many of the popular linting and code formatting tools available.

Please be sure to review/format your code changes in accordance with the style guides incorporated in this repository (which are typically named _.**rc_).
