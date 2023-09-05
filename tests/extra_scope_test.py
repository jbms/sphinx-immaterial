from __future__ import annotations

from typing import TYPE_CHECKING
from bs4 import BeautifulSoup
import re
import textwrap

if TYPE_CHECKING:
    from sphinx.testing.util import SphinxTestApp
    from bs4.element import Tag


def test_extra_scope(immaterial_make_app):
    expected_scope_url = "/test"

    app: SphinxTestApp = immaterial_make_app(
        extra_conf=textwrap.dedent(
            f"""
            html_theme_options = {{
                "scope": "{expected_scope_url}"
            }}
            """
        ),
        files={
            "index.rst": "Sample text",
        },
    )
    app.build()

    with open(app.outdir / "index.html", mode="r") as file:
        soup = BeautifulSoup(file.read(), "html.parser")

    scope_pattern = re.compile(r"__md_scope=new URL\(\"(?P<url>[^\"]+)\"")
    matched_scope_url = ""
    for script in soup.head.find_all("script"):
        script: Tag
        scope_match = scope_pattern.search(script.text)
        if scope_match:
            matched_scope_url = scope_match.group("url")
            break

    assert matched_scope_url == expected_scope_url
