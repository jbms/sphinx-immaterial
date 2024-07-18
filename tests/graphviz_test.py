"""Tests related to theme's patched graphviz ext."""

import pytest
from sphinx.testing.util import SphinxTestApp

WITH_BRACKETS = """
.. graphviz::

    graph {
        "foo()" [xref=":py:func:`foo()`"]
    }

"""

WITHOUT_BRACKETS = """
.. graphviz::

    graph {
        subgraph cluster_foo {
            xref=":py:func:`foo()`"
            A_node
        }
    }

"""


@pytest.mark.parametrize(
    "graph", [WITH_BRACKETS, WITHOUT_BRACKETS], ids=["with", "without"]
)
def test_square_brackets(immaterial_make_app, graph: str):
    """generate a graph with attributes not enclosed in square brackets"""
    app: SphinxTestApp = immaterial_make_app(
        extra_conf="\n".join(
            [
                'extensions.append("sphinx_immaterial.graphviz")',
                # tests also run on Windows in CI
                "graphviz_ignore_incorrect_font_metrics = True",
            ]
        ),
        files={
            "index.rst": """
The Test
========

A function
----------

.. py:function:: foo()

A graph
-------

{}""".format(graph)
        },
    )

    app.build()
    assert not app._warning.getvalue()  # type: ignore[attr-defined]
