"""Tests related to theme's mermaid graphs extension."""

import pytest
from sphinx.testing.util import SphinxTestApp

index_rst = """
The Test
========

.. md-mermaid::
    :name: flowcharts

    graph LR
        A[Start] --> B{Error?};
        B -->|Yes| C[Hmm...];
        C --> D[Debug];
        D --> B;
        B ---->|No| E[Yay!];
"""


@pytest.mark.parametrize("builder", ["html", "latex"])
def test_mermaid_graph(builder: str, immaterial_make_app):
    app: SphinxTestApp = immaterial_make_app(
        files={"index.rst": index_rst},
        buildername=builder,
    )

    app.build()
    assert not app._warning.getvalue()  # type: ignore[attr-defined]
