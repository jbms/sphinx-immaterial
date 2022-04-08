"""This module inherits from the generic ``admonition`` directive and makes the
title optional."""
from docutils import nodes
from docutils.parsers.rst.roles import set_classes
from docutils.parsers.rst.directives import admonitions
from sphinx.application import Sphinx

__version__ = "0.0.1"


class NoTitleAdmonition(admonitions.BaseAdmonition):

    optional_arguments = 1
    node_class = nodes.admonition
    default_title = ""

    classes = ()

    def run(self):
        set_classes(self.options)
        if self.classes:
            self.options.setdefault("classes", list(self.classes))
        self.assert_has_content()
        text = "\n".join(self.content)
        admonition_node = self.node_class(text, **self.options)
        self.add_name(admonition_node)
        if self.node_class is nodes.admonition:
            title_text = self.arguments[0] if self.arguments else self.default_title
            textnodes, messages = self.state.inline_text(title_text, self.lineno)
            title = nodes.title(title_text, "", *textnodes)
            title.source, title.line = self.state_machine.get_source_and_line(
                self.lineno
            )
            if title_text:
                admonition_node += title
            admonition_node += messages
            if not self.options.get("classes") and title_text:
                admonition_node["classes"] += ["admonition" + nodes.make_id(title_text)]
        self.state.nested_parse(self.content, self.content_offset, admonition_node)
        return [admonition_node]


def setup(app: Sphinx):
    """register our custom directive."""
    app.add_directive("md-admonition", NoTitleAdmonition)

    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
