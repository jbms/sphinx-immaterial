# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# add docs path to python sys.path to allow autodoc-ing a test_py_module
import os
from pathlib import Path
import re
import sys
import string
import typing

from sphinx.util.docutils import SphinxRole

sys.path.insert(0, os.path.abspath("."))

import docutils
import sphinx
import sphinx.domains.python
import sphinx.environment
import sphinx.util.logging
import sphinx.util.typing

from sphinx_immaterial.apidoc import (
    object_description_options as _object_description_options,
)
from sphinx_immaterial.apidoc.python import (
    type_annotation_transforms,
    apigen as python_apigen,
)

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
    "sphinx.ext.napoleon",
    "sphinx.ext.todo",
    "sphinx.ext.mathjax",
    "sphinx.ext.viewcode",
    "sphinx_immaterial.theme_result",
    "sphinx_immaterial.kbd_keys",
    "sphinx_immaterial.apidoc.format_signatures",
    "sphinx_immaterial.apidoc.cpp.cppreference",
    "sphinx_immaterial.apidoc.json.domain",
    "sphinx_immaterial.apidoc.python.apigen",
    "sphinx_immaterial.apidoc.cpp.apigen",
    "sphinx_immaterial.graphviz",
    "sphinx_jinja",
    "myst_parser",
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "sphinx_docs": ("https://www.sphinx-doc.org/en/master", None),
    "MyST parser docs": ("https://myst-parser.readthedocs.io/en/latest", None),
}

# The reST default role (used for this markup: `text`) to use for all
# documents.
default_role = "any"

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
html_css_files = ["extra_css.css", "custom_font_example.css"]
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
        "edit": "material/file-edit-outline",
    },
    "site_url": "https://jbms.github.io/sphinx-immaterial/",
    "repo_url": "https://github.com/jbms/sphinx-immaterial/",
    "repo_name": "Sphinx-Immaterial",
    "edit_uri": "blob/main/docs",
    "globaltoc_collapse": True,
    "features": [
        "navigation.expand",
        # "navigation.tabs",
        # "toc.integrate",
        "navigation.sections",
        # "navigation.instant",
        # "header.autohide",
        "navigation.top",
        # "navigation.tracking",
        # "search.highlight",
        "search.share",
        "toc.follow",
        "toc.sticky",
        "content.tabs.link",
        "announce.dismiss",
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
    # BEGIN: social icons
    "social": [
        {
            "icon": "fontawesome/brands/github",
            "link": "https://github.com/jbms/sphinx-immaterial",
            "name": "Source on github.com",
        },
        {
            "icon": "fontawesome/brands/python",
            "link": "https://pypi.org/project/sphinx-immaterial/",
        },
    ],
    # END: social icons
}
# end html_theme_options

# ---- Other documentation options -------------------------

todo_include_todos = True

extlinks = {
    "duref": (
        "http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html#%s",
        "rST %s",
    ),
    "durole": (
        "http://docutils.sourceforge.net/docs/ref/rst/roles.html#%s",
        "rST role %s",
    ),
    "dudir": (
        "http://docutils.sourceforge.net/docs/ref/rst/directives.html#%s",
        "rST directive %s",
    ),
    "graphvizattr": (
        "https://graphviz.org/docs/attrs/%s/",
        "%s attribute",
    ),
    "dutree": (
        "https://docutils.sourceforge.io/docs/ref/doctree.html#%s",
        "%s",
    ),
}

object_description_options = []

# BEGIN: sphinx_immaterial.apidoc.format_signatures extension options
object_description_options.append(
    ("cpp:.*", dict(clang_format_style={"BasedOnStyle": "LLVM"}))
)
object_description_options.append(("py:.*", dict(black_format_style={})))
# END: sphinx_immaterial.apidoc.format_signatures extension options

object_description_options.append(("py:.*", dict(wrap_signatures_with_css=True)))

# BEGIN: sphinx_immaterial.apidoc.cpp.external_cpp_references extension options
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
# END: sphinx_immaterial.apidoc.cpp.external_cpp_references extension options

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

.. role:: rst(code)
   :language: rst
   :class: highlight

.. role:: css(code)
   :language: css
   :class: highlight

.. role:: dot(code)
   :language: dot
   :class: highlight

.. role:: html(code)
   :language: html
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
    "example_mod._internal.": "example_mod.",
}
# END: python_type_aliases example

# BEGIN: python_module_names_to_strip_from_xrefs example
python_module_names_to_strip_from_xrefs = ["tensorstore_demo"]
# END: python_module_names_to_strip_from_xrefs example

# BEGIN CUSTOM ADMONITIONS
sphinx_immaterial_custom_admonitions = [
    {
        "name": "legacy",
        "color": (236, 64, 11),
        "icon": "fontawesome/solid/recycle",
    },
]
# END CUSTOM ADMONITIONS
sphinx_immaterial_icon_path = html_static_path

