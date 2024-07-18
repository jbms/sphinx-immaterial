"""This module inherits from the generic ``admonition`` directive and makes the
title optional."""

from abc import ABC
from pathlib import PurePath
import re
from typing import List, Dict, Any, Tuple, Optional, Type, cast
from docutils import nodes
from docutils.parsers.rst import directives, Directive
import jinja2
import pydantic
from pydantic_extra_types.color import Color
import sphinx
import sphinx.addnodes
from sphinx.application import Sphinx
from sphinx.config import Config
from sphinx.domains.changeset import VersionChange
from sphinx.environment import BuildEnvironment
import sphinx.ext.todo
from sphinx.locale import admonitionlabels, _
from sphinx.util.logging import getLogger
from sphinx.writers.html5 import HTML5Translator
from .css_and_javascript_bundles import add_global_css
from .inline_icons import load_svg_into_builder_env, get_custom_icons
from . import html_translator_mixin

logger = getLogger(__name__)

# treat the todo directive from the sphinx extension as a built-in directive
admonitionlabels["todo"] = _("Todo")

INHERITED_ADMONITIONS = (
    "abstract",
    "info",
    "success",
    "question",
    "failure",
    "bug",
    "example",
    "quote",
)

_CUSTOM_ADMONITIONS_KEY = "sphinx_immaterial_custom_admonitions"


# defaults used for version directives re-styling
VERSION_DIR_STYLE = {
    "versionadded": {
        "icon": "material/alert-circle",
        "color": (72, 138, 87),
        "classes": [],
    },
    "versionchanged": {
        "icon": "material/alert-circle",
        "color": (238, 144, 64),
        "classes": [],
    },
    "deprecated": {"icon": "material/delete", "color": (203, 70, 83), "classes": []},
}
if sphinx.version_info >= (7, 3):
    # re-use deprecated style for versionremoved directive except with different icon
    VERSION_DIR_STYLE["versionremoved"] = {
        "icon": "material/close",
        "color": (203, 70, 83),
        "classes": [],
    }


class CustomAdmonitionConfig(pydantic.BaseModel):
    """This data class validates the user's configuration value(s) in
    :confval:`sphinx_immaterial_custom_admonitions`. Each validated object
    corresponds to a generated custom :rst:dir:`admonition` directive tailored with
    theme specific options.
    """

    name: str
    """The required name of the directive. This will be also used as a CSS class name.
    This value shall have characters that match the regular expression pattern
    ``[a-zA-Z0-9_-]``."""
    title: Optional[str] = pydantic.Field(default=None, validate_default=True)
    """The default title to use when rendering the custom admonition. If this is
    not specified, then the `name` value is converted and used."""
    icon: Optional[str] = None
    """The relative path to an icon that will be used in the admonition's
    title. If specified, this path shall be relative to

    - a SVG file placed in the documentation project's
      :confval:`sphinx_immaterial_icon_path` (this takes precedence).
    - the ``.icons`` folder that has `all of the icons bundled with this theme
      <https://github.com/squidfunk/mkdocs-material/tree/master/material/.icons>`_."""
    color: Optional[Color] = None
    """The base color to be used for the admonition's styling. If specified, this
    must be defined via:

    - `name <http://www.w3.org/TR/SVG11/types.html#ColorKeywords>`_ (e.g.
      :python:`"Black"`, :python:`"azure"`)
    - `hexadecimal value <https://en.wikipedia.org/wiki/Web_colors#Hex_triplet>`_ (e.g.
      :python:`"0x000"`, :python:`"#FFFFFF"`, :python:`"7fffd4"`)
    - RGB/RGBA tuples (e.g. :python:`(255, 255, 255)`, :python:`(255, 255, 255, 0.5)`)
    - `RGB/RGBA strings <https://developer.mozilla.org/en-US/docs/Web/CSS/color_value>`_
      (e.g. :python:`"rgb(255, 255, 255)"`, :python:`"rgba(255, 255, 255, 0.5)"`)
    - `HSL strings <https://developer.mozilla.org/en-US/docs/Web/CSS/color_value>`_
      (e.g. :python:`"hsl(270, 60%, 70%)"`, :python:`"hsl(270, 60%, 70%, .5)"`)

    .. note:: Any specified transparency (alpha value) is ignored.
    """
    classes: List[str] = []
    """If specified, this list of qualified names will be added to every rendered
    admonition (specific to the generated directive) element's ``class`` attribute.

    To adopt the styling of pre-existing admonition, include the desired
    admonition directive's name in this list.

    .. code-block:: python
        :caption: Adopting the style of an :dutree:`hint` admonition:

        sphinx_immaterial_custom_admonitions = [
            {
                "name": "my-admonition",
                "classes": ["hint"],
            },
        ]
    """
    override: bool = False
    """Can be used to override an existing directive (default is :python:`False`). Only
    set this to :python:`True` if the directive being overridden is an existing
    admonition :ref:`defined by rST and Sphinx <predefined_admonitions>` or an
    admonition :ref:`inherited from the mkdocs-material theme <inherited_admonitions>`.
    """

    @pydantic.field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, val):
        illegal = re.findall(r"([^a-zA-Z0-9\-_])", val)
        if illegal:
            raise ValueError(
                f"The following characters are illegal for directive names: {illegal}"
            )
        return val

    @pydantic.field_validator("title")
    @classmethod
    def validate_title(cls, val, info: pydantic.ValidationInfo):
        if val is None:
            val = " ".join(
                re.split(r"[\-_]+", cast(str, info.data.get("name")))
            ).title()

        return val

    @pydantic.field_validator("classes")
    @classmethod
    def validate_classes(cls, val):
        validated = []
        for c in val:
            validated.append(nodes.make_id(c))
        return validated


