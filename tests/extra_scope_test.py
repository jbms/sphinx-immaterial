from __future__ import annotations

import re
import textwrap
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from bs4 import BeautifulSoup

if TYPE_CHECKING:
    from sphinx.testing.util import SphinxTestApp


@pytest.mark.parametrize(
    "scope_url,expected_scope_url",
    [
        (None, "."),
        ("", ""),
        ("/", "/"),
        ("/subsite", "/subsite"),
    ],
    ids=[
        "base_url",
        "empty",
        "root",
        "subsite",
    ],
)
def test_extra_scope(
    immaterial_make_app,
    scope_url: str | None,
    expected_scope_url: str,
):
    if scope_url is not None:
        scope_url = f'"{scope_url}"'

    app: SphinxTestApp = immaterial_make_app(
        extra_conf=textwrap.dedent(
            f"""
            html_theme_options = {{
                "scope": {scope_url}
            }}
            """
        ),
        files={
            "index.rst": "Sample text",
        },
    )
    app.build()

    assert not app._warning.getvalue()  # type: ignore[attr-defined]

    with open(Path(app.outdir) / "index.html", mode="r") as file:
        soup = BeautifulSoup(file.read(), "html.parser")

    head = soup.head
    assert head is not None

    scope_pattern = re.compile(r"__md_scope=new URL\(\"(?P<url>[^\"]+)\"")
    matched_scope_url = ""
    for script in head.find_all("script"):
        scope_match = scope_pattern.search(script.text)
        if scope_match:
            matched_scope_url = scope_match.group("url")
            break

    assert matched_scope_url == expected_scope_url
