"""Fixes ASTDeclarator.isPack method in the Sphinx c++ domain.

https://github.com/sphinx-doc/sphinx/pull/10257
"""

import sphinx.domains.cpp


def _monkey_patch_cpp_is_pack():
    sphinx.domains.cpp.ASTDeclaratorPtr.isPack = property(lambda self: self.next.isPack)
    sphinx.domains.cpp.ASTDeclaratorRef.isPack = property(lambda self: self.next.isPack)
    sphinx.domains.cpp.ASTDeclaratorMemPtr.isPack = property(
        lambda self: self.next.isPack
    )
    sphinx.domains.cpp.ASTDeclaratorParamPack.isPack = property(lambda self: True)
    sphinx.domains.cpp.ASTDeclaratorParen.isPack = property(
        lambda self: self.inner.isPack or self.next.isPack
    )


_monkey_patch_cpp_is_pack()
