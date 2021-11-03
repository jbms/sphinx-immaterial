"""Taken from sphinxcontrib-details
"""
from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.transforms.post_transforms import SphinxPostTransform
from sphinx.util.nodes import NodeMatcher
from sphinx.util.docutils import SphinxDirective

class material_details(nodes.Element, nodes.General):
    pass


class material_summary(nodes.TextElement, nodes.General):
    pass


def visit_material_details(self, node):
    if node.get("opened"):
        self.body.append(self.starttag(node, "details", open="open"))
    else:
        self.body.append(self.starttag(node, "details"))


def depart_material_details(self, node):
    self.body.append("</details>")


def visit_material_summary(self, node):
    self.body.append(self.starttag(node, "summary"))


def depart_material_summary(self, node):
    self.body.append("</summary>")


class MaterialDetailsDirective(SphinxDirective):
    """Parses the rst directive"""
    optional_arguments = 1  # title of dropdown
    final_argument_whitespace = True
    has_content = True
    option_spec = {
        "class": directives.class_option,
        "name": directives.unchanged,
        "open": directives.flag,
    }

    def run(self):
        admonition = nodes.container(
            "",
            classes=self.options.get("class", []),
            opened="open" in self.options,
            has_title=len(self.arguments) > 0,
            type="details",
        )
        if self.arguments:
            textnodes, messages = self.state.inline_text(self.arguments[0], self.lineno)
            admonition += nodes.rubric(self.arguments[0], "", *textnodes)
            admonition += messages
        self.state.nested_parse(self.content, self.content_offset, admonition)
        self.add_name(admonition)
        return [admonition]


class MaterialDetailsTransform(SphinxPostTransform):
    """Transform docutil node(s) into HTML"""
    default_priority = 200
    formats = ("html",)

    def run(self, **kwargs):
        matcher = NodeMatcher(nodes.container, type="details")
        for node in self.document.traverse(matcher):
            newnode = material_details(**node.attributes)
            newnode += material_summary("", "", *node[0])
            newnode.extend(node[1:])
            node.replace_self(newnode)
