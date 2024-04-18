"""Adds support for :noindex:, :symbol-ids:, and :node-id: options."""

import json
from typing import Optional, Union, Type, List

import docutils.parsers.rst.directives
import sphinx.addnodes
import sphinx.domains.c
import sphinx.domains.cpp

AST_ID_OVERRIDE_ATTR = "_sphinx_immaterial_id"
ANCHOR_ATTR = "sphinx_immaterial_anchor"


def _monkey_patch_override_ast_id(
    ast_declaration_class: Union[
        Type[sphinx.domains.c.ASTDeclaration], Type[sphinx.domains.cpp.ASTDeclaration]
    ],
):
    """Allows the Symbol id to be overridden."""
    orig_get_id = ast_declaration_class.get_id

    def get_id(
        self: Union[sphinx.domains.c.ASTDeclaration, sphinx.domains.cpp.ASTDeclaration],
        version: int,
        prefixed: bool = True,
    ):
        entity_id = getattr(self, AST_ID_OVERRIDE_ATTR, None)
        if entity_id is not None:
            return entity_id
        return orig_get_id(self, version, prefixed)  # type: ignore

    ast_declaration_class.get_id = get_id  # type: ignore


def get_symbol_anchor(
    symbol: Union[sphinx.domains.c.Symbol, sphinx.domains.cpp.Symbol],
) -> str:
    anchor = None
    if symbol.declaration is not None:
        anchor = getattr(symbol.declaration, ANCHOR_ATTR, None)
    if anchor is None:
        assert symbol.declaration is not None
        anchor = symbol.declaration.get_newest_id()
    return anchor


def _monkey_patch_cpp_noindex_option(
    object_class: Union[
        Type[sphinx.domains.c.CObject], Type[sphinx.domains.cpp.CPPObject]
    ],
    ast_declaration_class: Union[
        Type[sphinx.domains.c.ASTDeclaration], Type[sphinx.domains.cpp.ASTDeclaration]
    ],
    env_parent_symbol_key: str,
    duplicate_symbol_error: Union[
        Type[sphinx.domains.c._DuplicateSymbolError],
        Type[sphinx.domains.cpp._DuplicateSymbolError],
    ],
):
    object_class.option_spec["noindex"] = docutils.parsers.rst.directives.flag
    object_class.option_spec["symbol-ids"] = json.loads
    object_class.option_spec["node-id"] = lambda s: s or ""
    orig_handle_signature = object_class.handle_signature

    NEW_SYMBOLS_ATTR = "_sphinx_immaterial_new_symbols"

    SIGNATURE_INDEX_ATTR = "_sphinx_immaterial_signature_index"

    def handle_signature(
        self: Union[sphinx.domains.c.CObject, sphinx.domains.cpp.CPPObject],
        sig: str,
        signode: sphinx.addnodes.desc_signature,
    ):
        signature_index = getattr(self, SIGNATURE_INDEX_ATTR, -1) + 1
        setattr(self, SIGNATURE_INDEX_ATTR, signature_index)

        parentSymbol = self.env.temp_data[env_parent_symbol_key]
        orig_add_declaration = parentSymbol.add_declaration

        # For the `noindex` option, keep track of symbols that are added so that
        # they can be removed.
        new_symbols = getattr(self, NEW_SYMBOLS_ATTR, None)
        if new_symbols is None:
            new_symbols = []
            setattr(self, NEW_SYMBOLS_ATTR, new_symbols)

        symbol_ids = self.options.get("symbol-ids")
        symbol_id: Optional[str] = None
        if symbol_ids and signature_index < len(symbol_ids):
            symbol_id = symbol_ids[signature_index]

        def add_declaration(declaration, docname: str, line: int):
            if symbol_id is not None:
                setattr(declaration, AST_ID_OVERRIDE_ATTR, symbol_id)
            try:
                symbol = orig_add_declaration(declaration, docname, line)
                assert new_symbols is not None
                new_symbols.append(symbol)
            except duplicate_symbol_error as e:
                # Ignore duplicate symbols
                symbol = e.symbol
                declaration.symbol = symbol
                # Temporarily clear siblingAbove/siblingBelow to avoid an assertion
                # failure in `orig_handle_signature`.  They will be restored by
                # `orig_handle_signature`.
                siblingBelow = symbol.siblingBelow
                siblingAbove = symbol.siblingAbove
                if siblingAbove is not None:
                    if siblingAbove is not symbol:
                        symbol.siblingAbove.siblingBelow = siblingBelow
                    symbol.siblingAbove = None
                if siblingBelow is not None:
                    if siblingBelow is not symbol:
                        symbol.siblingBelow.siblingAbove = siblingAbove
                    symbol.siblingBelow = None

                # Remove duplicate symbol that was just created
                for other_symbol in symbol.parent._children:
                    if other_symbol.declaration is declaration:
                        assert other_symbol.isRedeclaration
                        other_symbol.remove()
                        break
                else:
                    raise AssertionError(  # pylint: disable=raise-missing-from
                        "Duplicate symbol not found: %r" % (symbol.dump(2),)
                    )
            return symbol

        parentSymbol.add_declaration = add_declaration
        try:
            return orig_handle_signature(self, sig, signode)  # type: ignore[arg-type]
        finally:
            parentSymbol.add_declaration = orig_add_declaration

    object_class.handle_signature = handle_signature  # type: ignore[assignment]

    orig_add_target_and_index = object_class.add_target_and_index

    def add_target_and_index(
        self: Union[sphinx.domains.c.CObject, sphinx.domains.cpp.CPPObject],
        ast: Union[sphinx.domains.c.ASTDeclaration, sphinx.domains.cpp.ASTDeclaration],
        sig: str,
        signode: sphinx.addnodes.desc_signature,
    ) -> None:
        node_id = self.options.get("node-id")
        if node_id is not None:
            symbol = ast.symbol
            assert symbol is not None
            assert symbol.declaration is not None
            setattr(symbol.declaration, ANCHOR_ATTR, node_id)
            symbol.docname = self.env.docname
            if ast is self.names[0] and node_id:
                signode["ids"].append(node_id)
            return

        orig_add_target_and_index(self, ast, sig, signode)  # type: ignore[arg-type]

    object_class.add_target_and_index = add_target_and_index  # type: ignore[assignment]

    orig_run = object_class.run

    def run(
        self: Union[sphinx.domains.c.CObject, sphinx.domains.cpp.CPPObject],
    ) -> List[docutils.nodes.Node]:
        result = orig_run(self)  # type: ignore[arg-type]

        if "noindex" in self.options:
            new_symbols = getattr(self, NEW_SYMBOLS_ATTR, None)
            if new_symbols:
                for s in new_symbols:
                    s.remove()

        return result

    object_class.run = run  # type: ignore[assignment]


_monkey_patch_override_ast_id(sphinx.domains.c.ASTDeclaration)
_monkey_patch_override_ast_id(sphinx.domains.cpp.ASTDeclaration)
_monkey_patch_cpp_noindex_option(
    object_class=sphinx.domains.cpp.CPPObject,
    ast_declaration_class=sphinx.domains.cpp.ASTDeclaration,
    env_parent_symbol_key="cpp:parent_symbol",
    duplicate_symbol_error=sphinx.domains.cpp._DuplicateSymbolError,
)
_monkey_patch_cpp_noindex_option(
    object_class=sphinx.domains.c.CObject,
    ast_declaration_class=sphinx.domains.c.ASTDeclaration,
    env_parent_symbol_key="c:parent_symbol",
    duplicate_symbol_error=sphinx.domains.c._DuplicateSymbolError,
)
