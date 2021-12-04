# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# add docs path to python sys.path to allow autodoc-ing a test_py_module
import os
import sys

sys.path.insert(0, os.path.abspath("."))

# -- Project information -----------------------------------------------------

project = "Sphinx-Immaterial"
copyright = "2021 The Sphinx-Immaterial Authors"
author = "Jeremy Maitin-Shepard"

# The full version, including alpha/beta/rc tags
release = "1"

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.doctest",
    "sphinx.ext.extlinks",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx.ext.mathjax",
    "sphinx.ext.viewcode",
    "sphinx_design",
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "sphinx_docs": ("https://www.sphinx-doc.org/en/master", None),
    "sphinx-design": ("https://sphinx-design.readthedocs.io/en/furo-theme", None),
}

# The reST default role (used for this markup: `text`) to use for all
# documents.
default_role = "any"

autosummary_generate = True
autoclass_content = "class"

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named 'default.css' will overwrite the builtin 'default.css'.
html_static_path = ["_static"]
html_css_files = [
    "extra_css.css",
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css",
]

# -- HTML theme settings ------------------------------------------------

extensions.append("sphinx_immaterial")
html_title = "Sphinx-Immaterial"
html_theme = "sphinx_immaterial"
html_favicon = "_static/images/favicon.ico"  # colored version of material/bookshelf.svg
html_logo = "_static/images/Ybin.gif"  # from https://gifer.com/en/Ybin

# material theme options (see theme.conf for more information)
html_theme_options = {
    "icon": {
        "repo": "fontawesome/brands/github",
    },
    "site_url": "https://jbms.github.io/sphinx-immaterial/",
    "repo_url": "https://github.com/jbms/sphinx-immaterial/",
    "repo_name": "Sphinx-Immaterial",
    "repo_type": "github",
    "edit_uri": "blob/main/docs",
    # "google_analytics": ["UA-XXXXX", "auto"],
    "globaltoc_collapse": True,
    "features": [
        # "navigation.expand",
        # "navigation.tabs",
        # "toc.integrate",
        "navigation.sections",
        # "navigation.instant",
        # "header.autohide",
        "navigation.top",
    ],
    "palette": [
        {
            "media": "(prefers-color-scheme: light)",
            "scheme": "default",
            "primary": "light-green",
            "accent": "light-blue",
            "toggle": {
                "icon": "material/lightbulb-outline",
                "name": "Switch to dark mode",
            },
        },
        {
            "media": "(prefers-color-scheme: dark)",
            "scheme": "slate",
            "primary": "deep-orange",
            "accent": "lime",
            "toggle": {
                "icon": "material/lightbulb",
                "name": "Switch to light mode",
            },
        },
    ],
    "version_dropdown": True,
    "version_info": [
        {
            "version": "https://sphinx-immaterial.rtfd.io",
            "title": "ReadTheDocs",
            "aliases": []
        },
        {
            "version": "https://jbms.github.io/sphinx-immaterial",
            "title": "Github Pages",
            "aliases": []
        },
    ],
}  # end html_theme_options

html_last_updated_fmt = ""
html_use_index = True
html_domain_indices = True

# ---- Other documentation options -------------------------

todo_include_todos = True

extlinks = {
    "duref": (
        "http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html#%s",
        "",
    ),
    "durole": ("http://docutils.sourceforge.net/docs/ref/rst/roles.html#%s", ""),
    "dudir": ("http://docutils.sourceforge.net/docs/ref/rst/directives.html#%s", ""),
}


def setup(app):
    app.add_object_type(
        "confval",
        "confval",
        objname="configuration value",
        indextemplate="pair: %s; configuration value",
    )
