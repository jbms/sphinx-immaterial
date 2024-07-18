"""Tests related to theme's patched graphviz ext."""

from sphinx.testing.util import SphinxTestApp


def test_system_font(immaterial_make_app):
    """generate a graph and some regular/mono text with system font as fallback."""
    app: SphinxTestApp = immaterial_make_app(
        extra_conf="\n".join(
            [
                'extensions.append("sphinx_immaterial.graphviz")',
                # tests also run on Windows in CI
                "graphviz_ignore_incorrect_font_metrics = True",
                "html_theme_options = dict(font=False)",
            ]
        ),
        files={
            "index.rst": """
The Test
========

Some normal text and::

    Some monospace text

A graph
-------

.. graphviz::

    digraph { A -> B }
""",
        },
    )

    app.build()
    assert not app._warning.getvalue()  # type: ignore[attr-defined]
