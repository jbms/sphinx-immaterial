from sphinx.addnodes import desc_parameterlist


def _monkey_patch_parameterlist_to_support_subscript():
    def astext(self: desc_parameterlist) -> str:
        open_paren, close_paren = self.get("parens", ("(", ")"))
        return f"{open_paren}{super(desc_parameterlist, self).astext()}{close_paren}"

    desc_parameterlist.astext = astext  # type: ignore


_monkey_patch_parameterlist_to_support_subscript()
