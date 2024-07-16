"""Tests related to theme's code block annotations."""

from sphinx.testing.util import SphinxTestApp

index_rst = """
The Test
========

.. code-block:: yaml
    :caption: A caption for good measure

    # (1)!

.. code-annotations::
    1. An annotation

.. code-annotations::
    #. A regular list not used in annotations.

.. code-block:: python

    # A normal code block without annotations
"""


def test_code_annotation(immaterial_make_app):
    app: SphinxTestApp = immaterial_make_app(
        files={"index.rst": index_rst},
    )

    app.build()
    assert not app._warning.getvalue()  # type: ignore[attr-defined]


def test_code_annotation_error(immaterial_make_app):
    app: SphinxTestApp = immaterial_make_app(
        files={
            "index.rst": """
The Test
========

.. code-annotations::
    This is not an enumerated list!

"""
        },
    )

    app.build()
    warnings = app._warning.getvalue()  # type: ignore[attr-defined]
    assert warnings
    assert "The code-annotations directive only accepts an enumerated list" in warnings
