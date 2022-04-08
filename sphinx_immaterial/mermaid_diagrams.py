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
        content = "\n".join(self.content)
        diagram = mermaid_node("", classes=["mermaid"], content=content)
        diagram += nodes.literal("", content, format="html")
        diagram_div = nodes.container(
            "",
            is_div=True,
            classes=["mermaid-diagram"] + self.options.get("class", []),
        )
        if self.options.get("name", ""):
            self.add_name(diagram_div)
        diagram_div += diagram
        self.set_source_info(diagram_div)
        return [diagram_div]


def visit_mermaid_node_html(self, node: mermaid_node):
    attributes = {"class": "mermaid"}
    self.body.append(self.starttag(node, "pre", **attributes))


def depart_mermaid_node_html(self, node: mermaid_node):
    self.body.append("</pre>")


def visit_mermaid_node_latex(self, node: mermaid_node):
    self.body.append("\n\\begin{sphinxVerbatim}[commandchars=\\\\\\{\\}]\n")


def depart_mermaid_node_latex(self, node: mermaid_node):
    self.body.append("\n\\end{sphinxVerbatim}\n")


def setup(app: Sphinx):
    app.add_directive("md-mermaid", MermaidDirective)
    app.add_node(
        mermaid_node,
        html=(visit_mermaid_node_html, depart_mermaid_node_html),
        latex=(visit_mermaid_node_latex, depart_mermaid_node_latex),
    )
    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