sphinx_immaterial_bundle_source_maps = True

CSS_PALETTE_BUNDLE = (
    Path(__file__).parent.parent / "sphinx_immaterial/bundles/stylesheets/palette.css"
)


def get_colors(color_t: str):
    unique_colors = []
    for m in re.finditer(
        r"\}\[data-md-color-"
        + color_t
        + r"=([a-z\-]+)\]\{.*?-fg-color:.*?;.*?-bg-color:.*?;",
        CSS_PALETTE_BUNDLE.read_text(encoding="utf-8"),
    ):
        unique_colors.append(m.group(1))
    return unique_colors


# jinja contexts
example_python_apigen_modules = {
    "my_module": "my_api/",
    "my_other_module": "other_api/my_other_module.",
}
example_python_apigen_objects = [
    ("my_module.foo", ""),
    ("my_module.Foo", ""),
    ("my_module.Foo.method", ""),
    ("my_module.Foo.__init__", "json"),
    ("my_module.Foo.__init__", "values"),
    ("my_module.Bar", ""),
    ("my_other_module.Baz", ""),
]
jinja_contexts = {
    "python_apigen_path_examples": {
        "example_python_apigen_objects": [
            (
                full_name,
                overload_id,
                python_apigen._get_docname(
                    example_python_apigen_modules, full_name, overload_id, False
                ),
                python_apigen._get_docname(
                    example_python_apigen_modules, full_name, overload_id, True
                ),
            )
            for full_name, overload_id in example_python_apigen_objects
        ],
    },
    "typing_names": {"TYPING_NAMES": type_annotation_transforms.TYPING_NAMES},
    "pep685_aliases": {"aliases": type_annotation_transforms.PEP585_ALIASES},
    "colors": {
        "supported_primary": get_colors("primary"),
        "supported_accent": get_colors("accent"),
    },
}


json_schemas = [
    "apidoc/json/index_transform_schema.yml",
    "apidoc/json/inheritance_schema.yml",
]

json_schema_rst_prolog = """
.. default-role:: json:schema

.. default-literal-role:: json

.. highlight:: json
"""

python_apigen_modules = {
    "tensorstore_demo": "python_apigen_generated/",
    "type_param_demo": "python_apigen_generated/",
}

python_apigen_default_groups = [
    ("class:.*", "Classes"),
    (r".*:.*\.__(init|new)__", "Constructors"),
    (r".*:.*\.__eq__", "Comparison operators"),
    (r".*:.*\.__(str|repr)__", "String representation"),
]

python_apigen_rst_prolog = """
.. default-role:: py:obj

.. default-literal-role:: python

.. highlight:: python
"""

cpp_demo_include_dir = os.path.join(os.path.dirname(__file__))

cpp_apigen_configs = [
    dict(
        document_prefix="cpp_apigen_generated/",
        api_parser_config=dict(
            input_content="""
#include "cpp_apigen_demo/index_interval.h"
#include "cpp_apigen_demo/array.h"
""",
            compiler_flags=["-std=c++17", "-I", cpp_demo_include_dir, "-x", "c++"],
            include_directory_map={
                f"{cpp_demo_include_dir}/": "",
            },
            allow_paths=["^cpp_apigen_demo/"],
            disallow_namespaces=["^std$"],
            verbose=True,
        ),
    ),
]

cpp_apigen_rst_prolog = """
.. default-role:: cpp:expr

.. default-literal-role:: cpp

.. highlight:: cpp
"""

autodoc_class_signature = "separated"

nitpicky = True
nitpick_ignore = [
    # Python standard library types not present in object inventory.
    ("py:class", "Pattern"),
    ("py:class", "re.Pattern"),
    # Example Python types
    ("py:class", "example_mod.Foo"),
    ("py:class", "alias_ex.MyUnqualifiedType"),
    # Example C++ types
    ("cpp:identifier", "Sphinx"),
    ("cpp:identifier", "RF24_SPI_SPEED"),
    # C++ namespaces referenced in the documentation
    #
    # It is a bug in the C++ domain that a reference to `ns::symbol` will
    # ultimately generate a reference to both `ns` and `ns::symbol`.  However,
    # because the C++ domain does not actually define "namespace" objects, the
    # `ns` reference will always fail to be resolved, leading to a spurious
    # warning.
    ("cpp:identifier", "::nlohmann"),
    ("cpp:identifier", "std"),
    ("cpp:identifier", "synopses_ex"),
    ("cpp:identifier", "my_ns1"),
    ("cpp:identifier", "my_ns2"),
    ("cpp:identifier", "my_ns2::my_nested_ns"),
    ("cpp:identifier", "my_ns3"),
    ("cpp:identifier", "cpp_apigen_demo"),
    # Example JavaScript types
    ("js:func", "string"),
    ("js:func", "SomeError"),
    # pydantic_extra_types.color not present in object inventory
    ("py:class", "pydantic_extra_types.color.Color"),
]


