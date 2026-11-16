"""Emits per-line anchors in code blocks to support line selection.

The ``content.code.select`` feature lets readers select lines in a code block
by clicking on them, and stores the selection in the URL so it can be shared.
Its JavaScript expects each line to be wrapped in a ``<span id="__span-N-L">``
whose first child is an ``<a id="__codelineno-N-L">`` anchor. With mkdocs this
markup comes from pymdownx; we get the same markup from Pygments' ``linespans``
and ``lineanchors`` options.
"""

import docutils.nodes
from sphinx.application import Sphinx

from . import html_translator_mixin


def _wants_line_selection(
    self: html_translator_mixin.HTMLTranslatorMixin, node: docutils.nodes.Element
) -> bool:
    classes = node.get("classes", [])
    if "select" in classes:
        return True
    if "no-select" in classes:
        return False
    features = self.config.html_theme_options.get("features", ())
    return "content.code.select" in features


@html_translator_mixin.override
def visit_literal_block(
    self: html_translator_mixin.HTMLTranslatorMixin,
    node: docutils.nodes.literal_block,
    super_func: html_translator_mixin.BaseVisitCallback[docutils.nodes.literal_block],
):
    if not _wants_line_selection(self, node):
        super_func(self, node)
        return

    # We number code blocks per page, which is what the anchor ids (and so the
    # selection stored in the URL) are scoped to.
    block = getattr(self, "_sphinx_immaterial_code_block_counter", 0)
    self._sphinx_immaterial_code_block_counter = block + 1  # type: ignore[attr-defined]

    # We restore the original highlight arguments afterwards, since the doctree
    # node outlives this translator and these options only concern HTML output.
    orig_highlight_args = node.get("highlight_args")
    highlight_args = dict(orig_highlight_args or {})
    highlight_args.update(
        linespans=f"__span-{block}",
        lineanchors=f"__codelineno-{block}",
        anchorlinenos=True,
    )
    node["highlight_args"] = highlight_args
    try:
        super_func(self, node)
    finally:
        if orig_highlight_args is None:
            del node["highlight_args"]
        else:
            node["highlight_args"] = orig_highlight_args


def setup(app: Sphinx):
    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
