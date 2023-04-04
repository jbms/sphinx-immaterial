"""Extension that adds `highlight-push` and `highlight-pop` directives."""

from typing import List

import docutils.nodes
import sphinx.addnodes
import sphinx.application
import sphinx.util.docutils
import sphinx.util.logging
from sphinx.transforms.post_transforms.code import HighlightLanguageVisitor

logger = sphinx.util.logging.getLogger(__name__)


class HighlightPushDirective(sphinx.util.docutils.SphinxDirective):
    has_content = False
    required_arguments = 0
    optional_arguments = 0

    def run(self) -> List[docutils.nodes.Node]:
        stack = self.env.temp_data.setdefault("highlight_language_stack", [])
        stack.append(self.env.temp_data.get("highlight_language"))
        return [sphinx.addnodes.highlightlang(push=True)]


class HighlightPopDirective(sphinx.util.docutils.SphinxDirective):
    has_content = False
    required_arguments = 0
    optional_arguments = 0

    def run(self) -> List[docutils.nodes.Node]:
        stack = self.env.temp_data.get("highlight_language_stack")
        if not stack:
            logger.error(
                "`highlight-pop` directive not preceded by `highlight-push` directive",
                location=self.get_location(),
            )
            return []
        language = stack.pop()
        if language is None:
            self.env.temp_data.pop("highlight_language", None)
        else:
            self.env.temp_data["highlight_language"] = language
        return [sphinx.addnodes.highlightlang(pop=True)]


def _monkey_patch_highlight_language_visitor():
    orig_visit_highlightlang = HighlightLanguageVisitor.visit_highlightlang

    def visit_highlightlang(self, node: sphinx.addnodes.highlightlang) -> None:
        if "push" in node.attributes:
            self.settings.append(self.settings[-1])
        elif "pop" in node.attributes:
            if self.settings:
                self.settings.pop()
            else:
                logger.error(
                    "highlight-pop node not preceded by hihglight-push node",
                    location=node,
                )
            if not self.settings:
                self.settings.append(self.default_setting)
                logger.error(
                    "highlight-pop node not preceded by hihglight-push node",
                    location=node,
                )
        else:
            orig_visit_highlightlang(self, node)

    HighlightLanguageVisitor.visit_highlightlang = visit_highlightlang  # type: ignore[assignment]


_monkey_patch_highlight_language_visitor()


def setup(app: sphinx.application.Sphinx):
    app.add_directive("highlight-push", HighlightPushDirective)
    app.add_directive("highlight-pop", HighlightPopDirective)

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