def visit_collapsible(self: HTML5Translator, node: nodes.Element, flag: str):
    tag_extra_args: Dict[str, Any] = {"CLASS": "admonition"}
    if flag.lower() == "open":
        tag_extra_args["open"] = ""
    self.body.append(self.starttag(node, "details", **tag_extra_args))
    title = cast(nodes.Element, node[0])
    self.body.append(
        self.starttag(title, "summary", suffix="", CLASS="admonition-title")
    )
    for child in title.children:
        child.walkabout(self)
    self.body.append("</summary>")
    del node[0]


def patch_visit_admonition():
    orig_func = HTML5Translator.visit_admonition

    def visit_admonition(self: HTML5Translator, node: nodes.Element, name: str = ""):
        collapsible: Optional[str] = node.get("collapsible", None)
        if collapsible is not None:
            assert isinstance(node[0], nodes.title)
            visit_collapsible(self, node, collapsible)
        else:
            orig_func(self, node, name)

    HTML5Translator.visit_admonition = visit_admonition  # type: ignore[assignment]


def patch_depart_admonition():
    orig_func = HTML5Translator.depart_admonition

    def depart_admonition(self: HTML5Translator, node: Optional[nodes.Element] = None):
        if node is None or node.get("collapsible", None) is None:
            orig_func(self, node)
        else:
            self.body.append("</details>\n")

    HTML5Translator.depart_admonition = depart_admonition  # type: ignore[assignment]


@html_translator_mixin.override
def visit_versionmodified(
    self: html_translator_mixin.HTMLTranslatorMixin,
    node: sphinx.addnodes.versionmodified,
    super_func: html_translator_mixin.BaseVisitCallback[
        sphinx.addnodes.versionmodified
    ],
) -> None:
    # do compatibility check for changes in Sphinx
    assert (
        len(node) >= 1
        and isinstance(node[0], nodes.paragraph)
        and node.get("type", None) is not None
        and node["type"] in VERSION_DIR_STYLE
    )
    if VERSION_DIR_STYLE[node["type"]]["classes"]:
        node["classes"].extend(VERSION_DIR_STYLE[node["type"]]["classes"])
    if node["type"] not in node["classes"]:
        node["classes"].append(node["type"])
    collapsible: Optional[str] = node.get("collapsible", None)
    if collapsible is not None:
        visit_collapsible(self, node, collapsible)
    else:
        # similar to what the OG visitor does but with an added admonition class
        self.body.append(self.starttag(node, "div", CLASSES=["admonition"]))
        # add admonition-title class to first paragraph
        node[0]["classes"].append("admonition-title")


@html_translator_mixin.override
def depart_versionmodified(
    self: html_translator_mixin.HTMLTranslatorMixin,
    node: sphinx.addnodes.versionmodified,
    super_func: html_translator_mixin.BaseVisitCallback[
        sphinx.addnodes.versionmodified
    ],
) -> None:
    collapsible: Optional[str] = node.get("collapsible", None)
    if collapsible is not None:
        self.body.append("</details>")
    else:
        super_func(self, node)


patch_visit_admonition()
patch_depart_admonition()


