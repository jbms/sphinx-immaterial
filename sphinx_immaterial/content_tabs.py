"""
A special theme-specific extension to support "content tabs" from mkdocs-material.
"""

from typing import List
from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util.docutils import SphinxDirective
from sphinx.application import Sphinx
from sphinx.util.logging import getLogger
from sphinx.writers.html import HTMLTranslator

LOGGER = getLogger(__name__)


def is_md_tab_type(node: nodes.Node, name: str):
    """Check if a node is a certain tabbed component."""
    if not isinstance(node, nodes.Element):
        return False
    return node.get("type") == name


class content_tab_set(nodes.container):
    pass


class MaterialTabSetDirective(SphinxDirective):
    """A container for a set of tab items."""

    has_content = True
    option_spec = {
        "name": directives.unchanged,
        "class": directives.class_option,
    }

    def run(self) -> List[nodes.Node]:
        """Run the directive."""
        self.assert_has_content()
        tab_set = content_tab_set(
            "",
            is_div=True,
            type="md-tab-set",
            classes=["tabbed-set", "tabbed-alternate"] + self.options.get("class", []),
        )
        self.set_source_info(tab_set)
        if self.options.get("name", ""):
            self.add_name(tab_set)
        self.state.nested_parse(self.content, self.content_offset, tab_set)
        for item in tab_set.children:
            if not is_md_tab_type(item, "md-tab-item"):
                LOGGER.warning(
                    "All children of a 'md-tab-set' should be 'md-tab-item'",
                    location=item,
                )
                break
        return [tab_set]


class MaterialTabItemDirective(SphinxDirective):
    """A single tab item in a tab set.
    Note: This directive generates a single container,
    for the label and content::
        <container design_component="tab-item" has_title=True>
            <rubric>
                ...title nodes
            <container design_component="tab-content">
                ...content nodes
    This allows for a default rendering in non-HTML outputs.
    The ``MaterialTabSetHtmlTransform`` then transforms this container
    into the HTML specific structure.
    """

    required_arguments = 1  # the tab label is the first argument
    final_argument_whitespace = True
    has_content = True
    option_spec = {
        "class": directives.class_option,
    }

    def run(self) -> List[nodes.Node]:
        """Run the directive."""
        self.assert_has_content()
        if not is_md_tab_type(self.state_machine.node, "md-tab-set"):
            LOGGER.warning(
                "The parent of a 'md-tab-item' should be a 'md-tab-set'",
                location=(self.env.docname, self.lineno),
            )
        tab_item = nodes.container(
            "", is_div=True, type="md-tab-item", classes=["tabbed-block"]
        )

        # add tab label
        textnodes, _ = self.state.inline_text(self.arguments[0], self.lineno)
        tab_label = nodes.rubric("", "", *textnodes, classes=["tabbed-label"])
        self.add_name(tab_label)
        tab_item += tab_label

        # add tab content
        tab_content = nodes.container(
            "",
            is_div=True,
            type="",
            classes=["tabbed-block"] + self.options.get("class", []),
        )
        self.state.nested_parse(self.content, self.content_offset, tab_content)
        tab_item += tab_content

        return [tab_item]


class content_tab_label(nodes.TextElement, nodes.General):
    pass


def visit_tab_label(self, node):
    attributes = {"for": node["input_id"]}
    self.body.append(self.starttag(node, "label", **attributes))


def depart_tab_label(self, node):
    self.body.append("</label>")


def visit_tab_set(self: HTMLTranslator, node: content_tab_set):
    # increment tab set counter
    tab_set_count: int = getattr(self, "tab_set_count", 0) + 1
    setattr(self, "tab_set_count", tab_set_count)

    # configure tab set's div attributes
    tab_set_identity = f"__tabbed_{tab_set_count}"
    attributes = {"data-tabs": f"{tab_set_count}:{len(node.children)}"}
    self.body.append(self.starttag(node, "div", **attributes))

    # walkabout the children
    tab_label_div = nodes.container("", is_div=True, classes=["tabbed-labels"])
    tab_content_div = nodes.container("", is_div=True, classes=["tabbed-content"])
    for tab_count, tab_item in enumerate(node.children):
        assert isinstance(tab_item, nodes.Element)
        try:
            tab_label, tab_block = tab_item.children
        except ValueError as exc:
            raise ValueError(f"md-tab-item has no children:\n{repr(tab_item)}") from exc
        tab_item_identity = tab_set_identity + f"_{tab_count + 1}"

        assert isinstance(tab_label, nodes.Element)

        # create: <input checked="checked" id="id" type="radio">
        self.body.append(
            "<input "
            + ("checked " if not tab_count else "")
            + f'type="radio" id="{self.attval(tab_item_identity)}"'
            + f' name="{self.attval(tab_set_identity)}">'
        )

        # create: <label for="id">...</label>
        label_node = content_tab_label(
            "",
            "",
            *tab_label.children,
            input_id=tab_item_identity,
            classes=tab_label["classes"],
        )
        label_node.source, label_node.line = tab_item.source, tab_item.line
        tab_label_div += label_node

        # add content
        tab_content_div += tab_block

    tab_label_div.walkabout(self)
    tab_content_div.walkabout(self)
    self.body.append("</div>")
    raise nodes.SkipNode()


def depart_tab_set(self: HTMLTranslator, node: content_tab_set):
    pass  # pragma: no cover


def setup(app: Sphinx):
    app.add_directive("md-tab-set", MaterialTabSetDirective)
    app.add_directive("md-tab-item", MaterialTabItemDirective)
    app.add_node(content_tab_label, html=(visit_tab_label, depart_tab_label))
    app.add_node(content_tab_set, html=(visit_tab_set, depart_tab_set))
    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
