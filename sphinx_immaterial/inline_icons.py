"""This module adds the md-icon role. This is specific to this this theme because,
primarily, the icons bundled with this theme are supported (plus any svg files in the
user project's static directories)."""
from pathlib import Path
from typing import Tuple, List
from docutils import nodes
from sphinx.application import Sphinx
from sphinx.writers.html5 import HTML5Translator


class md_icon(nodes.container):
    pass


def visit_md_icon(self: HTML5Translator, node: md_icon):
    """read icon data and put it into a span element"""
    # in case this node was created from another extension
    assert node.rawsource, "icon node's rawsource must be a relative path"
    icon_name = node.rawsource + ".svg"
    svg = Path(__file__).parent / ".icons" / icon_name
    if not svg.exists():
        static_paths: str = getattr(self.builder.config, "html_static_path")
        if not static_paths:
            raise FileNotFoundError(f"{icon_name} not found in bundled theme icons")
        for path in static_paths:
            svg = Path(self.builder.srcdir) / path / icon_name
            if svg.exists():
                break
        else:
            raise FileNotFoundError(
                f"{icon_name} not found in html_static_path and not bundled with theme"
            )
    svg_data = svg.read_text(encoding="utf-8")

    css_classes = " ".join(node["classes"])
    self.body.append(f'<span class="{css_classes}">{svg_data}</span>')
    raise nodes.SkipNode()


def icons_role(
    role: str, rawtext: str, text: str, lineno: int, inliner, options={}, content=[]
) -> Tuple[List[nodes.Node], List[nodes.system_message]]:
    path, classes = (text, "")
    if ";" in text:
        path, classes = text.split(";")
    div = md_icon(path, classes=["md-icon", "si-icon-inline"] + classes.split(","))
    return [div], []


def setup(app: Sphinx):

    app.add_role("si-icon", icons_role)
    app.add_node(md_icon, html=(visit_md_icon, None))
    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