class CustomVersionChange(VersionChange):
    """Derivative of the original version directives to add theme-specific admonition
    options"""

    option_spec = {  # type: ignore[misc]
        "collapsible": directives.unchanged,
        "class": directives.class_option,
        "name": directives.unchanged,
    }

    def run(self):
        ret = super().run()
        assert len(ret) and isinstance(ret[0], sphinx.addnodes.versionmodified)
        if "collapsible" in self.options:
            if len(self.arguments) < 2:
                raise self.error(
                    "Expected 2 arguments before content in %s directive" % self.name
                )
            self.assert_has_content()
            ret[0]["collapsible"] = self.options["collapsible"]
        if "class" in self.options:
            ret[0]["classes"].extend(self.options["class"])
        self.add_name(ret[0])
        return ret


class CustomAdmonitionDirective(Directive, ABC):
    """A base class to define custom admonition directives.

    .. warning::
        Do not instantiate an object directly from this class as it could mess up the
        argument parsing for other derivative classes.
    """

    node_class: Type[nodes.admonition] = nodes.admonition
    optional_arguments: int
    final_argument_whitespace: bool = True
    has_content = True
    default_title: str = ""
    classes: List[str] = []
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
            # title_text must be an explicit string for renderers like MyST
            title_text = str(self.default_title)
        self.assert_has_content()
        admonition_node = self.node_class("\n".join(self.content), **self.options)  # type: ignore[call-arg]
        (
            admonition_node.source,  # type: ignore[attr-defined]
            admonition_node.line,  # type: ignore[attr-defined]
        ) = self.state_machine.get_source_and_line(self.lineno)
        if isinstance(admonition_node, sphinx.ext.todo.todo_node):
            # todo admonitions need extra info for the todolist directive
            admonition_node["docname"] = admonition_node.source
            self.state.document.note_explicit_target(admonition_node)
        else:
            self.add_name(admonition_node)
        if "collapsible" in self.options:
            admonition_node["collapsible"] = self.options["collapsible"]
        if "no-title" in self.options and "collapsible" in self.options:
            logger.error(
                "title is needed for collapsible admonitions",
                location=admonition_node,
            )
            del self.options["no-title"]  # force-disable option
        textnodes, messages = self.state.inline_text(title_text, self.lineno)
        if "no-title" not in self.options and title_text:
            title = nodes.title(title_text, "", *textnodes)
            title.source, title.line = self.state_machine.get_source_and_line(
                self.lineno
            )
            admonition_node += title
        admonition_node += messages
        admonition_node["classes"] += self.classes
        self.state.nested_parse(self.content, self.content_offset, admonition_node)
        return [admonition_node]


def get_directive_class(name, title, classes=None) -> Type[CustomAdmonitionDirective]:
    """A helper function to produce a admonition directive's class."""
    # alias upstream-deprecated CSS classes for pre-defined admonitions in sphinx
    class_list = [nodes.make_id(name)]
    if classes:
        class_list.extend(classes)

    # uncomment this block when we merge v9.x from upstream
    # if name in ("caution", "attention"):
    #     class_list.append("warning")
    # elif name == "error":
    #     class_list.append("danger")
    # elif name in ("important", "hint"):
    #     class_list.append("tip")
    # elif name == "todo":
    #     class_list.append("info")

    class CustomizedAdmonition(CustomAdmonitionDirective):
        default_title = title
        classes = class_list
        optional_arguments = int(name not in admonitionlabels)
        node_class = cast(
            Type[nodes.admonition],
            nodes.admonition if name != "todo" else sphinx.ext.todo.todo_node,
        )

    return CustomizedAdmonition


