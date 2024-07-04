"""Tests related to theme's patched graphviz ext."""

from pathlib import Path
import json
from sphinx.testing.util import SphinxTestApp


FILES = {
    "index.rst": """
.. tocentry::
    :hidden:

    and_more

Landing Page
============

""",
    "and_more.rst": """

Non-Indexed Page
================
""",
}


def test_search_metadata(tmp_path: Path, immaterial_make_app):
    """generate a graph and some regular/mono text with system font as fallback."""
    files = FILES.copy()
    files["index.rst"] = ":search-boost: 2\n" + files["index.rst"]
    files["and_more.rst"] = ":search-exclude:\n" + files["and_more.rst"]
    app: SphinxTestApp = immaterial_make_app(files=files)

    app.build()
    index_out = tmp_path / "_build" / "html" / "search" / "search_index.json"
    assert index_out.exists()
    index_json = json.loads(index_out.read_bytes())
    assert "docs" in index_json
    assert len(index_json["docs"]) == 1
    assert index_json["docs"][0]["boost"] == "2"
