"""Adds support for resolution symbols through type aliases.

https://github.com/sphinx-doc/sphinx/pull/10296
"""

from typing import Any, Iterator, Optional, Union

import sphinx.domains.cpp
from sphinx.domains.cpp import Symbol

# Different version of the patch required for Sphinx < 8.2.
assert sphinx.version_info >= (8, 2)


def _monkey_patch_cpp_domain_symbol_resolution_through_type_aliases():
    def resolve_type_alias(self: Symbol) -> Optional[Symbol]:
        """Resolves `self` to another symbol if it is a type alias."""
        declaration = self.declaration
        if declaration is None:
            return None
        if declaration.objectType != "type":
            return None
        nested_name: sphinx.domains.cpp.ASTNestedName
        if (
            isinstance(declaration.declaration, sphinx.domains.cpp.ASTTypeUsing)
            and declaration.declaration.type is not None
        ):
            trailing_type_spec = declaration.declaration.type.declSpecs.trailingTypeSpec
            if not isinstance(
                trailing_type_spec, sphinx.domains.cpp.ASTTrailingTypeSpecName
            ):
                return None
            nested_name = trailing_type_spec.name
        elif isinstance(declaration.declaration, sphinx.domains.cpp.ASTType):
            trailing_type_spec = declaration.declaration.declSpecs.trailingTypeSpec
            if not isinstance(
                trailing_type_spec, sphinx.domains.cpp.ASTTrailingTypeSpecName
            ):
                return None
            nested_name = trailing_type_spec.name
        else:
            return None
        assert self.parent is not None
        symbols, failReason = self.parent.find_name(
            nested_name,
            templateDecls=[],
            typ="any",
            matchSelf=False,
            recurseInAnon=True,
            searchInSiblings=False,
            templateShorthand=True,
        )
        if symbols:
            return symbols[0]
        return None

    def resolve_alias_or_base_type(self) -> Iterator["Symbol"]:
        resolved = resolve_type_alias(self)
        if resolved is not None:
            yield resolved
        declaration = self.declaration
        if declaration is None:
            return
        if declaration.objectType != "class":
            return
        for base in declaration.declaration.bases:
            symbols, failReason = self.parent.find_name(
                base.name,
                templateDecls=[],
                typ="any",
                matchSelf=False,
                recurseInAnon=True,
                searchInSiblings=False,
                templateShorthand=True,
            )
            if symbols:
                yield symbols[0]

    orig_find_named_symbols = Symbol._find_named_symbols

    def _find_named_symbols(
        self: Symbol,
        ident_or_op: Union[
            sphinx.domains.cpp.ASTIdentifier, sphinx.domains.cpp.ASTOperator
        ],
        template_params: Any,
        template_args: sphinx.domains.cpp.ASTTemplateArgs,
        template_shorthand: bool,
        match_self: bool,
        recurse_in_anon: bool,
        correct_primary_template_args: bool,
        search_in_siblings: bool,
    ) -> Iterator[Symbol]:
        results = orig_find_named_symbols(
            self,
            ident_or_op,
            template_params,
            template_args,
            template_shorthand,
            match_self,
            recurse_in_anon,
            correct_primary_template_args,
            search_in_siblings,
        )
        found_match = False
        for result in results:
            found_match = True
            yield result

        if found_match:
            return

        if not template_shorthand:
            return

        if template_params is not None or template_args is not None:
            # Try match again, ignoring template params and args.
            results = orig_find_named_symbols(
                self,
                ident_or_op,
                None,  # type: ignore[arg-type]
                None,  # type: ignore[arg-type]
                template_shorthand,
                match_self,
                recurse_in_anon,
                correct_primary_template_args,
                search_in_siblings,
            )
            for result in results:
                found_match = True
                yield result

            if found_match:
                return

        # Try to resolve type alias
        for resolved_symbol in resolve_alias_or_base_type(self):
            if resolved_symbol is self:
                continue
            yield from resolved_symbol._find_named_symbols(  # type: ignore[call-arg]
                ident_or_op,
                template_params,
                template_args,
                template_shorthand,
                match_self,
                recurse_in_anon,
                correct_primary_template_args=False,
                search_in_siblings=False,
            )

    Symbol._find_named_symbols = _find_named_symbols  # type: ignore[assignment]

    in_symbol_lookup_with_shorthand = []

    orig_symbol_lookup = Symbol._symbol_lookup

    def _symbol_lookup(
        self,
        nested_name,
        template_decls,
        on_missing_qualified_symbol,
        strict_template_param_arg_lists: bool,
        ancestor_lookup_type: str,
        template_shorthand: bool,
        match_self: bool,
        recurse_in_anon: bool,
        correct_primary_template_args: bool,
        search_in_siblings: bool,
    ):
        try:
            in_symbol_lookup_with_shorthand.append(template_shorthand)

            return orig_symbol_lookup(
                self,
                nested_name,
                template_decls,
                on_missing_qualified_symbol,
                strict_template_param_arg_lists,
                ancestor_lookup_type,
                template_shorthand,
                match_self,
                recurse_in_anon,
                correct_primary_template_args,
                search_in_siblings,
            )

        finally:
            in_symbol_lookup_with_shorthand.pop()

    Symbol._symbol_lookup = _symbol_lookup  # type: ignore[assignment]

    orig_find_identifier = Symbol.find_identifier

    def find_identifier(
        self,
        identOrOp: Union[
            sphinx.domains.cpp.ASTIdentifier, sphinx.domains.cpp.ASTOperator
        ],
        matchSelf: bool,
        recurseInAnon: bool,
        searchInSiblings: bool,
    ):
        s = orig_find_identifier(
            self, identOrOp, matchSelf, recurseInAnon, searchInSiblings
        )
        if s is not None:
            return s
        if (
            not in_symbol_lookup_with_shorthand
            or not in_symbol_lookup_with_shorthand[-1]
        ):
            return None
        for other in resolve_alias_or_base_type(self):
            if other is self:
                continue
            s = other.find_identifier(
                identOrOp=identOrOp,
                matchSelf=matchSelf,
                recurseInAnon=recurseInAnon,
                searchInSiblings=False,
            )
            if s is not None:
                return s
        return None

    Symbol.find_identifier = find_identifier  # type: ignore[assignment]


_monkey_patch_cpp_domain_symbol_resolution_through_type_aliases()
