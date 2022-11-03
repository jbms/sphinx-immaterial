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
    """This class serves as a user's value(s) to
    :confval:`sphinx_immaterial_custom_admonitions`. Each instantiated object
    corresponds to a custom :dudir:`admonition directive <admonitions>` created with
    theme specific options.
    """

    def __init__(
        self,
        name: str,
        color: Tuple[int, int, int],
        icon: str,
        title: str = None,
        override: bool = False,
    ):
        """
        :param name: The name of the directive. This will be also used as a CSS class
            name.
        :param icon: The relative path to an icon that will be used in the admonition's
            title. This path shall be relative to

            - the ``.icons`` folder that has `all of the icons bundled with this theme
              <https://github.com/squidfunk/mkdocs-material/tree/master/material/
              .icons>`_ (this takes precedence).
            - a SVG file placed in the documentation project's `html_static_path`.
        :param color: The base color to be used for the admonition's styling. This
            must be specified as a RGB color space. It is also possible to use the
            :py:mod:`colorsys` module if converting from a different color space (like
            HSL) to RGB.
        :param title: The title to use when rendering the custom admonition. If this is
            not specified, then the ``name`` parameter is converted using
            :py:meth:`~str.title()` after the ``-`` and ``_`` characters are replaced
            with spaces.
        :param override: Can be used to override an existing directive. Only set this to
            :python:`True` if the directive being overridden is an
            :dudir:`existing admonition <admonitions>`.

        .. _custom_admonition_example:

        As an demonstration, we will be using the following configuration:

        .. literalinclude:: conf.py
            :language: python
            :start-after: # BEGIN CUSTOM ADMONITIONS
            :end-before: # END CUSTOM ADMONITIONS

        The above setting will create a directive that can be used like so:

        .. rst-example::

            .. example-admonition::
                This is simple a example

            .. example-admonition::
                :no-title:

                Just some admonished text, no title.

            .. example-admonition::
                :collapsible: open

                A collapsible admonition that is expanded by default.

            .. example-admonition::
                :collapsible: any

                If the :rst:`:collapsible:` option's value is anything but ``open``,
                then the collapsible admonition is closed by default.

        The created custom admonitions could be documented in the following manner.
        Note that only the name of the directive (:rst:dir:`example-admonition`) is subject to
        change depending on the value of the ``name`` parameter.

        .. rst:directive:: example-admonition

            A custom admonition created from the `example's configuration
            <custom_admonition_example>`.

            .. rst:directive:option:: no-title

                This flag will skip rendering the admonition's title.

                .. error::
                    This option cannot be used simultaneously with the
                    :rst:`:collapsible:` option.
            .. rst:directive:option:: collapsible

                This option can be used to convert the custom admonition into a
                collapsible admonition. A value of ``open`` will make the admonition
                expanded by default. Any other value is ignored and will make the
                admonition collapsed by default.
            .. rst:directive:option:: name

                Set this option with a qualified ID to reference the admonition from
                other parts of the documentation using the `ref` role.
            .. rst:directive:option:: class

                If further CSS styling is needed, then use this option to append a CSS
                class name to the rendered HTML elements.
        """
        self.name = name
        assert len(color) == 3, "color must have 3 components"
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
    setattr(app.builder.env, "sphinx_immaterial_custom_icons", {})
    for admonition in custom_admonitions:
        if not isinstance(admonition, CustomAdmonition):
            raise TypeError(
                "config values for custom admonitions must use the class "
                "sphinx_immaterial.custom_admonitions.CustomAdmonition"
            )

        class UserAdmonition(CustomAdmonitionDirective):
            default_title = admonition.title
            name = admonition.name

        app.add_directive(
            name=admonition.name, cls=UserAdmonition, override=admonition.override
        )

        # set variables for CSS template to match HTML output from generated directives
        admonition.name = nodes.make_id(admonition.name)
        admonition.icon = load_svg_into_builder_env(app.builder, admonition.icon)
    setattr(app.builder.env, "sphinx_immaterial_custom_admonitions", custom_admonitions)


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
        types=list,
    )
    app.connect("builder-inited", on_builder_inited)
    app.connect("build-finished", on_build_finished)

    patch_visit_admonition()
    patch_depart_admonition()

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
