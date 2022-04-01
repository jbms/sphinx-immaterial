"""A directive designed to reduce example snippets duplication."""
from docutils.parsers.rst import directives
from docutils import nodes
from sphinx.util.docutils import SphinxDirective
from sphinx.directives.code import container_wrapper


class ResultsDirective(SphinxDirective):
    """Takes content as a rst code snippet and renders it after outputting it as a
    literal code-block."""

    has_content = True
    optional_arguments = 1
    final_argument_whitespace = True
    option_spec = {
        "class": directives.class_option,
        "name": directives.unchanged,
        "output-prefix": directives.unchanged,
    }

    def run(self):
        """Run the directive."""
        container_node = nodes.container(
            "", is_div=True, classes=self.options.get("class", []) + ["results"]
        )
        code = "\n".join(self.content)
        literal_node = nodes.literal_block(
            code, code, caption="" if not self.arguments else self.arguments[0]
        )
        literal_node["language"] = "rst"
        literal_node["classes"] += ["highlight"]
        if self.arguments:
            literal_node = container_wrapper(
                self, literal_node=literal_node, caption=self.arguments[0]
            )
        results_div = nodes.container("", is_div=True, classes=["result"])
        if "output-prefix" in self.options:
            out_prefix = nodes.container("", classes=["results-prefix"])
            prefix = self.options.get("output-prefix", "")
            if not prefix:
                prefix = "Which renders the following content:"
            textnodes, _ = self.state.inline_text(prefix, self.lineno)
            out_prefix += textnodes
            results_div += out_prefix
        self.state.nested_parse(self.content, self.content_offset, results_div)
        container_node += literal_node
        container_node += results_div
        self.set_source_info(container_node)
        self.add_name(container_node)
        return [container_node]


def setup(app):
    app.add_directive("result", ResultsDirective)