def on_builder_inited(app: Sphinx):
    """register the directives for the custom admonitions and build the CSS."""
    custom_admonitions = [
        x.model_copy()
        for x in cast(
            List[CustomAdmonitionConfig],
            getattr(app.config, "sphinx_immaterial_custom_admonitions"),
        )
    ]
    builtin_css_classes = list(admonitionlabels.keys()) + list(INHERITED_ADMONITIONS)
    custom_admonition_names = []
    for admonition in custom_admonitions:
        custom_admonition_names.append(admonition.name)
        if admonition.name in VERSION_DIR_STYLE:  # if specific to version directives
            inheriting_style = any(
                filter(lambda x: x in builtin_css_classes, admonition.classes or [])
            )
            if admonition.classes:
                cast(List[str], VERSION_DIR_STYLE[admonition.name]["classes"]).extend(
                    admonition.classes
                )
            if not inheriting_style or admonition.icon:
                admonition.icon = load_svg_into_builder_env(
                    app.builder,
                    admonition.icon
                    or cast(str, VERSION_DIR_STYLE[admonition.name]["icon"]),
                )
            if admonition.color is None and not inheriting_style:
                admonition.color = Color(
                    cast(
                        Tuple[int, int, int],
                        VERSION_DIR_STYLE[admonition.name]["color"],
                    )
                )
            continue  # don't override the version directives
        app.add_directive(
            name=admonition.name,
            cls=get_directive_class(
                admonition.name, admonition.title, admonition.classes
            ),
            override=admonition.override,
        )

        # set variables for CSS template to match HTML output from generated directives
        admonition.name = nodes.make_id(admonition.name)
        if admonition.icon is not None:
            admonition.icon = load_svg_into_builder_env(app.builder, admonition.icon)

    # add styles for sphinx directives versionadded, versionchanged, and deprecated
    for name, style in VERSION_DIR_STYLE.items():
        if name in custom_admonition_names:
            continue  # already handled above
        # add entries for default style of version directives
        version_dir_style = CustomAdmonitionConfig(
            name=name,
            icon=load_svg_into_builder_env(app.builder, cast(str, style["icon"])),
            color=style["color"],
        )
        custom_admonitions.append(version_dir_style)
    setattr(app.builder.env, "sphinx_immaterial_custom_admonitions", custom_admonitions)


def on_config_inited(app: Sphinx, config: Config):
    """Add admonitions based on CSS classes inherited from mkdocs-material theme."""

    # override the generic admonition directive
    if getattr(config, "sphinx_immaterial_override_generic_admonitions"):
        app.add_directive("admonition", get_directive_class("admonition", ""), True)

    # generate directives for inherited admonitions from upstream CSS
    if getattr(config, "sphinx_immaterial_generate_extra_admonitions"):
        for admonition in INHERITED_ADMONITIONS:
            app.add_directive(
                admonition,
                get_directive_class(admonition, _(admonition.title())),
            )
    confval_name = "sphinx_immaterial_custom_admonitions"
    # validate user defined config for custom admonitions
    user_defined_admonitions: List[CustomAdmonitionConfig] = pydantic.TypeAdapter(
        List[CustomAdmonitionConfig]
    ).validate_python(getattr(config, confval_name))
    setattr(config, confval_name, user_defined_admonitions)
    user_defined_dir_names = [directive.name for directive in user_defined_admonitions]

    # override the specific admonitions defined in sphinx and docutils
    # these are the admonitions that have translated titles in sphinx.locale
    if getattr(config, "sphinx_immaterial_override_builtin_admonitions"):
        for admonition, title in admonitionlabels.items():
            if admonition in user_defined_dir_names:
                continue
            app.add_directive(admonition, get_directive_class(admonition, title), True)

    if getattr(config, "sphinx_immaterial_override_version_directives"):
        # override original version directives with custom derivatives
        for name, __ in VERSION_DIR_STYLE.items():
            app.add_directive(name, CustomVersionChange, override=True)


def add_admonition_and_icon_css(app: Sphinx, env: BuildEnvironment):
    """Generates the CSS for icons and admonitions, then appends that to the
    theme's bundled CSS."""

    custom_admonitions = getattr(env, _CUSTOM_ADMONITIONS_KEY)
    custom_icons = get_custom_icons(env)

    jinja_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(PurePath(__file__).parent))
    )
    template = jinja_env.get_template("custom_admonitions.css")
    generated = template.render(
        icons=custom_icons,
        admonitions=custom_admonitions,
    )

    # append the generated CSS for icons and admonitions
    add_global_css(app, generated.replace("\n", ""))


def setup(app: Sphinx):
    """register our custom directive."""
    app.add_config_value(
        name="sphinx_immaterial_custom_admonitions",
        default=[],
        rebuild="env",
        types=[List[CustomAdmonitionConfig]],
    )
    app.add_config_value(
        name="sphinx_immaterial_generate_extra_admonitions",
        default=True,
        rebuild="html",
        types=bool,
    )
    app.add_config_value(
        name="sphinx_immaterial_override_generic_admonitions",
        default=True,
        rebuild="html",
        types=bool,
    )
    app.add_config_value(
        name="sphinx_immaterial_override_builtin_admonitions",
        default=True,
        rebuild="html",
        types=bool,
    )
    app.add_config_value(
        name="sphinx_immaterial_override_version_directives",
        default=True,
        rebuild="env",
        types=bool,
    )

    app.connect("builder-inited", on_builder_inited)
    app.connect("env-check-consistency", add_admonition_and_icon_css)
    app.connect("config-inited", on_config_inited)

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
