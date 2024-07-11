"""Tests related to theme's patched admonitions."""

import pytest
from sphinx.testing.util import SphinxTestApp
from sphinx.errors import ExtensionError

conf = [
    {
        "name": "legacy",
        "color": (236, 64, 11),
        "icon": "fontawesome/solid/recycle",
        "classes": ["custom-class"],
    },
    {
        "name": "attention",
        "classes": ["important"],
    },
    {
        "name": "versionremoved",
        "classes": ["warning"],
        "override": True,
    },
    {
        "name": "deprecated",
        "color": (0, 0, 0),
        "override": True,
    },
    {
        # This is impractical, but it covers a condition in production code
        "name": "versionchanged",
        "override": True,
    },
]


def test_admonitions(immaterial_make_app):
    app: SphinxTestApp = immaterial_make_app(
        extra_conf=f"sphinx_immaterial_custom_admonitions={repr(conf)}",
        files={
            "index.rst": """
The Test
========

.. deprecated:: 0.0.1 scheduled for removal

.. versionremoved:: 0.1.0 Code was removed!
    :collapsible: open
    :class: custom-class

    Some rationale.

.. legacy::
    :collapsible: open
    :class: custom-class

    Some content.

.. legacy:: A
    :title: Custom title

    Some content.

""",
        },
    )

    app.build()
    assert not app._warning.getvalue()  # type: ignore[attr-defined]


def test_admonition_name_error(immaterial_make_app):
    # both exceptions must be raised here, so signify this using nested with statements
    with pytest.raises(ExtensionError):
        with pytest.raises(ValueError):
            immaterial_make_app(
                extra_conf="sphinx_immaterial_custom_admonitions=[{"
                '"name":"legacy!","classes":["note"]}]',
                files={
                    "index.rst": "",
                },
            )


def test_admonitions_warnings(immaterial_make_app):
    app: SphinxTestApp = immaterial_make_app(
        files={
            "index.rst": """
The Test
========

.. note::
    :collapsible:
    :no-title:

    Some content.

.. deprecated:: 0.1.0
    :collapsible:

""",
        },
    )

    app.build()
    warnings = app._warning.getvalue()  # type: ignore[attr-defined]
    assert warnings
    assert "title is needed for collapsible admonitions" in warnings
    assert "Expected 2 arguments before content in deprecated directive" in warnings


def test_todo_admonition(immaterial_make_app):
    app: SphinxTestApp = immaterial_make_app(
        extra_conf="extensions.append('sphinx.ext.todo')",
        files={
            "index.rst": """
The Test
========

.. todo::
    Some content.

""",
        },
    )

    app.build()
    assert not app._warning.getvalue()  # type: ignore[attr-defined]
