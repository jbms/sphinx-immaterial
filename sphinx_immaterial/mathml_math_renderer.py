"""Extension that enables docutils' MathML-based math rendering."""

import docutils.nodes
import docutils.utils.math
from docutils.writers._html_base import HTMLTranslator as BaseHTMLTranslator
from sphinx.application import Sphinx

# Sphinx overrides Docutils' math rendering.  Here, we override Sphinx's
# override to revert to docutils' math rendering.


def visit_math(self: BaseHTMLTranslator, node: docutils.nodes.math):
    self.math_output = "mathml"
    self.math_output_options = []
    BaseHTMLTranslator.visit_math(self, node)


def visit_math_block(self: BaseHTMLTranslator, node: docutils.nodes.math_block):
    self.math_output = "mathml"
    self.math_output_options = []
    # Note: We can't call `BaseHTMLTranslator.visit_math_block` here, because
    # that just forwards to `self.visit_math`, which ultimately calls back into
    # our `visit_math` function defined above but without the `math_env`
    # argument.
    BaseHTMLTranslator.visit_math(
        self, node, math_env=docutils.utils.math.pick_math_environment(node.astext())
    )


def setup(app: Sphinx):
    """Setup the extension."""
    app.add_html_math_renderer(
        "mathml",
        (visit_math, None),  # type: ignore[arg-type]
        (visit_math_block, None),  # type: ignore[arg-type]
    )
    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
