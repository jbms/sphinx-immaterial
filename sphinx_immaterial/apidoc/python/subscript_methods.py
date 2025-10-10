import sphinx.domains.python
from docutils.parsers.rst import directives
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


def _mark_subscript_parameterlist(signode: sphinx.addnodes.desc_signature) -> None:
    """Modifies an object description to display as a "subscript method".

    A "subscript method" is a property that defines __getitem__ and is intended to
    be treated as a method invoked using [] rather than (), in order to allow
    subscript syntax like ':'.

    :param node: Signature to modify in place.
    """
    for sub_node in signode.findall(condition=sphinx.addnodes.desc_parameterlist):
        sub_node["parens"] = ("[", "]")


def _monkey_patch_python_domain_to_support_subscript_option():
    for object_class in sphinx.domains.python.PythonDomain.directives.values():
        if not issubclass(
            object_class,
            (sphinx.domains.python.PyMethod, sphinx.domains.python.PyFunction),
        ):
            continue
        object_class.option_spec["subscript"] = directives.flag

    def _monkey_patch_handle_signature(
        cls: type[sphinx.domains.python.PyObject],
    ) -> None:
        def handle_signature(
            self, sig: str, signode: sphinx.addnodes.desc_signature
        ) -> tuple[str, str]:
            result = super(cls, self).handle_signature(sig, signode)
            if "subscript" in self.options:
                _mark_subscript_parameterlist(signode)

            return result

        setattr(cls, "handle_signature", handle_signature)

    _monkey_patch_handle_signature(sphinx.domains.python.PyFunction)
    _monkey_patch_handle_signature(sphinx.domains.python.PyMethod)


_monkey_patch_parameterlist_to_support_subscript()
_monkey_patch_python_domain_to_support_subscript_option()
