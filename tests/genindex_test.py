"""Tests that genindex page is created correctly."""

from pathlib import Path

from sphinx.testing.util import SphinxTestApp

index_rst = """
The Test
========

.. py:module:: mymodule

   This is a module.

"""


def test_genindex(tmp_path: Path, immaterial_make_app):
    app: SphinxTestApp = immaterial_make_app(
        confoverrides=dict(html_title="Project"),
        files={"index.rst": index_rst},
    )
    app.build()
    assert not app._warning.getvalue()  # type: ignore[attr-defined]
    genindex_path = tmp_path / "_build" / "html" / "genindex.html"
    assert genindex_path.exists()
    genindex_html = genindex_path.read_text(encoding="utf-8")

    assert "<title>Index - Project</title>" in genindex_html

    assert "module-mymodule" in genindex_html
