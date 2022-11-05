"""This module inherits from the generic ``admonition`` directive and makes the
title optional."""
from pathlib import Path, PurePath
import re
from typing import List, Dict, Any, Tuple, Optional, cast, Type, Union
from docutils import nodes
from docutils.parsers.rst import directives
from docutils.parsers.rst.directives import admonitions
import jinja2
import pydantic
from sphinx.application import Sphinx
import sphinx.addnodes
import sphinx.ext.todo
from sphinx.writers.html5 import HTML5Translator
from sphinx.util.docutils import SphinxDirective
from sphinx.util.logging import getLogger
from sphinx.locale import admonitionlabels, _
from .inline_icons import load_svg_into_builder_env

logger = getLogger(__name__)


class CustomAdmonitionConfig(pydantic.BaseModel):
    """This data class validates the user's configuration value(s) in
    :confval:`sphinx_immaterial_custom_admonitions`. Each instantiated object
    corresponds to a generated custom :rst:dir:`admonition` directive tailored with
    theme specific options.
    """

    name: str
    color: Tuple[int, int, int]
    icon: str
    title: str
    override: bool = False

    def __init__(
        self,
        name: str,
        color: Tuple[int, int, int],
        icon: str,
        title: str = None,
        override: bool = False,
    ):
        """
        :param name:
            The name of the directive. This will be also used as a CSS class name.
            This value shall have characters that match the regular expression pattern
            ``[a-zA-Z0-9_-]``.
        :param icon:
            The relative path to an icon that will be used in the admonition's
            title. This path shall be relative to

            - the ``.icons`` folder that has `all of the icons bundled with this theme
              <https://github.com/squidfunk/mkdocs-material/tree/master/material/
              .icons>`_ (this takes precedence).
            - a SVG file placed in the documentation project's `html_static_path`.
        :param color:
            The base color to be used for the admonition's styling. This
            must be specified as a RGB color space. Each color component shall be
            confined to the range [0, 255]. It is also possible to use the
            :py:mod:`colorsys` module if converting from a different color space (like
            HSL) to RGB.
        :param title:
            The title to use when rendering the custom admonition. If this is not
            specified, then the
            :py:obj:`~sphinx_immaterial.custom_admonitions.CustomAdmonitionConfig.__init__.name`
            value is converted and used.
        :param override:
            Can be used to override an existing directive. Only set this to
            :python:`True` if the directive being overridden is an existing admonition
            :ref:`defined by rST and Sphinx <predefined_admonitions>` or an admonition
            :ref:`inherited from the mkdocs-material theme <inherited_admonitions>`.
        """
        illegal = re.findall(r"([^a-zA-Z0-9\-_])", name)
        if illegal:
            raise ValueError(
                f"The following characters are illegal for directive names: {illegal}"
            )
        # assert len(color) == 3, "color must have 3 components"
        for c in color:
            assert 0 <= c <= 255, f"color component {c} is not in range [0, 255]"
        if title is None:
            title = " ".join(re.split(r"[\-_]+", name)).title()
        super().__init__(
            name=name,
            color=color,
            icon=icon,
            title=title,
            override=override,
        )


def patch_visit_admonition():
    orig_func = HTML5Translator.visit_admonition

    def visit_admonition(self: HTML5Translator, node: nodes.Element, name: str = ""):
        collapsible: Optional[str] = node.get("collapsible", None)
        if collapsible is not None:
            tag_extra_args: Dict[str, Any] = dict(CLASS="admonition")
            if collapsible.lower() == "open":
                tag_extra_args["open"] = ""
            self.body.append(self.starttag(node, "details", **tag_extra_args))
            title = node.children[0]
            assert isinstance(title, nodes.title)
            self.body.append(
                self.starttag(title, "summary", suffix="", CLASS="admonition-title")
            )
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
        if node is None or node.get("collapsible", None) is None:
            orig_func(self, node)
        else:
            self.body.append("</details>\n")

    HTML5Translator.depart_admonition = depart_admonition


