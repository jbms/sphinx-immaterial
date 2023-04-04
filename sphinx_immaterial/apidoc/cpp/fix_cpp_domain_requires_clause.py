"""Extends support for requires clauses in Sphinx C++ domain.

https://github.com/sphinx-doc/sphinx/pull/10286
"""

import re
from typing import Optional, Union

import sphinx
import sphinx.domains.cpp
from sphinx.domains.cpp import DefinitionParser, ASTDeclaration


# Not needed in Sphinx 5.2
assert sphinx.version_info < (5, 2)


def _monkey_patch_cpp_domain_support_requires_clause():
    orig_parse_declaration = DefinitionParser.parse_declaration

    orig_parse_type = DefinitionParser._parse_type

    def _parse_type(
        self, named: Union[bool, str], outer: Optional[str] = None
    ) -> sphinx.domains.cpp.ASTType:
        orig_assert_end = self.assert_end

        def assert_end_or_requires(allowSemicolon=False):
            # Allow trailing requires on constructors
            self.skip_ws()
            if re.compile(r"requires\b").match(self.definition, self.pos):
                return
            orig_assert_end(allowSemicolon=allowSemicolon)

        if outer == "function":
            try:
                self.assert_end = assert_end_or_requires
                return orig_parse_type(self, named, outer)
            finally:
                self.assert_end = orig_assert_end
        return orig_parse_type(self, named, outer)  # type: ignore[arg-type]

    DefinitionParser._parse_type = _parse_type  # type: ignore[assignment]

    def parse_declaration(
        self: DefinitionParser, objectType: str, directiveType: str
    ) -> ASTDeclaration:
        if objectType not in ("type", "member", "class"):
            ast = orig_parse_declaration(self, objectType, directiveType)
            if (
                objectType == "function"
                and ast.templatePrefix is None
                and ast.trailingRequiresClause is None
            ):
                ast.trailingRequiresClause = self._parse_requires_clause()
                ast.semicolon = ast.semicolon or self.skip_string(";")
            return ast

        try:
            orig_parse_template_declaration_prefix = (
                self._parse_template_declaration_prefix
            )

            requires_clause = None

            def parse_template_declaration_prefix(*args, **kwargs):
                self._parse_template_declaration_prefix = (  # type: ignore[assignment]
                    orig_parse_template_declaration_prefix
                )
                result = orig_parse_template_declaration_prefix(*args, **kwargs)
                if result is None:
                    return None
                nonlocal requires_clause
                requires_clause = self._parse_requires_clause()
                return result

            self._parse_template_declaration_prefix = parse_template_declaration_prefix  # type: ignore[assignment]

            result = orig_parse_declaration(self, objectType, directiveType)
            result.requiresClause = requires_clause  # type: ignore[attr-defined]
            return result
        finally:
            self._parse_template_declaration_prefix = (  # type: ignore[assignment]
                orig_parse_template_declaration_prefix
            )

    DefinitionParser.parse_declaration = parse_declaration  # type: ignore[assignment]


_monkey_patch_cpp_domain_support_requires_clause()
