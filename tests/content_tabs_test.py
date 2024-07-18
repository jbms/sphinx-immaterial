"""Tests related to theme's content tabs."""

from docutils.nodes import Node
import pytest
from sphinx.testing.util import SphinxTestApp
from sphinx_immaterial.content_tabs import is_md_tab_type

index_rst = """
The Test
========

.. md-tab-set::
    :name: tab_set_ref

    .. md-tab-item:: A

        Tab A content

    .. md-tab-item:: B

        Tab B content
"""


def test_content_tabs(immaterial_make_app):
    app: SphinxTestApp = immaterial_make_app(
        files={"index.rst": index_rst},
    )

    app.build()
    assert not app._warning.getvalue()  # type: ignore[attr-defined]


def test_tab_ext_error():
    assert not is_md_tab_type(Node(), "")


def test_tab_set_child_error(immaterial_make_app):
    app: SphinxTestApp = immaterial_make_app(
        files={
            "index.rst": """
The Test
========

.. md-tab-set::

    This is not a ``md-tab-item``!
"""
        },
    )

    with pytest.raises(ValueError):
        app.build()
        warnings = app._warning.getvalue()  # type: ignore[attr-defined]
        assert warnings
        assert "All children of a 'md-tab-set' should be 'md-tab-item'" in warnings


def test_tab_item_parent_error(immaterial_make_app):
    app: SphinxTestApp = immaterial_make_app(
        files={
            "index.rst": """
The Test
========

.. md-tab-item:: Orphan

    This is ``md-tab-item`` has no parent ``md-tab-set``!
"""
        },
    )
    app.build()
    warnings = app._warning.getvalue()  # type: ignore[attr-defined]
    assert warnings
    assert "The parent of a 'md-tab-item' should be a 'md-tab-set'" in warnings
