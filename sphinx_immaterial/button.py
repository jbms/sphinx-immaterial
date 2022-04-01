"""A simple directive that creates a HTML ``<a>`` element."""

from typing import List, Any, Tuple
from docutils.parsers.rst import directives
from docutils import nodes
from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective
from sphinx import addnodes
from sphinx.roles import AnyXRefRole
from sphinx.writers.html import HTMLTranslator
from sphinx.util.logging import getLogger
from docutils.parsers.rst import states

LOGGER = getLogger(__name__)


class a_tag_node(nodes.container):
    pass


def visit_a_tag(self: HTMLTranslator, node: a_tag_node):
    attributes = {"class": " ".join(node["classes"])}
    if "href" in node:
        attributes["href"] = node["href"]
    if "reftarget" in node:
        attributes["href"] = node["reftarget"]
    self.body.append(self.starttag(node, "a", **attributes))


def depart_a_tag(self: HTMLTranslator, node: a_tag_node):
    self.body.append("</a>")


class MaterialButtonRole(AnyXRefRole):
    def result_nodes(
        self,
        document: nodes.document,
        env: "BuildEnvironment",
        node: nodes.Element,
        is_ref: bool,
    ) -> Tuple[List[nodes.Node], List[str]]:
        node["classes"] += ["md-button"]
        return super().result_nodes(document, env, node, is_ref)


class MaterialButtonPrimaryRole(AnyXRefRole):
    def result_nodes(
        self,
        document: nodes.document,
        env: "BuildEnvironment",
        node: nodes.Element,
        is_ref: bool,
    ) -> Tuple[List[nodes.Node], List[str]]:
        node["classes"] += ["md-button", "md-button--primary"]
        return super().result_nodes(document, env, node, is_ref)


class BasicButton(SphinxDirective):

    has_content = True
    required_arguments = 1
    option_spec = {
        "name": directives.unchanged,
        "class": directives.class_option,
        "is-md": directives.flag,
        "is-md-primary": directives.flag,
    }

    def run(self) -> List[nodes.Node]:
        """Run the directive."""
        default_cls = []
        if self.options is not None:
            default_cls = self.options.get("class", [])
            if "is-md" in self.options:
                default_cls.append("md-button")
            if "is-md-primary" in self.options:
                default_cls.append("md-button--primary")
        a_tag = a_tag_node("", classes=default_cls, href=self.arguments[0])
        if self.options.get("name", ""):
            self.add_name(a_tag)
        textnodes, _ = self.state.inline_text(self.arguments[0], self.lineno)
        if not self.content:
            a_tag += textnodes
        else:
            a_tag["alt"] = textnodes
            for line in self.content:
                content, _ = self.state.inline_text(line, self.content_offset)
                a_tag += content
        return [a_tag]


class MaterialButton(BasicButton):
    def __init__(
        self,
        name: str,
        arguments: list[Any],
        options: dict[str, Any],
        content: list[str],
        lineno: int,
        content_offset: int,
        block_text: str,
        state: states.RSTState,
        state_machine: states.RSTStateMachine,
    ) -> None:
        if options is not None:
            options["is-md"] = True
        else:
            options = {"is-md": True}
        super().__init__(
            name,
            arguments,
            options,
            content,
            lineno,
            content_offset,
            block_text,
            state,
            state_machine,
        )


class MaterialButtonPrimary(MaterialButton):
    def __init__(
        self,
        name: str,
        arguments: list[Any],
        options: dict[str, Any],
        content: list[str],
        lineno: int,
        content_offset: int,
        block_text: str,
        state: states.RSTState,
        state_machine: states.RSTStateMachine,
    ) -> None:
        if options is not None:
            options["is-md-primary"] = True
        else:
            options = {"is-md-primary": True}
        super().__init__(
            name,
            arguments,
            options,
            content,
            lineno,
            content_offset,
            block_text,
            state,
            state_machine,
        )


def setup(app: Sphinx):
    """Setup the extension."""
    app.add_directive("button", BasicButton)
    app.add_directive("md-button", MaterialButton)
    app.add_directive("md-button-primary", MaterialButtonPrimary)
    app.add_node(a_tag_node, html=(visit_a_tag, depart_a_tag))
    app.add_role("md-button", MaterialButtonRole())
    app.add_role("md-button-primary", MaterialButtonPrimaryRole())
