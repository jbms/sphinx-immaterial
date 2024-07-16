"""A directive designed to reduce example snippets duplication."""

from pathlib import PurePath
from docutils.parsers.rst import directives
from docutils import nodes
from sphinx.application import Sphinx
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
            "", classes=self.options.get("class", []) + ["results"]
        )
        code = "\n".join(self.content)
        literal_node: nodes.Element = nodes.literal_block(code, code)
        src_file: str = self.state.document.attributes["source"]
        suffix = PurePath(src_file).suffix.lstrip(".")
        literal_node["language"] = suffix
        if self.arguments:
            literal_node = container_wrapper(self, literal_node, self.arguments[0])
        container_node += literal_node

        if "output-prefix" in self.options:
            out_prefix = nodes.container("", classes=["results-prefix"])
            prefix = self.options.get("output-prefix", "")
            if not prefix:
                prefix = "Which renders the following content:"
            textnodes, _ = self.state.inline_text(prefix, self.lineno)
            out_prefix += textnodes
            container_node += out_prefix

        # the `result` CSS class is theme specific (as used by mkdocs-material theme)
        results_div = nodes.container("", classes=["result"])
        self.state.nested_parse(self.content, self.content_offset, results_div)
        container_node += results_div

        self.set_source_info(container_node)
        self.add_name(container_node)
        return [container_node]


def setup(app: Sphinx):
    app.add_directive("rst-example", ResultsDirective)
    app.add_directive("myst-example", ResultsDirective)
    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
