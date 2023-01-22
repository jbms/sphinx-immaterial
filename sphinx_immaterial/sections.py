"""Modifies HTML translation of sections.

Sphinx normally writes sections with a section heading as:

    <div id="identifier" class="section"><hN>...</hN>...</div>

but that is incompatible with the way scroll-margin-top and the
`:target` selector are used in the mkdocs-material CSS.  For
compatibility with mkdocs-material, we strip the outer `<div>` and
instead add the `id` to the inner `<hN>` element.

That is accomplished by overriding `visit_section` and
`depart_section` not to add the `<div>` and `</div>` tags, and also
modifying `visit_title` to insert the `id`.
"""

import docutils.nodes

from . import html_translator_mixin


@html_translator_mixin.override
def visit_section(
    self: html_translator_mixin.HTMLTranslatorMixin,
    node: docutils.nodes.section,
    super_func: html_translator_mixin.BaseVisitCallback[docutils.nodes.section],
) -> None:
    self.section_level += 1


@html_translator_mixin.override
def depart_section(
    self: html_translator_mixin.HTMLTranslatorMixin,
    node: docutils.nodes.section,
    super_func: html_translator_mixin.BaseVisitCallback[docutils.nodes.section],
) -> None:
    self.section_level -= 1


@html_translator_mixin.override
def visit_title(
    self: html_translator_mixin.HTMLTranslatorMixin,
    node: docutils.nodes.title,
    super_func: html_translator_mixin.BaseVisitCallback[docutils.nodes.title],
) -> None:
    if isinstance(node.parent, docutils.nodes.section):
        if node.parent.get("ids") and not node.get("ids"):
            node["ids"] = node.parent.get("ids")
            super_func(self, node)
            del node["ids"]
            return
    super_func(self, node)