graphviz_ignore_incorrect_font_metrics = True

# MyST parser config options
myst_enable_extensions = [
    "deflist",
    "fieldlist",
    "smartquotes",
    "replacements",
    "strikethrough",
    "substitution",
    "tasklist",
    "attrs_inline",
    "attrs_block",
]

myst_enable_checkboxes = True
myst_substitutions = {
    "role": "[role](#syntax/roles)",
}

# Myst parser's strikethrough plugin seems to think that sphinx-immaterial doesn't use
# HTML output (probably due to the custom translator mixin used).
suppress_warnings = ["myst.strikethrough"]


def _validate_parallel_build(app):
    # Verifies that all of the extensions defined by this theme support parallel
    # building.
    assert app.is_parallel_allowed("read")
    assert app.is_parallel_allowed("write")


if sphinx.version_info >= (6, 1):
    stringify = sphinx.util.typing.stringify_annotation
else:
    stringify = sphinx.util.typing.stringify


def _parse_object_description_signature(
    env: sphinx.environment.BuildEnvironment, signature: str, node: docutils.nodes.Node
) -> str:
    registry = _object_description_options.get_object_description_option_registry(
        env.app
    )
    registry_option = registry.get(signature)
    node += sphinx.addnodes.desc_name(signature, signature)
    if registry_option is None:
        logger.error("Invalid object description option: %r", signature, location=node)
    else:
        node += sphinx.addnodes.desc_sig_punctuation(" : ", " : ")
        annotations = sphinx.domains.python._parse_annotation(
            stringify(registry_option.type_constraint), env
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
        logger.error("Invalid config option: %r", signature, location=node)
    else:
        default = registry_option.default
        types = registry_option.valid_types
        if isinstance(types, sphinx.config.ENUM):
            types = (typing.Literal[tuple(types.candidates)],)
        if isinstance(types, type):
            types = (types,)
        if types:
            type_constraint = typing.Union[tuple(types)]
            node += sphinx.addnodes.desc_sig_punctuation(" : ", " : ")
            annotations = sphinx.domains.python._parse_annotation(
                stringify(type_constraint), env
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


class TestColor(SphinxRole):
    color_type: str
    style = (
        "background-color: %s;"
        "color: %s;"
        "padding: 0.05rem 0.3rem;"
        "border-radius: 0.25rem;"
        "cursor: pointer;"
    )
    style_params: typing.Tuple[str, str]
    on_click = (
        "document.body.setAttribute(`data-md-color-$color_type`, `$attr`);"
        "var name = document.querySelector("
        "`#$color_type-color-conf-example code span:nth-last-child(3)`);"
        "name.textContent = `&quot;$attr&quot;`;"
    )

    def run(self):
        if self.color_type == "primary":
            self.style_params = (
                f"var(--md-{self.color_type}-fg-color)",
                f"var(--md-{self.color_type}-bg-color)",
            )
        elif self.color_type == "accent":
            self.style_params = (
                "var(--md-code-bg-color)",
                f"var(--md-{self.color_type}-fg-color)",
            )
        color_attr = ""
        if self.color_type in ("primary", "accent"):
            color_attr = f'data-md-color-{self.color_type}="{self.text}"'
        el_style = self.style % self.style_params
        click_func = string.Template(self.on_click).substitute(
            color_type=self.color_type, attr=self.text
        )
        node = docutils.nodes.raw(
            self.rawtext,
            f"<button {color_attr} style="
            f'"{el_style}" onclick="{click_func}">{self.text}</button>',
            format="html",
        )
        return ([node], [])


class TestColorPrimary(TestColor):
    color_type = "primary"


class TestColorAccent(TestColor):
    color_type = "accent"


class TestColorScheme(TestColor):
    color_type = "scheme"
    style_params = ("var(--md-primary-fg-color)", "var(--md-primary-bg-color)")
    on_click = (
        "document.body.setAttribute('data-md-color-switching', '');"
        + TestColor.on_click
        + "setTimeout(function() {document.body.removeAttribute"
        "('data-md-color-switching')});"
    )


def setup(app):
    app.add_role("test-color-primary", TestColorPrimary())
    app.add_role("test-color-accent", TestColorAccent())
    app.add_role("test-color-scheme", TestColorScheme())

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

    # Add `event` type from Sphinx's own documentation, to allow intersphinx
    # references to Sphinx events.
    app.add_object_type(
        "event",
        "event",
        objname="Sphinx event",
        indextemplate="pair: %s; event",
    )
    app.connect("builder-inited", _validate_parallel_build)
