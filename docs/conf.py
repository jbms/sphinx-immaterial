# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# add docs path to python sys.path to allow autodoc-ing a test_py_module
import os
import sys
import typing

sys.path.insert(0, os.path.abspath("."))

import docutils
import sphinx
import sphinx.domains.python
import sphinx.environment
import sphinx.util.logging
import sphinx.util.typing

from sphinx_immaterial import apidoc_formatting

logger = sphinx.util.logging.getLogger(__name__)

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
    "sphinxcontrib.details.directive",
    "sphinx_immaterial.theme_result",
    "sphinx_immaterial.kbd_keys",
    "sphinx_immaterial.format_signatures",
    "sphinx_immaterial.cppreference",
    "sphinx_immaterial.json_domain",
    "sphinx_jinja",
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "sphinx_docs": ("https://www.sphinx-doc.org/en/master", None),
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

# -- sphinx_immaterial.keys extension options
#
# optional key_map for example purposes
keys_map = {"my-special-key": "Awesome Key", "git": ""}

# -- Options for HTML output -------------------------------------------------

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named 'default.css' will overwrite the builtin 'default.css'.
html_static_path = ["_static"]
html_css_files = ["extra_css.css"]
html_last_updated_fmt = ""
html_title = "Sphinx-Immaterial"
html_favicon = "_static/images/favicon.ico"  # colored version of material/bookshelf.svg
html_logo = "_static/images/Ybin.gif"  # from https://gifer.com/en/Ybin

# -- HTML theme specific settings ------------------------------------------------

extensions.append("sphinx_immaterial")
html_theme = "sphinx_immaterial"

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
        # "navigation.tracking",
        # "search.highlight",
        "search.share",
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
    # BEGIN: version_dropdown
    "version_dropdown": True,
    "version_info": [
        {
            "version": "https://sphinx-immaterial.rtfd.io",
            "title": "ReadTheDocs",
            "aliases": [],
        },
        {
            "version": "https://jbms.github.io/sphinx-immaterial",
            "title": "Github Pages",
            "aliases": [],
        },
    ],
    # END: version_dropdown
    "toc_title_is_page_title": True,
}
# end html_theme_options

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

object_description_options = []

# BEGIN: sphinx_immaterial.format_signatures extension options
object_description_options.append(
    ("cpp:.*", dict(clang_format_style={"BasedOnStyle": "LLVM"}))
)
# END: sphinx_immaterial.format_signatures extension options

object_description_options.append(("py:.*", dict(wrap_signatures_with_css=True)))

# BEGIN: sphinx_immaterial.external_cpp_references extension options
external_cpp_references = {
    "nlohmann::json": {
        "url": "https://json.nlohmann.me/api/json/",
        "object_type": "type alias",
        "desc": "C++ type alias",
    },
    "nlohmann::basic_json": {
        "url": "https://json.nlohmann.me/api/basic_json/",
        "object_type": "class",
        "desc": "C++ class",
    },
}
# END: sphinx_immaterial.external_cpp_references extension options

# BEGIN: cpp_strip_namespaces_from_signatures option
cpp_strip_namespaces_from_signatures = [
    "my_ns1",
    "my_ns2",
    "my_ns2::my_nested_ns",
]
# END: cpp_strip_namespaces_from_signatures option

rst_prolog = """
.. role:: python(code)
   :language: python
   :class: highlight

.. role:: cpp(code)
   :language: cpp
   :class: highlight

.. role:: json(code)
   :language: json
   :class: highlight
"""


object_description_options.append(
    (
        "std:confval",
        dict(
            toc_icon_class="data", toc_icon_text="C", generate_synopses="first_sentence"
        ),
    )
)

object_description_options.append(
    (
        "std:objconf",
        dict(
            toc_icon_class="data",
            toc_icon_text="O",
            generate_synopses=None,
        ),
    )
)

object_description_options.append(
    (
        "std:themeconf",
        dict(
            toc_icon_class="data", toc_icon_text="T", generate_synopses="first_sentence"
        ),
    )
)

python_type_aliases = {}

# BEGIN: python_type_aliases example
python_type_aliases = {
    "MyUnqualifiedType": "alias_ex.MyUnqualifiedType",
}
# END: python_type_aliases example


jinja_contexts = {
    "sys": {"sys": sys},
}


json_schemas = ["index_transform_schema.yml", "inheritance_schema.yml"]


def _validate_parallel_build(app):
    # Verifies that all of the extensions defined by this theme support parallel
    # building.
    assert app.is_parallel_allowed("read")
    assert app.is_parallel_allowed("write")


def _parse_object_description_signature(
    env: sphinx.environment.BuildEnvironment, signature: str, node: docutils.nodes.Node
) -> str:
    registry = apidoc_formatting.get_object_description_option_registry(env.app)
    registry_option = registry.get(signature)
    node += sphinx.addnodes.desc_name(signature, signature)
    if registry_option is None:
        logger.error("Invalid object description option: %r", signature)
    else:
        node += sphinx.addnodes.desc_sig_punctuation(" : ", " : ")
        annotations = sphinx.domains.python._parse_annotation(
            sphinx.util.typing.stringify(registry_option.type_constraint), env
        )
        node += sphinx.addnodes.desc_type("", "", *annotations)
        node += sphinx.addnodes.desc_sig_punctuation(" = ", " = ")
        default_repr = repr(registry_option.default)
        node += docutils.nodes.literal(
            default_repr,
            default_repr,
            language="python",
            classes=["python", "code", "highlight"],
        )
    return signature


def _parse_confval_signature(
    env: sphinx.environment.BuildEnvironment, signature: str, node: docutils.nodes.Node
) -> str:
    values = env.config.values
    registry_option = values.get(signature)
    node += sphinx.addnodes.desc_name(signature, signature)
    if registry_option is None:
        logger.error("Invalid config option: %r", signature)
    else:
        default, rebuild, types = registry_option
        if isinstance(types, type):
            types = (types,)
        if types:
            type_constraint = typing.Union[tuple(types)]
            node += sphinx.addnodes.desc_sig_punctuation(" : ", " : ")
            annotations = sphinx.domains.python._parse_annotation(
                sphinx.util.typing.stringify(type_constraint), env
            )
            node += sphinx.addnodes.desc_type("", "", *annotations)
        if not callable(default):
            node += sphinx.addnodes.desc_sig_punctuation(" = ", " = ")
            default_repr = repr(default)
            node += docutils.nodes.literal(
                default_repr,
                default_repr,
                language="python",
                classes=["python", "code", "highlight"],
            )
    return signature


def setup(app):
    app.add_object_type(
        "confval",
        "confval",
        objname="configuration value",
        indextemplate="pair: %s; configuration value",
        parse_node=_parse_confval_signature,
    )

    app.add_object_type(
        "themeconf",
        "themeconf",
        objname="theme configuration option",
        indextemplate="pair: %s; theme option",
    )

    app.add_object_type(
        "objconf",
        "objconf",
        objname="object description option",
        indextemplate="pair: %s; object description option",
        parse_node=_parse_object_description_signature,
    )
    app.connect("builder-inited", _validate_parallel_build)
