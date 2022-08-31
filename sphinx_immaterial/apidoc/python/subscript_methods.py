from sphinx.addnodes import desc_parameterlist

from ... import html_translator_mixin


@html_translator_mixin.override
def visit_desc_parameterlist(
    self: html_translator_mixin.HTMLTranslatorMixin,
    node: desc_parameterlist,
    super_func: html_translator_mixin.BaseVisitCallback[desc_parameterlist],
) -> None:
    super_func(self, node)
    open_paren, _ = node.get("parens", ("(", ")"))
    self.body[-1] = self.body[-1].replace("(", open_paren)


@html_translator_mixin.override
def depart_desc_parameterlist(
    self: html_translator_mixin.HTMLTranslatorMixin,
    node: desc_parameterlist,
    super_func: html_translator_mixin.BaseVisitCallback[desc_parameterlist],
) -> None:
    super_func(self, node)
    _, close_paren = node.get("parens", ("(", ")"))
    self.body[-1] = self.body[-1].replace(")", close_paren)


def _monkey_patch_parameterlist_to_support_subscript():
    def astext(self: desc_parameterlist) -> str:
        open_paren, close_paren = self.get("parens", ("(", ")"))
        return f"{open_paren}{super(desc_parameterlist, self).astext()}{close_paren}"

    desc_parameterlist.astext = astext  # type: ignore


_monkey_patch_parameterlist_to_support_subscript()
