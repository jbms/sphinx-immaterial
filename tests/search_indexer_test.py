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


def test_search_incremental_builds(tmp_path: Path, immaterial_make_app):
    """generate a graph and some regular/mono text with system font as fallback."""

    def verify_search_index(index_out: Path):
        index_json = json.loads(index_out.read_bytes())
        assert "docs" in index_json
        assert len(index_json["docs"]) == 2
        locations = [e["location"] for e in index_json["docs"]]
        assert "index.html" in locations
        assert "and_more.html" in locations
        return index_json

    app: SphinxTestApp = immaterial_make_app(files=FILES)
    app.build()
    index_out = tmp_path / "_build" / "html" / "search" / "search_index.json"
    assert index_out.exists()
    first_index = verify_search_index(index_out)

    # change the contents of the and_more.rst file
    changed_file = tmp_path / "and_more.rst"
    assert changed_file.exists()
    changed_file.write_bytes(changed_file.read_bytes() + b"\nSome new content\n")
    assert "and_more" in list(app.builder.get_outdated_docs())
    app.build()

    # verify expected changes on second build
    new_index = verify_search_index(index_out)
    assert new_index != first_index
    for e in new_index["docs"]:
        if e["location"] == "and_more.html":
            changed_text = e["text"]
            break
    else:  # pragma: no cover
        # should never get here. but just in case something changes the test...
        raise RuntimeError("search index entry for changed file not found")
    assert "Some new content" in changed_text
