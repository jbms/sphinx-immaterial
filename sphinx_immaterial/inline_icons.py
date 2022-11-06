"""This module adds the md-icon role. This is specific to this this theme because,
primarily, the icons bundled with this theme are supported (plus any svg files in the
user project's static directories)."""
from pathlib import Path
from typing import Tuple, List
from docutils import nodes
from sphinx.application import Sphinx
from sphinx.builders import Builder
from sphinx.writers.html5 import HTML5Translator


def load_svg_into_builder_env(builder: Builder, icon_name: str) -> str:
    """Reads the SVG data into a builder env variable for CSS generation."""
    css_icon_name = icon_name.replace("/", "_").replace("\\", "_")
    custom_icons = getattr(builder.env, "sphinx_immaterial_custom_icons", {})
    icon_name += ".svg"
    if css_icon_name not in custom_icons:
        static_paths: List[str] = getattr(builder.config, "sphinx_immaterial_icon_path")
        for path in static_paths:
            svg = Path(builder.srcdir) / path / icon_name
            if svg.exists():
                break
        else:
            svg = Path(__file__).parent / ".icons" / icon_name
            if not svg.exists():
                raise FileNotFoundError(
                    f"{icon_name} not found in sphinx_immaterial_icon_path and"
                    " not bundled with the theme"
                )
        custom_icons[css_icon_name] = svg.read_text(encoding="utf-8")
        setattr(builder.env, "sphinx_immaterial_custom_icons", custom_icons)
    return css_icon_name


class si_icon(nodes.container):
    pass


def visit_si_icon(self: HTML5Translator, node: si_icon):
    """read icon data and put it into a span element"""
    # in case this node was created from another extension
    assert node.rawsource, "icon node's rawsource must be a relative path"

    css_icon_name = load_svg_into_builder_env(
        builder=self.builder,
        icon_name=node.rawsource,
    )
    self.body.append(
        f'<span class="{" ".join(node["classes"])} {css_icon_name}"></span>'
    )
    raise nodes.SkipNode()


def icons_role(
    role: str, rawtext: str, text: str, lineno: int, inliner, options={}, content=[]
) -> Tuple[List[nodes.Node], List[nodes.system_message]]:
    path, classes = (text, "")
    if ";" in text:
        path, classes = text.split(";")[:2]
    div = si_icon(path, classes=["md-icon", "si-icon-inline"] + classes.split(","))
    return [div], []


def setup(app: Sphinx):

    app.add_role("si-icon", icons_role)
    app.add_node(si_icon, html=(visit_si_icon, None))

    app.add_config_value(
        name="sphinx_immaterial_icon_path",
        default=[],
        rebuild="env",
        types=[str],
    )

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
