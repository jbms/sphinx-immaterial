"""This module adds the md-icon role. This is specific to this this theme because,
primarily, the icons bundled with this theme are supported (plus any svg files in the
user project's static directories)."""
from pathlib import Path
from typing import Tuple, List
from docutils import nodes
from sphinx.application import Sphinx
from sphinx.builders import Builder
from sphinx.writers.html5 import HTML5Translator


def read_svg_into_span(builder: Builder, icon_name: str, classes: List[str]) -> str:
    """Reads the SVG data into a HTML span element."""
    svg = Path(__file__).parent / ".icons" / icon_name
    if not svg.exists():
        static_paths: List[str] = getattr(builder.config, "html_static_path")
        for path in static_paths:
            svg = Path(builder.srcdir) / path / icon_name
            if svg.exists():
                break
        else:
            raise FileNotFoundError(
                f"{icon_name} not found in html_static_path and not bundled with theme"
            )
    svg_data = svg.read_text(encoding="utf-8")
    css_classes = " ".join(classes)
    return f'<span class="{css_classes}">{svg_data}</span>'


class si_icon(nodes.container):
    pass


def visit_si_icon(self: HTML5Translator, node: si_icon):
    """read icon data and put it into a span element"""
    # in case this node was created from another extension
    assert node.rawsource, "icon node's rawsource must be a relative path"

    self.body.append(
        read_svg_into_span(
            builder=self.builder,
            icon_name=node.rawsource + ".svg",
            classes=node["classes"],
        )
    )
    raise nodes.SkipNode()


def icons_role(
    role: str, rawtext: str, text: str, lineno: int, inliner, options={}, content=[]
) -> Tuple[List[nodes.Node], List[nodes.system_message]]:
    path, classes = (text, "")
    if ";" in text:
        path, classes = text.split(";")
    div = si_icon(path, classes=["md-icon", "si-icon-inline"] + classes.split(","))
    return [div], []


def setup(app: Sphinx):

    app.add_role("si-icon", icons_role)
    app.add_node(si_icon, html=(visit_si_icon, None))
    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
