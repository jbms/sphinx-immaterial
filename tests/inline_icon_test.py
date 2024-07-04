"""Tests related to theme's inline icon extension."""

from pathlib import Path
import pytest
from sphinx.testing.util import SphinxTestApp
from sphinx_immaterial.inline_icons import get_custom_icons

index_rst = """
The Test
========

This icon :si-icon:`sphinx_logo;custom-class` is sourced from a third-party.
"""

sphinx_logo = Path(__file__).parent.parent / "docs" / "_static" / "sphinx_logo.svg"


@pytest.mark.parametrize(
    "custom_path", ["./", "./sub/path"], ids=["root", "nested_subdir"]
)
def test_custom_icon(custom_path: str, tmp_path: Path, immaterial_make_app):
    (tmp_path / custom_path).mkdir(parents=True, exist_ok=True)
    app: SphinxTestApp = immaterial_make_app(
        extra_conf=f'sphinx_immaterial_icon_path = ["{custom_path}"]',
        files={
            "index.rst": index_rst,
            f"{custom_path}/sphinx_logo.svg": sphinx_logo.read_text(encoding="utf-8"),
        },
    )
    app.build()
    assert not app._warning.getvalue()  # type: ignore[attr-defined]


def test_bundled_icon_not_found(immaterial_make_app):
    app: SphinxTestApp = immaterial_make_app(files={"index.rst": index_rst})
    with pytest.raises(FileNotFoundError):
        app.build()


def test_merge_env_icon_data(immaterial_make_app):
    toc = """
.. toctree::
    :hidden:

    self
    and_more
"""
    app: SphinxTestApp = immaterial_make_app(
        extra_conf='sphinx_immaterial_icon_path = ["./"]',
        files={
            "index.rst": "\n".join([toc, index_rst]),
            "and_more.rst": index_rst + "\n:si-icon:`material/material-design`\n",
            "sphinx_logo.svg": sphinx_logo.read_text(encoding="utf-8"),
        },
        parallel=2,
    )
    app.builder.read()
    icon_data = get_custom_icons(app.env)
    assert icon_data
    assert "sphinx_logo" in icon_data
    assert "material_material-design" in icon_data
