"""
A special theme-specific extension to support "content tabs" from mkdocs-material.
"""
from typing import List, Any
from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util.docutils import SphinxDirective
from sphinx.util.nodes import NodeMatcher
from sphinx.application import Sphinx
from sphinx.util.logging import getLogger
from sphinx.transforms.post_transforms import SphinxPostTransform


page_tab_set_counter = [0]
LOGGER = getLogger(__name__)


def is_component(node: nodes.Node, name: str):
    """Check if a node is a certain tabbed component."""
    try:
        return node.get("type") == name
    except AttributeError:
        return False


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
        page_tab_set_counter[0] += 1
        self.state.nested_parse(self.content, self.content_offset, tab_set)
        tab_total = 0
        for item in tab_set.children:
            if not is_component(item, "md-tab-item"):
                LOGGER.warning(
                    "All children of a 'md-tab-set' should be 'md-tab-item'",
                    location=item,
                )
                break
            tab_total += 1
        tab_set["data-tabs"] = f"{page_tab_set_counter[0]}:{tab_total}"
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
        if not is_component(self.state_machine.node, "md-tab-set"):
            LOGGER.warning(
                "The parent of a 'md-tab-item' should be a 'md-tab-set'",
                location=(self.env.docname, self.lineno),
            )
        tab_item = nodes.container(
            "", is_div=True, type="md-tab-item", classes=["tabbed-block"]
        )

        # add tab label
        textnodes, _ = self.state.inline_text(self.arguments[0], self.lineno)
        tab_label = nodes.rubric(
            self.arguments[0],
            *textnodes,
            classes=["tabbed-label"],
        )
        self.add_name(tab_label)
        tab_item += tab_label

        # add tab content
        tab_content = nodes.container(
            "", is_div=True, type="", classes=["tabbed-block"] + self.options.get("class", [])
        )
        self.state.nested_parse(self.content, self.content_offset, tab_content)
        tab_item += tab_content

        return [tab_item]


class content_tab_input(nodes.Element, nodes.General):
    pass


class content_tab_label(nodes.TextElement, nodes.General):
    pass


def visit_tab_input(self, node):
    attributes = {"ids": [node["id"]], "type": node["type"], "name": node["set_id"]}
    if node["checked"]:
        attributes["checked"] = "checked"
    self.body.append(self.starttag(node, "input", **attributes))


def depart_tab_input(self, node):
    self.body.append("</input>")


def visit_tab_label(self, node):
    attributes = {"for": node["input_id"]}
    self.body.append(self.starttag(node, "label", **attributes))


def depart_tab_label(self, node):
    self.body.append("</label>")


def visit_tab_set(self, node):
    attributes = {"data-tabs": node["data-tabs"]}
    self.body.append(self.starttag(node, "div", **attributes))


def depart_tab_set(self, node):
    self.body.append("</div>")


class MaterialTabSetHtmlTransform(SphinxPostTransform):
    """Transform tab-set to HTML specific AST structure."""

    default_priority = 200
    formats = ("html",)

    def run(self, **kwargs: Any) -> None:
        """Run the transform."""
        matcher = NodeMatcher(nodes.container, type="md-tab-set")
        for set_numb, tab_set in enumerate(self.document.traverse(matcher)):
            tab_set_identity = f"__tabbed_{set_numb + 1}"
            children = []
            tab_label_div = nodes.container("", is_div=True, classes=["tabbed-labels"])
            tab_content_div = nodes.container(
                "", is_div=True, classes=["tabbed-content"]
            )
            tab_total = 0
            for tab_item in tab_set.children:
                try:
                    tab_label, tab_block = tab_item.children
                except ValueError:
                    print(tab_item)
                    raise
                tab_total += 1
                tab_item_identity = tab_set_identity + f"_{tab_total}"

                # create: <input checked="checked" id="id" type="radio">
                input_node = content_tab_input(
                    "",
                    id=tab_item_identity,
                    set_id=tab_set_identity,
                    type="radio",
                    checked=(tab_total == 1),
                )
                input_node.source, input_node.line = tab_item.source, tab_item.line
                children.append(input_node)

                # create: <label for="id">...</label>
                label_node = content_tab_label(
                    "",
                    *tab_label.children,
                    input_id=tab_item_identity,
                    classes=tab_label["classes"],
                )
                label_node.source, label_node.line = tab_item.source, tab_item.line
                tab_label_div += label_node

                # add content
                tab_content_div += tab_block

            tab_set.children = children
            tab_set += tab_label_div
            tab_set += tab_content_div


def setup(app: Sphinx) -> None:
    app.add_directive("md-tab-set", MaterialTabSetDirective)
    app.add_directive("md-tab-item", MaterialTabItemDirective)
    app.add_post_transform(MaterialTabSetHtmlTransform)
    app.add_node(content_tab_input, html=(visit_tab_input, depart_tab_input))
    app.add_node(content_tab_label, html=(visit_tab_label, depart_tab_label))
    app.add_node(content_tab_set, html=(visit_tab_set, depart_tab_set))
