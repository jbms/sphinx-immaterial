"""This module inherits from the generic ``admonition`` directive and makes the
title optional."""
from pathlib import Path, PurePath
from typing import List, Dict, Any, Tuple, Optional
from docutils import nodes
from docutils.parsers.rst import directives
from docutils.parsers.rst.directives import admonitions
from sphinx.application import Sphinx
from sphinx.writers.html5 import HTML5Translator
import jinja2
from .inline_icons import load_svg_into_builder_env


class CustomAdmonition:
    def __init__(
        self,
        name: str,
        color: Tuple[int, int, int],
        icon: str,
        title: str = None,
        override: bool = False,
    ):
        self.name = name
        self.color = color
        self.icon = icon
        if title is not None:
            self.title = title
        else:
            self.title = name.replace("-", " ").replace("_", " ").title()
        self.override = override


def patch_visit_admonition():
    orig_func = HTML5Translator.visit_admonition

    def visit_admonition(self: HTML5Translator, node: nodes.Element, name: str = ""):
        collapsible: Optional[str] = node.get("collapsible", None)
        if collapsible is not None:
            tag_extra_args: Dict[str, Any] = dict(CLASS="admonition")
            if collapsible.lower() == "open":
                tag_extra_args["open"] = ""
            self.body.append(self.starttag(node, "details", **tag_extra_args))
            assert isinstance(node.children[0], nodes.title)
            title = node.children[0]
            self.body.append(
                self.starttag(title, "summary", suffix="", CLASS="admonition-title")
            )
            del title["classes"]
            for child in title.children:
                child.walkabout(self)
            self.body.append("</summary>")
            del node.children[0]
        else:
            orig_func(self, node, name)

    HTML5Translator.visit_admonition = visit_admonition


def patch_depart_admonition():
    orig_func = HTML5Translator.depart_admonition

    def depart_admonition(self: HTML5Translator, node: Optional[nodes.Element] = None):
        if node is None:
            return
        if node.get("collapsible", None) is not None:
            self.body.append("</details>\n")
        else:
            orig_func(self, node)

    HTML5Translator.depart_admonition = depart_admonition


class CustomAdmonitionDirective(admonitions.BaseAdmonition):
    """A class to define custom admonitions"""

    node_class = nodes.admonition
    final_argument_whitespace = False
    default_title: str
    name: str
    option_spec = {
        "class": directives.class_option,
        "name": directives.unchanged,
        "collapsible": directives.unchanged,
        "no-title": directives.flag,
    }

    def run(self):
        # docutils.parsers.rst.roles.set_classes() is deprecated &
        # its replacement is not available in older versions, so
        # manually convert key from "class" to "classes"
        if "class" in self.options:
            if "classes" not in self.options:
                self.options["classes"] = []
            self.options["classes"].extend(self.options["class"])
            del self.options["class"]
        self.assert_has_content()
        admonition_node = self.node_class("\n".join(self.content), **self.options)
        self.add_name(admonition_node)
        if "collapsible" in self.options:
            admonition_node["collapsible"] = self.options["collapsible"]
        textnodes, messages = self.state.inline_text(self.default_title, self.lineno)
        if "no-title" in self.options:
            if "collapsible" in self.options:
                self.error("title is needed for collapsible admonitions")
        else:
            title = nodes.title(self.default_title, "", *textnodes)
            title.source, title.line = self.state_machine.get_source_and_line(
                self.lineno
            )
            if self.default_title:
                admonition_node += title
        admonition_node += messages
        if not self.options.get("classes") and self.default_title:
            admonition_node["classes"] += [nodes.make_id(self.name)]
        self.state.nested_parse(self.content, self.content_offset, admonition_node)
        return [admonition_node]


def on_builder_inited(app: Sphinx):
    """register the directives for the custom admonitions and build the CSS."""
    config = app.config
    custom_admonitions: List[CustomAdmonition] = getattr(
        config, "sphinx_immaterial_custom_admonitions"
    )
    setattr(app.builder.env, "sphinx_immaterial_custom_admonitions", custom_admonitions)
    setattr(app.builder.env, "sphinx_immaterial_custom_icons", {})
    for admonition in custom_admonitions:

        class UserAdmonition(CustomAdmonitionDirective):
            default_title = admonition.title
            name = admonition.name

        app.add_directive(
            name=admonition.name, cls=UserAdmonition, override=admonition.override
        )

        load_svg_into_builder_env(app.builder, admonition.icon)


def on_build_finished(app: Sphinx, exception: Optional[Exception]):
    """generates the CSS for icons and admonitions, then appends that to the
    doc project's CSS"""
    if exception is not None or app.builder.name not in ("html", "dirhtml"):
        return
    custom_admonitions = getattr(
        app.builder.env, "sphinx_immaterial_custom_admonitions"
    )
    custom_icons = getattr(app.builder.env, "sphinx_immaterial_custom_icons")
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(PurePath(__file__).parent))
    )
    template = env.get_template("custom_admonitions.css")
    generated = template.render(
        icons=custom_icons,
        admonitions=custom_admonitions,
    )
    static_output = Path(app.outdir) / "_static" / "stylesheets"
    for css in static_output.glob("main.*.min.css"):
        if css.suffix.endswith("css"):  # ignore the CSS map file
            base_css = css
            break
    else:
        raise FileNotFoundError(f"couldn't locate main.css in {static_output}")
    with base_css.open("a") as css_out:
        css_out.write(generated.replace("\n", ""))


def setup(app: Sphinx):
    """register our custom directive."""
    app.add_config_value(
        name="sphinx_immaterial_custom_admonitions",
        default=[],
        rebuild="env",
        types=List[CustomAdmonition],
    )
    app.connect("builder-inited", on_builder_inited)
    app.connect("build-finished", on_build_finished)

    patch_visit_admonition()
    patch_depart_admonition()

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