class CustomAdmonitionDirective(admonitions.BaseAdmonition, SphinxDirective):
    """A class to define custom admonitions"""

    node_class: Type[nodes.Admonition] = nodes.admonition
    optional_arguments = 1
    final_argument_whitespace = True
    default_title: str = ""
    name: str = ""
    option_spec = {
        "class": directives.class_option,
        "name": directives.unchanged,
        "collapsible": directives.unchanged,
        "no-title": directives.flag,
        "title": directives.unchanged,
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
        title_text = "" if not self.arguments else self.arguments[0]
        if "title" in self.options:
            # this option can be combined with the directive argument used as a title.
            title_text += (" " if title_text else "") + self.options["title"]
            # don't auto-assert `:no-title:` if value is blank; just use default
        if not title_text:
            title_text = self.default_title
        self.assert_has_content()
        admonition_node = self.node_class("\n".join(self.content), **self.options)
        self.set_source_info(admonition_node)
        if isinstance(admonition_node, sphinx.ext.todo.todo_node):
            # todo admonitions need extra info for the todolist directive
            admonition_node["docname"] = self.env.docname
            self.state.document.note_explicit_target(admonition_node)
        else:
            self.add_name(admonition_node)
        if "collapsible" in self.options:
            admonition_node["collapsible"] = self.options["collapsible"]
        if "no-title" in self.options and "collapsible" in self.options:
            logger.warning(
                "title is needed for collapsible admonitions",
                location=admonition_node,
            )
            del self.options["no-title"]  # force-disable option
        textnodes, messages = self.state.inline_text(title_text, self.lineno)
        if "no-title" not in self.options and title_text:
            title = nodes.title(title_text, "", *textnodes)
            self.set_source_info(title)
            admonition_node += title
        admonition_node += messages
        admonition_node["classes"] += [nodes.make_id(self.name)]
        self.state.nested_parse(self.content, self.content_offset, admonition_node)
        return [admonition_node]


def on_builder_inited(app: Sphinx):
    """register the directives for the custom admonitions and build the CSS."""
    config = app.config
    custom_admonitions: List[CustomAdmonitionConfig] = getattr(
        config, "sphinx_immaterial_custom_admonitions"
    )
    setattr(app.builder.env, "sphinx_immaterial_custom_icons", {})
    user_admonitions = []
    for config_val in custom_admonitions:

        admonition = CustomAdmonitionConfig(**dict(config_val))

        class UserAdmonition(CustomAdmonitionDirective):
            default_title = admonition.title
            name = admonition.name

        app.add_directive(
            name=admonition.name, cls=UserAdmonition, override=admonition.override
        )

        # set variables for CSS template to match HTML output from generated directives
        admonition.name = nodes.make_id(admonition.name)
        admonition.icon = load_svg_into_builder_env(app.builder, admonition.icon)
        user_admonitions.append(admonition)
    setattr(app.builder.env, "sphinx_immaterial_custom_admonitions", user_admonitions)


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
        types=[Dict[str, Union[str, Tuple[int, int, int], bool]]],
    )

    # add admonitions based on  CSS classes inherited from mkdocs-material theme
    for admonition in (
        "abstract",
        "info",
        "success",
        "question",
        "failure",
        "bug",
        "example",
        "quote",
    ):

        class InheritedAdmonition(CustomAdmonitionDirective):
            default_title = admonition.title()
            name = admonition

        app.add_directive(admonition, InheritedAdmonition)

    # override the generic admonition directive with our custom base class
    app.add_directive("admonition", CustomAdmonitionDirective, True)

    # override the specific admonitions defined in sphinx and docutils
    # these are the admonitions that have translated titles in sphinx.locale
    #
    # NOTE todo and todolist are actually sphinx exts that ship with sphinx,
    # so we'll leave those alone until their config is confirmed compatible.
    for admonition in (
        "note",
        "tip",
        "hint",
        "important",
        "attention",
        "caution",
        "warning",
        "danger",
        "error",
        "seealso",
    ):

        class SpecificAdmonition(CustomAdmonitionDirective):
            default_title = admonitionlabels[admonition]
            name = admonition
            optional_arguments = 0
            final_argument_whitespace = False

        app.add_directive(admonition, SpecificAdmonition, True)

    # override the todo directive from the sphinx extension
    class TodoAdmonitionDirectiveOverride(CustomAdmonitionDirective):
        default_title = _("Todo")
        node_class = cast(Type[nodes.Admonition], sphinx.ext.todo.todo_node)
        name = "todo"
        optional_arguments = 0
        final_argument_whitespace = False

    app.add_directive("todo", TodoAdmonitionDirectiveOverride, True)

    app.connect("builder-inited", on_builder_inited)
    app.connect("build-finished", on_build_finished)

    patch_visit_admonition()
    patch_depart_admonition()

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
