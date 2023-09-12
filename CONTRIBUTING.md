# General Procedure

1. Check all issues (open and closed) to see if your query has been previously raised, mentioned or discussed at all.
2. Open an issue if your query has not been previously addressed.
3. If a solution is found, and requires changes to this repository, then submit a Pull Request.

## Code style

We use linters to keep our code style conventional. Thus, this repository is setup to use many of the popular linting and code formatting tools available.

Please be sure to review/format your code changes in accordance with the style guides incorporated in this repository (which are typically named _.**rc_).

### Using `nox` & `npm`

Most of our CI uses a program utility called `nox`.
For JS and SCSS checking, we use `npm` tasks.

#### Run type checkers and formatters for Python

Be sure `nox` is installed via `pip install nox`.

From the repository root directory:

```shell
nox
```

More info is available via `nox -h` or [their documentation](https://nox.thea.codes/en/stable/usage.html).

#### Run type checkers and formatters for JS & SCSS

```shell
npm run check
```

## Unwanted changes

Anything contained within the _src_ folder is meant to be merged from the upstream mkdocs-material repo. As such, it is discouraged from making any changes that might cause a merge conflict when new changes are pulled from the upstream repository.

There is no intention to support any mkdocs extensions in this theme because this theme is designed for the Sphinx documentation generator. You will often find that most of the extensions available for mkdocs are natively implemented in Sphinx or available in the form of a Sphinx extension.

### Merging in changes from upstream

There is a script titled "merge_from_mkdocs_material.py" that is designed to do most of the heavy lifting when pulling in changes from the mkdocs-material theme. It can only be executed in a Linux shell. More usage information is provided by the help menu:

```sh
python merge_from_mkdocs_material.py -h
```

Please take the time to read the extremely helpful comment from @jbms on the matter:

> To be clear this is not at all a normal merge.  If you aren't familiar with normal git merging then this will be extra confusing, but anyway let's see how it goes.
>
> In a normal git merge scenario, there is a common ancestor commit (as far as git is concerned) between the two branches being merged.  However, I have not set up this repository to actually have mkdocs-material commits in the history for various reasons:
>
> - The mkdocs-material repository frequently checks in new versions of the generated html, css, and javascript files, as well as all of the icons.  That significantly bloats the repository size, and also would lead to merge conflicts if we tried to merge.  (If this repository directly used mkdocs-material commits as parents of our commits, then all of the mkdocs-material repository history would also be in our history.)
>
> Normally git does a merge using the 3-way merge algorithm: it locates the common ancestor commit, so you have:
>
> ```text
> A----B
>   \---C
> ```
>
> So suppose our `main` branch is `C`, `A` is the common ancestor, and `B` is the new version of the other branch we want to merge in.
>
> For every file in the repository, git will consider 3 versions: the version in A, the version in B, and the version in C.  If all 3 versions are the same, then the merge result will be that single version.  If the version in B is the same as the version in A (i.e. modified only in C) then the version from C will be chosen automatically for the merge.  Likewise if the version in C is the same as A (i.e. modified only in C), then the version from B will be chosen automatically.  If all 3 versions are different, then git will attempt to merge the changes in B and C.  This uses a configurable merge driver, but by default will attempt to merge automatically and if it fails to merge a portion of the file will leave conflict markers:
>
> ```text
> <<<<<< HEAD
> // version from head
> ======
> // Version from other branch
> >>>>>>>> other-branch
> ```
>
> Additionally, it will put the git index into a special state to indicate that this file has a conflict.  To complete the merge you have to manually edit the file to the desired state (deleting the conflict markers) and then `git add` the file to mark it completed.
>
> Once resolving all conflicts you can do `git merge --continue`.  Instead of adding the conflict markers you can also have git use an interactive merge tool.
>
> With the `merge_from_mkdocs_material.py` script there is a similar process:
>
> Since the git history does not indicate the common ancestor in the mkdocs-material repository, the script instead relies on the `MKDOCS_MATERIAL_MERGE_BASE` file.
>
> The script creates a temporary mkdocs-material repository, checks out the MKDOCS_MATERIAL_MERGE_BASE  version, copies the changes from our repository into it and makes a temporary commit, then does the 3-way merge in that temporary repository, leaving conflict markers in files that have conflicts.  It then copies back the merged result, including any conflict markers, into our repository.  It will also update the MKDOCS_MATERIAL_MERGE_BASE file.  Finally, any files that merged without conflicts are staged (added to the git index).  Any remaining files that are listed as "modified" in the working tree are the files with merge conflicts and they will contain conflict markers.  However, since this isn't a real merge, the git index will not indicate that these files have conflicts.  But you will in any case need to resolve the conflicts, remove the conflict markers, and then stage these files and create a commit.
>
> As I mentioned, the merge excludes the `package-json.lock` file, since it makes some changes to the `package.json` file automatically, so you will have to run `npm install` after completing the merge to update the lock file.
>
> One of the most common source of conflicts is changes to the rxjs imports in javascript files, since these all happen at the start of the file.  These are pretty easy to resolve, you just need to figure out which symbols are actually used in the file.
>
> I have made a lot of changes to the search code, so if there are any upstream changes to the search code, it may take some significant effort to resolve.
