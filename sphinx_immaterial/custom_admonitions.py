"""This module inherits from the generic ``admonition`` directive and makes the
title optional."""
from abc import ABC
import io
import hashlib
from pathlib import Path, PurePath
import re
from typing import List, Dict, Any, Tuple, Optional, Type, Union, cast
from docutils import nodes
from docutils.parsers.rst import directives, Directive
import jinja2
import pydantic
import sphinx.addnodes
from sphinx.application import Sphinx
from sphinx.config import Config
from sphinx.environment import BuildEnvironment
import sphinx.ext.todo
from sphinx.locale import admonitionlabels, _
from sphinx.util.logging import getLogger
from sphinx.writers.html5 import HTML5Translator
from .inline_icons import load_svg_into_builder_env

logger = getLogger(__name__)

# treat the todo directive from the sphinx extension as a built-in directive
admonitionlabels["todo"] = _("Todo")


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
    title: Optional[str]
    """The default title to use when rendering the custom admonition. If this is
    not specified, then the `name` value is converted and used."""
    icon: Optional[str] = None
    """The relative path to an icon that will be used in the admonition's
    title. If specified, this path shall be relative to

    - a SVG file placed in the documentation project's
      :confval:`sphinx_immaterial_icon_path` (this takes precedence).
    - the ``.icons`` folder that has `all of the icons bundled with this theme
      <https://github.com/squidfunk/mkdocs-material/tree/master/material/.icons>`_."""
    color: Optional[Tuple[int, int, int]] = None
    """The base color to be used for the admonition's styling. If specified, this
    must be specified as a RGB color space. Each color component shall be
    confined to the range [0, 255]. It is also possible to use the
    :py:mod:`colorsys` module if converting from a different color space (like
    HSL) to RGB."""
    classes: Optional[List[str]]
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

    # pylint: disable=no-self-argument

    @pydantic.validator("name", pre=True)
    def validate_name(cls, val):
        illegal = re.findall(r"([^a-zA-Z0-9\-_])", val)
        if illegal:
            raise ValueError(
                f"The following characters are illegal for directive names: {illegal}"
            )
        return val

    @pydantic.validator("title", always=True)
    def validate_title(cls, val, values):
        if val is None:
            val = " ".join(re.split(r"[\-_]+", values["name"])).title()
        return val

    @pydantic.validator("color", each_item=True)
    def validate_color_component(cls, val):
        if 0 <= val <= 255:
            return val
        raise ValueError(f"color component {val} is not in range [0, 255]")

    @pydantic.validator("classes", each_item=True)
    def conform_classes(cls, val):
        return nodes.make_id(val)

    # pylint: enable=no-self-argument


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

    HTML5Translator.visit_admonition = visit_admonition  # type: ignore[assignment]


def patch_depart_admonition():
    orig_func = HTML5Translator.depart_admonition

    def depart_admonition(self: HTML5Translator, node: Optional[nodes.Element] = None):
        if node is None or node.get("collapsible", None) is None:
            orig_func(self, node)
        else:
            self.body.append("</details>\n")

    HTML5Translator.depart_admonition = depart_admonition  # type: ignore[assignment]


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
    config = app.config
    custom_admonitions: List[CustomAdmonitionConfig] = getattr(
        config, "sphinx_immaterial_custom_admonitions"
    )
    setattr(app.builder.env, "sphinx_immaterial_custom_icons", {})
    for admonition in custom_admonitions:

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
    setattr(app.builder.env, "sphinx_immaterial_custom_admonitions", custom_admonitions)


def on_config_inited(app: Sphinx, config: Config):
    """Add admonitions based on CSS classes inherited from mkdocs-material theme."""

    # override the generic admonition directive
    if getattr(config, "sphinx_immaterial_override_generic_admonitions"):
        app.add_directive("admonition", get_directive_class("admonition", ""), True)

    # generate directives for inherited admonitions from upstream CSS
    if getattr(config, "sphinx_immaterial_generate_extra_admonitions"):
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
            app.add_directive(
                admonition,
                get_directive_class(admonition, _(admonition.title())),
            )
    confval_name = "sphinx_immaterial_custom_admonitions"
    # validate user defined config for custom admonitions
    user_defined_admonitions = pydantic.parse_obj_as(
        List[CustomAdmonitionConfig], getattr(config, confval_name)
    )
    setattr(config, confval_name, user_defined_admonitions)
    user_defined_dir_names = [directive.name for directive in user_defined_admonitions]

    # override the specific admonitions defined in sphinx and docutils
    # these are the admonitions that have translated titles in sphinx.locale
    if getattr(config, "sphinx_immaterial_override_builtin_admonitions"):
        for admonition, title in admonitionlabels.items():

            if admonition in user_defined_dir_names:
                continue
            app.add_directive(admonition, get_directive_class(admonition, title), True)


def consolidate_css(app: Sphinx, env: BuildEnvironment):
    """Generates the CSS for icons and admonitions, then appends that to the
    theme's bundled CSS."""

    theme_options = app.config["html_theme_options"]
    is_palette_defined = False
    if theme_options:
        is_palette_defined = "palette" in theme_options

    custom_admonitions = getattr(env, "sphinx_immaterial_custom_admonitions")
    custom_icons = getattr(env, "sphinx_immaterial_custom_icons")
    jinja_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(PurePath(__file__).parent))
    )
    template = jinja_env.get_template("custom_admonitions.css")
    generated = template.render(
        icons=custom_icons,
        admonitions=custom_admonitions,
    )

    css_data = io.BytesIO()
    # copy pre-minified CSS from theme's bundles
    theme_bundles = Path(__file__).parent / "bundles" / "stylesheets"
    for bundle in theme_bundles.glob("*.min.css"):
        if not is_palette_defined and bundle.name.startswith("palette"):
            continue  # don't need the palette CSS if HTML doesn't need it
        css_data.write(bundle.read_bytes())

    # append the generated CSS for icons and admonitions
    css_data.write(generated.replace("\n", "").encode(encoding="utf-8"))

    # hash CSS data and write to generated file
    css_data_hash = hashlib.sha256(css_data.getvalue()).hexdigest()
    css_name = f"stylesheets/sphinx_immaterial_theme.{css_data_hash[:17]}.min.css"
    css_output = Path(app.outdir, "_static", css_name)
    css_output.parent.mkdir(parents=True, exist_ok=True)
    css_output.write_bytes(css_data.getvalue())

    # ensure new CSS file is added in the rendered HTML output
    app.add_css_file(css_name)


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

    app.connect("builder-inited", on_builder_inited)
    app.connect("env-check-consistency", consolidate_css)
    app.connect("config-inited", on_config_inited)

    patch_visit_admonition()
    patch_depart_admonition()

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
