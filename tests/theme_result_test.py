"""Tests related to theme's theme_result extension."""

from sphinx.testing.util import SphinxTestApp

index_rst = """
The Test
========

.. rst-example::

    The directive content to showcase.

.. rst-example:: A caption

    The directive content to showcase.

.. rst-example::
    :output-prefix:

    The directive content to showcase.

.. rst-example::
    :output-prefix: The above code renders the following result:

    The directive content to showcase.
"""


def test_theme_result(immaterial_make_app):
    app: SphinxTestApp = immaterial_make_app(
        extra_conf="extensions.append('sphinx_immaterial.theme_result')",
        files={"index.rst": index_rst},
    )

    app.build()
    assert not app._warning.getvalue()  # type: ignore[attr-defined]
