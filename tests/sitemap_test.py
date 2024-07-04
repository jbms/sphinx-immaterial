"""Tests related to theme's postprocess_html extension (which creates a sitemap)."""
# TODO: sphinx_immaterial.postprocess_html does not support incremental builds.
# This is adequate because docs are typically deployed from a fresh build.
# However, this lacking implementation may impact versioned docs.

from pathlib import Path
from sphinx.testing.util import SphinxTestApp

index_rst = """
The Test
========
"""


def test_create_sitemap(tmp_path: Path, immaterial_make_app):
    url = "https://example.com/test"
    app: SphinxTestApp = immaterial_make_app(
        extra_conf=f'html_theme_options = {{"site_url": "{url}"}}',
        files={"index.rst": index_rst},
    )
    app.build()
    assert not app._warning.getvalue()  # type: ignore[attr-defined]
    sitemap = tmp_path / "_build" / "html" / "sitemap.xml"
    assert sitemap.exists()
    sitemap_data = sitemap.read_text(encoding="utf-8")
    for doc in ["index", "genindex"]:
        assert f"{url}/{doc}.html" in sitemap_data
