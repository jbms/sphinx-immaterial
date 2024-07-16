"""Monkey patches C/C++ resolve_xref to save the resolved symbol.

This also other customizations to make use of the resolved symbol.
"""

from typing import Union, Type, Tuple, Optional

import docutils.nodes
import sphinx.addnodes
import sphinx.domains.c
import sphinx.domains.cpp

from sphinx.domains.c import Symbol as CSymbol, CDomain
from sphinx.domains.cpp import Symbol as CPPSymbol, CPPDomain

_last_resolved_symbol: Optional[Union[CSymbol, CPPSymbol]] = None
"""Symbol resolved by `_resolve_xref_inner` or `get_objects`.

This allows additional customizations of those functions to access the symbol.
"""


def get_symbol():
    return _last_resolved_symbol


def set_symbol(symbol: Optional[Union[CSymbol, CPPSymbol]]):
    global _last_resolved_symbol
    _last_resolved_symbol = symbol


def _monkey_patch_resolve_xref_save_symbol(
    symbol_class: Union[Type[CSymbol], Type[CPPSymbol]],
    domain_class: Union[Type[CDomain], Type[CPPDomain]],
):
    orig_resolve_xref_inner = domain_class._resolve_xref_inner

    def _resolve_xref_inner(
        self: Union[CDomain, CPPDomain],
        env: sphinx.environment.BuildEnvironment,
        fromdocname: str,
        builder: sphinx.builders.Builder,
        typ: str,
        target: str,
        node: sphinx.addnodes.pending_xref,
        contnode: docutils.nodes.Element,
    ) -> Tuple[Optional[docutils.nodes.Element], Optional[str]]:
        set_symbol(None)

        orig_find_name = getattr(symbol_class, "find_name", None)

        if orig_find_name:

            def find_name(self: Union[CSymbol, CPPSymbol], *args, **kwargs):
                symbols, failReason = orig_find_name(self, *args, **kwargs)  # type: ignore
                if symbols:
                    set_symbol(symbols[0])
                return symbols, failReason

            symbol_class.find_name = find_name  # type: ignore

        orig_find_declaration = symbol_class.find_declaration

        def find_declaration(self: Union[CSymbol, CPPSymbol], *args, **kwargs):
            symbol = orig_find_declaration(self, *args, **kwargs)  # type: ignore
            if symbol:
                set_symbol(symbol)
            return symbol

        symbol_class.find_declaration = find_declaration  # type: ignore

        try:
            return orig_resolve_xref_inner(
                self,  # type: ignore[arg-type]
                env,
                fromdocname,
                builder,
                typ,
                target,
                node,
                contnode,  # type: ignore
            )
        finally:
            if orig_find_name:
                symbol_class.find_name = orig_find_name  # type: ignore
            symbol_class.find_declaration = orig_find_declaration  # type: ignore

    domain_class._resolve_xref_inner = _resolve_xref_inner  # type: ignore


_monkey_patch_resolve_xref_save_symbol(
    sphinx.domains.cpp.Symbol, sphinx.domains.cpp.CPPDomain
)
_monkey_patch_resolve_xref_save_symbol(
    sphinx.domains.c.Symbol, sphinx.domains.c.CDomain
)
