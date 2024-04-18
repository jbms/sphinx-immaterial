"""Adds support for `macroParam` as an object type."""

import sphinx.domains.c

from sphinx.domains.c import (
    Symbol as CSymbol,
    ASTMacro,
    ASTMacroParameter,
    ASTDeclaration,
)


def _monkey_patch_c_macro_parameter_symbols():
    """Adds support for the `macroParam` object type to the C domain."""

    orig_add_function_params = CSymbol._add_function_params

    def _add_function_params(self: CSymbol) -> None:
        orig_add_function_params(self)
        if self.declaration is None or not isinstance(
            self.declaration.declaration, ASTMacro
        ):
            return
        args = self.declaration.declaration.args
        if not args:
            return
        for p in args:
            nn = p.arg
            if nn is None:
                continue
            decl = ASTDeclaration("macroParam", None, p)  # type: ignore[arg-type]
            assert not nn.rooted
            assert len(nn.names) == 1
            self._add_symbols(nn, decl, self.docname, self.line)

    CSymbol._add_function_params = _add_function_params  # type: ignore[assignment]

    def get_id(
        self: ASTMacroParameter, version: int, objectType: str, symbol: CSymbol
    ) -> str:
        # the anchor will be our parent
        assert symbol.parent is not None
        declaration = symbol.parent.declaration
        assert declaration is not None
        return declaration.get_id(version, prefixed=False)

    ASTMacroParameter.get_id = get_id  # type: ignore[attr-defined]

    sphinx.domains.c.CDomain.object_types["macroParam"] = sphinx.domains.ObjType(
        "macro parameter", "identifier", "var", "member", "data"
    )


_monkey_patch_c_macro_parameter_symbols()
