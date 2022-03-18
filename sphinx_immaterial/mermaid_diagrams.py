"""A custom directive that allows using mermaid diagrams"""
from typing import List
from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util.docutils import SphinxDirective
from sphinx.application import Sphinx


class mermaid_node(nodes.General, nodes.Element):
    pass


class MermaidDirective(SphinxDirective):
    """a special directive"""

    has_content = True
    option_spec = {
        "name": directives.unchanged,
        "class": directives.class_option,
    }

    def run(self) -> List[nodes.Node]:
        """Run the directive."""
        self.assert_has_content()
        diagram = mermaid_node(
            "",
            classes=["mermaid"] + self.options.get("class", []),
            name=self.options.get("name", ""),
            content="\n".join(self.content),
        )
        self.set_source_info(diagram)
        return [diagram]


def visit_mermaid(self, node: mermaid_node):
    attributes = {"class": " ".join(node["classes"]), "name": node["name"]}
    self.body.append(self.starttag(node, "pre", **attributes))
    self.body.append("<code>\n" + node["content"])


def depart_mermaid(self, node: mermaid_node):
    self.body.append("</code></pre>")


def setup(app: Sphinx):
    app.add_directive("md-mermaid", MermaidDirective)
    app.add_node(mermaid_node, html=(visit_mermaid, depart_mermaid))
