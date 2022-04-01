"""A monkey patch to conform code-blocks to superfences' output."""
from docutils import nodes
from sphinx.transforms.post_transforms.code import HighlightLanguageVisitor
from sphinx.writers.html5 import HTML5Translator
from sphinx.application import Sphinx
from sphinx.locale import _


def re_visit_literal_block(
    self: HighlightLanguageVisitor, node: nodes.literal_block
) -> None:
    setting = self.settings[-1]

    node.parent["classes"] += ["highlight"]
    if "language" not in node:
        node["language"] = setting.language
        node["force"] = setting.force
    if "linenos" not in node:
        lines = node.astext().count("\n")
        node["linenos"] = lines >= setting.lineno_threshold - 1


def re_visit_caption(self: HTML5Translator, node: nodes.Element) -> None:
    attributes = {"class": "caption-text"}
    if isinstance(node.parent, nodes.container) and node.parent.get("literal_block"):
        self.body.append('<div class="code-block-caption">')
        attributes["class"] += " filename"
    else:
        super().visit_caption(node)
    self.add_fignumber(node.parent)
    self.body.append(self.starttag(node, "span", **attributes))


def re_depart_caption(self: HTML5Translator, node: nodes.Element) -> None:
    if not isinstance(node.parent, nodes.container) and not node.parent.get(
        "literal_block"
    ):
        self.body.append("</span>")

    # append permalink if available
    if isinstance(node.parent, nodes.container) and node.parent.get("literal_block"):
        self.add_permalink_ref(node.parent, _("Permalink to this code"))
        self.body.append("</span>")
    elif isinstance(node.parent, nodes.figure):
        self.add_permalink_ref(node.parent, _("Permalink to this image"))
    elif node.parent.get("toctree"):
        self.add_permalink_ref(node.parent.parent, _("Permalink to this toctree"))

    if isinstance(node.parent, nodes.container) and node.parent.get("literal_block"):
        self.body.append("</div>\n")
    else:
        super().depart_caption(node)


def setup(app: Sphinx):
    HighlightLanguageVisitor.visit_literal_block = re_visit_literal_block
    HTML5Translator.visit_caption = re_visit_caption
    HTML5Translator.depart_caption = re_depart_caption
