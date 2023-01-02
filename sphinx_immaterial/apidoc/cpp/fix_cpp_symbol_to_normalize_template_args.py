"""Normalizes the representation of Symbols for non-specialized templates.

https://github.com/sphinx-doc/sphinx/pull/10257

When declaring e.g.::

    .. cpp:function:: template <typename T> int A<T>::foo()

If there was a previous definition of:

    .. cpp:class:: template <typename T> class A

Then the symbol table will be of the form:

    A: template <typename T> class A
      foo: int foo()

However, if there is no previous definition of the class, then the symbol
table will be of the form (where A has template arguments):

    A: template <typename T> class A<T>
      foo: int foo()

That leads to symbol lookup problems due to the way we remove symbols defined
as part of the "summary".  This monkey patch ensures that the representation
is consistent regardless of whether the class is declared first.
"""

from typing import Union, Any

import sphinx
import sphinx.domains.cpp
from sphinx.domains.cpp import Symbol

# Not needed in Sphinx 5.2
assert sphinx.version_info < (5, 2)


def _is_cpp_ast_specialization(
    templateParams: Union[
        sphinx.domains.cpp.ASTTemplateParams, sphinx.domains.cpp.ASTTemplateIntroduction
    ],
    templateArgs: Any,
) -> bool:
    # the names of the template parameters must be given exactly as args
    # and params that are packs must in the args be the name expanded
    if len(templateParams.params) != len(templateArgs.args):
        return True
    # having no template params and no arguments is also a specialization
    if len(templateParams.params) == 0:
        return True
    for i, param in enumerate(templateParams.params):
        arg = templateArgs.args[i]
        # TODO: doing this by string manipulation is probably not the most efficient
        paramName = str(getattr(param, "name"))
        argTxt = str(arg)
        isArgPackExpansion = argTxt.endswith("...")
        if getattr(param, "isPack") != isArgPackExpansion:
            return True
        argName = argTxt[:-3] if isArgPackExpansion else argTxt
        if paramName != argName:
            return True
    return False


def _monkey_patch_cpp_symbol_to_normalize_template_args():
    orig_init = Symbol.__init__

    def __init__(
        self: Symbol,
        parent: Symbol,
        identOrOp: Union[
            sphinx.domains.cpp.ASTIdentifier, sphinx.domains.cpp.ASTOperator
        ],
        templateParams: Union[
            sphinx.domains.cpp.ASTTemplateParams,
            sphinx.domains.cpp.ASTTemplateIntroduction,
        ],
        templateArgs: Any,
        declaration: sphinx.domains.cpp.ASTDeclaration,
        docname: str,
        line: int,
    ) -> None:
        if templateArgs is not None and not _is_cpp_ast_specialization(
            templateParams, templateArgs
        ):
            templateArgs = None
        orig_init(
            self,
            parent,
            identOrOp,
            templateParams,
            templateArgs,
            declaration,
            docname,
            line,
        )

    Symbol.__init__ = __init__  # type: ignore[assignment]


_monkey_patch_cpp_symbol_to_normalize_template_args()
