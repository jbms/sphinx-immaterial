"""Fixes ASTDeclarator.isPack method in the Sphinx c++ domain.

https://github.com/sphinx-doc/sphinx/pull/10257
"""

import sphinx
import sphinx.domains.cpp

# Not needed in Sphinx 5.2
assert sphinx.version_info < (5, 2)


def _monkey_patch_cpp_is_pack():
    sphinx.domains.cpp.ASTDeclaratorPtr.isPack = property(lambda self: self.next.isPack)  # type: ignore[assignment]
    sphinx.domains.cpp.ASTDeclaratorRef.isPack = property(lambda self: self.next.isPack)  # type: ignore[assignment]
    sphinx.domains.cpp.ASTDeclaratorMemPtr.isPack = property(  # type: ignore[assignment]
        lambda self: self.next.isPack
    )
    sphinx.domains.cpp.ASTDeclaratorParamPack.isPack = property(lambda self: True)  # type: ignore[assignment]
    sphinx.domains.cpp.ASTDeclaratorParen.isPack = property(  # type: ignore[assignment]
        lambda self: self.inner.isPack or self.next.isPack
    )


_monkey_patch_cpp_is_pack()
