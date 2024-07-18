"""This module adds the md-icon role. This is specific to this this theme because,
primarily, the icons bundled with this theme are supported (plus any svg files in the
user project's static directories)."""

from pathlib import Path
from typing import Tuple, List, Dict

from docutils import nodes
from sphinx.application import Sphinx
from sphinx.builders import Builder
import sphinx.environment
from sphinx.writers.html5 import HTML5Translator
from sphinx.util.docutils import SphinxRole


CUSTOM_ICON_KEY = "_sphinx_immaterial_custom_icons"


def get_custom_icons(env: sphinx.environment.BuildEnvironment) -> Dict[str, str]:
    custom_icons = getattr(env, CUSTOM_ICON_KEY, None)
    if custom_icons is None:
        custom_icons = {}
        setattr(env, CUSTOM_ICON_KEY, custom_icons)
    return custom_icons


def load_svg_into_builder_env(builder: Builder, icon_name: str) -> str:
    """Reads the SVG data into a builder env variable for CSS generation.

    Returns: The name of CSS class associated with the SVG data."""
    css_icon_name = icon_name.replace("/", "_").replace("\\", "_")
    icon_name += ".svg"
    custom_icons = get_custom_icons(builder.env)
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
    return css_icon_name


class si_icon(nodes.container):
    pass


def visit_si_icon(self: HTML5Translator, node: si_icon):
    """Create a span element with associated CSS classes."""
    self.body.append(f'<span class="{" ".join(node["classes"])}"></span>')
    raise nodes.SkipNode()


class IconsRole(SphinxRole):
    """A interpreted text role to use icons in lines of text."""

    def run(self) -> Tuple[List[nodes.Node], List[nodes.system_message]]:
        path, classes = (self.text, "")
        if ";" in self.text:
            path, classes = self.text.split(";")[:2]
        class_list = [
            "md-icon",
            "si-icon-inline",
            load_svg_into_builder_env(
                builder=self.env.app.builder,
                icon_name=path,
            ),
        ]
        class_list.extend([cls for cls in classes.split(",") if cls])
        div = si_icon(path, classes=class_list)
        return [div], []


def _merge_info(
    app: sphinx.application.Sphinx,
    env: sphinx.environment.BuildEnvironment,
    docnames: List[str],
    other: sphinx.environment.BuildEnvironment,
) -> None:
    get_custom_icons(env).update(get_custom_icons(other))


def setup(app: Sphinx):
    app.connect("env-merge-info", _merge_info)
    app.add_role("si-icon", IconsRole())
    app.add_node(si_icon, html=(visit_si_icon, None))

    app.add_config_value(
        name="sphinx_immaterial_icon_path",
        default=[],
        rebuild="env",
        types=[List[str]],
    )

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
