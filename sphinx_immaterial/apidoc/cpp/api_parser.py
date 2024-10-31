"""Converts a preprocessed C++ source file into a JSON API description.

This program expects as input preprocessed C++ source code obtained using the
`-E` (preprocessed), `-C` (preserve comments), and `-dD` (preserve macro
definitions) GCC/Clang options.  It also accepts a list of compiler options to
be passed to Clang, although these are mostly irrelevant due to the prior
preprocessing.

It uses a combination of the libclang Python bindings and the C++ parser in the
Sphinx Python package to parse declarations and definitions and produce a JSON
representation of the API.

The JSON representation describes the API as a set of "entities", each with a
unique id, and relations between them.

Libclang can handle arbitrary C++ syntax, but provides very restricted access to
the resultant AST.  To workaround those limitations, in some cases extracted
declarations or portions of declarations are converted back to source
representation and re-parsed using the C++ parser provided by the Sphinx C++
domain.  The C++ parser in Sphinx is extremely limited and as it does not rely
on a symbol table does not always correctly handle template arguments, but
provides full access to its AST.

This program performs a number of transformations on the declarations:

- Exported entities are filtered using various criteria

- `std::enable_if_t` uses are converted to C++20 requires clauses.

- Internal return types are elided (replaced with auto).
"""

import argparse
import dataclasses
import functools
import json
import os
import pathlib
import re
import time
import typing
from typing import (
    cast,
    Dict,
    Any,
    List,
    Tuple,
    Optional,
    Sequence,
    Union,
    Pattern,
    Literal,
    Callable,
    TypedDict,
    Iterator,
)
from textwrap import dedent

import ctypes

import clang.cindex
from clang.cindex import (
    Cursor,
    CursorKind,
    Token,
    TokenKind,
    TranslationUnit,
    SourceLocation,
    SourceRange,
)
import docutils.nodes
import pydantic.dataclasses
import sphinx.domains.cpp
import sphinx.util.logging
from typing_extensions import NotRequired

from . import ast_fixes  # noqa: F401


logger = sphinx.util.logging.getLogger(__name__)

_UNMATCHABLE_REGEXP = re.compile("a^")


def _combine_regexp_list(items: Sequence[Union[str, Pattern[str]]]) -> re.Pattern:
    if not items:
        return _UNMATCHABLE_REGEXP

    def get_parenthesized_source(x: Union[str, Pattern[str]]):
        if isinstance(x, re.Pattern):
            x = x.pattern
        return f"(?:{x})"

    return re.compile("|".join(get_parenthesized_source(x) for x in items))


def _make_replacement_pattern(
    strings: List[str], prefix: str, suffix: str
) -> re.Pattern:
    if not strings:
        return _UNMATCHABLE_REGEXP
    return re.compile(
        "|".join(rf"(?:{prefix}{re.escape(before)}{suffix})" for before in strings)
    )


TEMPLATE_PARAMETER_ENABLE_IF_TYPE_PATTERN = re.compile(
    r"\s*(?:typename|class)\s*=\s*std\s*::\s*enable_if_t\s*<(.*)>\s*"
)
TEMPLATE_PARAMETER_ENABLE_IF_NON_TYPE_PATTERN = re.compile(
    r"\s*std\s*::\s*enable_if_t\s*<(.*)>\s*\*\s*=\s*(nullptr|0)\s*"
)

SPECIAL_GROUP_COMMAND_PATTERN = re.compile(
    r"^(?:\\|@)(ingroup|relates|membergroup|id)\s+(.*[^\s])\s*$", re.MULTILINE
)


@pydantic.dataclasses.dataclass
class Config:
    """Specifies a C++ API parsing configuration.

    Based on this configuration, a description of the API is generated.
    """

    input_path: str = "__input.cpp"
    """Path to the input file to parse.

    This may either be a path to an existing file, or `.input_content` may
    specify its content, in which case the filesystem is not accessed.

    If `.input_content` is specified and merely contains :cpp:`#include`
    directives, then the actual path does not matter and may be left as the
    default value.
    """

    input_content: Optional[bytes] = None
    """Specifies the content of `.input_path`.

    If unspecified, the content is read from filesystem.
    """

    compiler_flags: List[str] = dataclasses.field(default_factory=list)
    """List of compiler flags to pass to Clang."""

    verbose: bool = False
    """Parse in verbose mode."""

    include_directory_map: Dict[str, str] = dataclasses.field(default_factory=dict)
    """Maps actual include directories to a displayed directory name.

    The keys should be prefixes of paths specified in error messages/source
    locations identified by clang.

    The values should be the corresponding prefix to use in the documented
    :cpp:`#include` paths.
    """

    allow_paths: List[Pattern] = dataclasses.field(
        default_factory=lambda: [re.compile("")]
    )
    """List of regular expressions matching *allowed* paths.

    Only entities defined in files that match `.allow_paths`, and don't match
    `.disallow_paths`, are documented.  By default all entities are documented,
    but this default is not normally usable, because it will include entities
    defined in the standard library and third-party libraries.

    .. important::
        When building on Windows, all path separators are normalized to :python:`"/"`.
        Therefore, in the specified regular expressions, always use :python:`"/"` to
        match a path separator.
    """

    disallow_paths: List[Pattern] = dataclasses.field(default_factory=list)
    """List of regular expressions matching *disallowed* paths.

    Entities defined in files matching any of these patterns are not documented.

    .. important::
        When building on Windows, all path separators are normalized to :python:`"/"`.
        Therefore, in the specified regular expressions, always use :python:`"/"` to
        match a path separator.
    """

    disallow_namespaces: List[Pattern] = dataclasses.field(default_factory=list)
    """List of regular expressions matching *disallowed* namespaces.

    Entities defined in namespaces matching any of the specified patterns are
    not documented.
    """

    allow_symbols: List[Pattern] = dataclasses.field(
        default_factory=lambda: [re.compile("")]
    )
    """List of regular expressions matching *allowed* symbols.

    Only symbols matching one of the `.allow_symbols` patterns, and not matching
    `.disallow_symbols`, are documented.  By default, all symbols are allowed.
    """

    disallow_symbols: List[Pattern] = dataclasses.field(default_factory=list)
    """List of regular expressions matching *disallowed* symbols.

    Symbols matching any of these patterns are undocumented.
    """

    allow_macros: List[Pattern] = dataclasses.field(
        default_factory=lambda: [re.compile("")]
    )
    """List of regular expressions matching *allowed* macros.

    Only macros names matching `.allow_macros`, and not matching
    `.disallow_macros`, are documented.
    """

    disallow_macros: List[Pattern] = dataclasses.field(default_factory=list)
    """List of regular expressions matching *disallowed* macro names.

    Macros matching any of these patterns are undocumented.
    """

    ignore_diagnostics: List[Pattern] = dataclasses.field(default_factory=list)
    """List of regular expressions matching diagnostics to ignore.

    Diagnostics matching any of these patterns are ignored.
    """

    template_parameter_enable_if_patterns: List[Pattern] = dataclasses.field(
        default_factory=lambda: [
            TEMPLATE_PARAMETER_ENABLE_IF_TYPE_PATTERN,
            TEMPLATE_PARAMETER_ENABLE_IF_NON_TYPE_PATTERN,
        ]
    )

    type_replacements: Dict[str, str] = dataclasses.field(default_factory=dict)
    """Remaps type names."""

    hide_types: List[Pattern] = dataclasses.field(default_factory=list)
    """List of regular expressions matching *hidden* types.

    Matching return types are replaced with :cpp:`auto`, and matching
    initializers are elided.
    """
    ignore_template_parameters: List[Pattern] = dataclasses.field(default_factory=list)
    """List of regular expressions matching *ignored* template parameters.

    Template parameters with a declaration matching any of these patterns are
    excluded from the generated documentation.
    """

    hide_initializers: List[Pattern] = dataclasses.field(
        default_factory=lambda: [re.compile(r"^=\s*(?:(true|false)\s*$|\[)")]
    )
    """List of regular expressions matching initializers to elide.

    Any matching initializer expression is elided from the generated
    documentation.
    """

    # Derived from `allow_paths`.
    allow_path_pattern: Pattern = dataclasses.field(init=False)

    # Derived from `disallow_paths`.
    disallow_path_pattern: Pattern = dataclasses.field(init=False)

    # Derived from `allow_symbols`.
    allow_symbols_pattern: Pattern = dataclasses.field(init=False)

    # Derived from `disallow_symbols`.
    disallow_symbols_pattern: Pattern = dataclasses.field(init=False)

    # Derived from `allow_macros`.
    allow_macros_pattern: Pattern = dataclasses.field(init=False)

    # Derived from `disallow_macros`.
    disallow_macros_pattern: Pattern = dataclasses.field(init=False)

    # Derived from `ignore_diagnostics`.
    ignore_diagnostics_pattern: Pattern = dataclasses.field(init=False)

    # Derived from `hide_types`.
    hide_types_pattern: Pattern = dataclasses.field(init=False)

    # Derived from `type_replacements`.
    type_replacements_pattern: Pattern = dataclasses.field(init=False)

    # Derived from `ignore_template_parameters`.
    ignore_template_parameters_pattern: Pattern = dataclasses.field(init=False)

    # Derived from `hide_initializers`.
    hide_initializers_pattern: Pattern = dataclasses.field(init=False)

    include_directory_map_pattern: Pattern = dataclasses.field(init=False)

    disallow_namespaces_pattern: Pattern = dataclasses.field(init=False)

    def __post_init__(self):
        self.allow_path_pattern = _combine_regexp_list(self.allow_paths)  # type: ignore[misc]
        self.disallow_path_pattern = _combine_regexp_list(self.disallow_paths)  # type: ignore[misc]
        self.allow_path_pattern = _combine_regexp_list(self.allow_paths)  # type: ignore[misc]
        self.disallow_namespaces_pattern = _combine_regexp_list(
            self.disallow_namespaces
        )
        self.allow_symbols_pattern = _combine_regexp_list(self.allow_symbols)  # type: ignore[misc]
        self.disallow_symbols_pattern = _combine_regexp_list(self.disallow_symbols)  # type: ignore[misc]
        self.allow_macros_pattern = _combine_regexp_list(self.allow_macros)  # type: ignore[misc]
        self.disallow_macros_pattern = _combine_regexp_list(self.disallow_macros)  # type: ignore[misc]
        self.ignore_diagnostics_pattern = _combine_regexp_list(self.ignore_diagnostics)  # type: ignore[misc]
        self.hide_types_pattern = _combine_regexp_list(self.hide_types)  # type: ignore[misc]
        self.type_replacements_pattern = _make_replacement_pattern(  # type: ignore[misc]
            list(self.type_replacements.keys()), prefix=r"\b", suffix=r"\b"
        )
        self.ignore_template_parameters_pattern = _combine_regexp_list(  # type: ignore[misc]
            self.ignore_template_parameters
        )
        self.hide_initializers_pattern = _combine_regexp_list(self.hide_initializers)  # type: ignore[misc]
        if os.name == "nt":
            self.normalized_include_directory_map = {  # type: ignore[misc]
                key.replace("\\", "/"): value
                for key, value in self.include_directory_map.items()
            }
        else:
            self.normalized_include_directory_map = self.include_directory_map  # type: ignore[misc]
        self.include_directory_map_pattern = _make_replacement_pattern(  # type: ignore[misc]
            list(self.normalized_include_directory_map.keys()), prefix="^", suffix=""
        )
        self.cached_mapped_include_directories = {}  # type: ignore[misc]

    normalized_include_directory_map: Dict[str, str] = dataclasses.field(init=False)
    cached_mapped_include_directories: Dict[str, str] = dataclasses.field(init=False)

    def map_include_path(self, path: str) -> str:
        mapped = self.cached_mapped_include_directories.get(path)
        if mapped is not None:
            return mapped
        if os.name == "nt":
            path = path.replace("\\", "/")
        if path.startswith("./"):
            path = path[2:]
        new_mapped = self.include_directory_map_pattern.sub(
            lambda m: self.normalized_include_directory_map[m.group(0)], path
        )
        self.cached_mapped_include_directories[path] = new_mapped
        return new_mapped


EntityId = str
EntityKind = Literal[
    "class",
    "conversion_function",
    "function",
    "method",
    "constructor",
    "var",
    "alias",
    "enum",
]
FunctionEntityKind = Literal[
    "conversion_function", "function", "method", "constructor", "destructor"
]

ClassKeyword = Literal["class", "struct"]


class JsonLocation(TypedDict):
    file: str
    line: int
    col: int


class JsonDocComment(TypedDict):
    text: str
    location: JsonLocation


TemplateParameterKind = Literal["type", "template", "non_type"]


class TemplateParameter(TypedDict):
    declaration: str
    name: str
    kind: TemplateParameterKind
    pack: bool


class CppApiEntityBase(TypedDict, total=False):
    id: EntityId
    parent: NotRequired[EntityId]
    scope: NotRequired[str]
    doc: NotRequired[Optional[JsonDocComment]]
    document_with: NotRequired[EntityId]
    siblings: NotRequired[List[EntityId]]
    name: str
    template_parameters: NotRequired[Optional[List[TemplateParameter]]]
    location: JsonLocation
    special_id: NotRequired[Optional[str]]
    page_name: str
    requires: Optional[List[str]]
    specializes: Union[None, EntityId, Literal[True]]
    related_members: Dict[str, List[EntityId]]
    related_nonmembers: Dict[str, List[EntityId]]
    special_membergroup: str
    special_ingroup: str
    special_relates: str
    document_prefix: str
    nonitpick: List[str]


class FunctionEntity(CppApiEntityBase):
    kind: FunctionEntityKind
    arity: int
    name_substitute: str
    friend: bool
    declaration: str


class BaseClass(TypedDict):
    type: str
    access: str


class ClassEntity(CppApiEntityBase):
    kind: Literal["class"]
    keyword: ClassKeyword
    prefix: List[str]
    bases: List[BaseClass]


class VarEntity(CppApiEntityBase):
    kind: Literal["var"]
    declaration: str
    name_substitute: str
    initializer: Optional[str]


class TypeAliasEntity(CppApiEntityBase):
    kind: Literal["alias"]
    underlying_type: Optional[str]


class MacroEntity(CppApiEntityBase):
    kind: Literal["macro"]
    parameters: Optional[List[str]]


class EnumeratorEntity(TypedDict):
    kind: Literal["enumerator"]
    id: EntityId
    name: str
    decl: str
    doc: Optional[JsonDocComment]
    location: JsonLocation


class EnumEntity(CppApiEntityBase):
    kind: Literal["enum"]
    keyword: Optional[ClassKeyword]
    enumerators: List[EnumeratorEntity]


CppApiEntity = Union[
    ClassEntity, FunctionEntity, VarEntity, TypeAliasEntity, MacroEntity, EnumEntity
]


def json_location_to_string(location: Optional[JsonLocation]) -> Optional[str]:
    if location is None:
        return None
    return "%s:%s:%s" % (location["file"], location["line"], location["col"])


def get_entity_id(cursor: Cursor) -> EntityId:
    # USR workarounds from:
    # https://github.com/foonathan/cppast/blob/e558e2d58f519e3a83af770d460672b1d4ba2886/src/libclang/parse_functions.cpp#L13
    usr = cursor.get_usr()
    if cursor.kind in (CursorKind.FUNCTION_TEMPLATE, CursorKind.CONVERSION_FUNCTION):
        # Combine return type with USR to prevent collisions
        return f"{usr} {cursor.result_type.spelling}"
    if cursor.kind == CursorKind.CLASS_TEMPLATE_PARTIAL_SPECIALIZATION:
        # libclang issue: templ<T()> vs templ<T() &>
        # but identical USR
        # same workaround: combine display name with usr
        # (and hope this prevents all collisions...)
        return f"{usr} {cursor.displayname}"
    return usr


def _substitute_internal_type_names(config: Config, decl: str) -> str:
    return config.type_replacements_pattern.sub(
        lambda m: config.type_replacements[m.group(0)], decl
    )


def get_previous_line_location(tu, location: SourceLocation):
    file = location.file
    line = location.line
    return SourceLocation.from_position(tu, file, line - 1, 1)


def get_presumed_location(location: SourceLocation) -> typing.Tuple[str, int, int]:
    file, line, col = clang.cindex._CXString(), ctypes.c_uint(), ctypes.c_uint()
    clang.cindex.conf.lib.clang_getPresumedLocation(
        location, ctypes.byref(file), ctypes.byref(line), ctypes.byref(col)
    )
    return (clang.cindex._CXString.from_result(file), int(line.value), int(col.value))


_clang_getFileContents = clang.cindex.conf.lib.clang_getFileContents
_clang_getFileContents.restype = ctypes.c_void_p
_PyMemoryView_FromMemory = ctypes.pythonapi.PyMemoryView_FromMemory
_PyMemoryView_FromMemory.argtypes = (ctypes.c_char_p, ctypes.c_ssize_t, ctypes.c_int)
_PyMemoryView_FromMemory.restype = ctypes.py_object


def _get_file_contents(tu, f):
    size = ctypes.c_size_t()
    ptr = _clang_getFileContents(tu, f, ctypes.byref(size))
    buf = _PyMemoryView_FromMemory(ctypes.cast(ptr, ctypes.c_char_p), size.value, 0x100)
    return buf


def _get_template_cursor_kind(cursor: Cursor) -> CursorKind:
    return CursorKind.from_id(clang.cindex.conf.lib.clang_getTemplateCursorKind(cursor))


def _get_specialized_cursor_template(cursor: Cursor) -> typing.Optional[Cursor]:
    return clang.cindex.conf.lib.clang_getSpecializedCursorTemplate(cursor)


def _get_full_nested_name(cursor: typing.Optional[Cursor]) -> str:
    if cursor is None:
        return ""
    ancestors = []
    while True:
        if cursor.kind == CursorKind.TRANSLATION_UNIT:
            break
        if cursor.kind == CursorKind.NAMESPACE:
            name = cursor.spelling
        else:
            name = cursor.displayname
        ancestors.append(name + "::")
        cursor = cursor.semantic_parent
    ancestors.reverse()
    return "".join(ancestors)


CLASS_KINDS = (
    CursorKind.STRUCT_DECL,
    CursorKind.CLASS_DECL,
    CursorKind.CLASS_TEMPLATE,
    CursorKind.CLASS_TEMPLATE_PARTIAL_SPECIALIZATION,
)


def _get_all_decls(
    config: Config, cursor: Cursor, allow_file
) -> Iterator[tuple[Cursor, SourceLocation]]:
    NAMESPACE = CursorKind.NAMESPACE
    doc_comment_start_bound = cursor.location
    for child in cursor.get_children():
        location = child.location
        if location.file is None:
            continue
        prev_doc_comment_start_bound = doc_comment_start_bound
        doc_comment_start_bound = child.extent.end
        kind = child.kind
        if kind == NAMESPACE:
            if (
                not allow_file or allow_file(get_presumed_location(location)[0])
            ) and not config.disallow_namespaces_pattern.match(child.spelling):
                yield from _get_all_decls(config, child, None)
            continue
        if kind not in ALLOWED_KINDS:
            continue
        if allow_file and not allow_file(get_presumed_location(location)[0]):
            continue
        if child.kind == CursorKind.MACRO_DEFINITION:
            yield (child, prev_doc_comment_start_bound)
            continue
        yield (child, prev_doc_comment_start_bound)
        if kind in CLASS_KINDS:
            yield from _get_all_decls(config, child, None)


# Matches the start of a doc comment.
#
# This is used to test if an individual comment token is a doc comment.
_DOC_COMMENT_START = re.compile(
    r"""
    (?:
      //
      (?:/|!)
    )
    |
    (?:
      /\*
      (?:!|\*)
    )
    """,
    re.VERBOSE,
)

# Matches one or more doc comments with a "<" introducer to indicate that the
# doc comment applies to the entity before it, rather than the entity after it.
#
# This is used by `_get_raw_comments_after`.
_DOC_COMMENT_AFTER = re.compile(
    rb"""
    (
      \s*            # Skip leading whitespace
      (?:
        (
          //           # Comment introducer
          (?:/|!)<     # Doc comment indicator
          [^\r\n]*     # Comment text
          \r?          # Optionally ignored CR
          $            # End of comment line
        )
        |
        (
          /\*         # Comment introducer
          (?:!|\*)<   # Doc comment indicator
          (?:.|\n)*?  # Comment text
          \*/         # Comment terminator
        )
      )
    )+
    """,
    re.MULTILINE | re.VERBOSE,
)


def _get_raw_comments(
    cursor: Cursor, doc_comment_start_bound: SourceLocation
) -> Optional[tuple[str, SourceLocation]]:
    # libclang exposes `cursor.raw_comment` but in some cases it appears to be
    # `None` even if there is in fact a comment. Instead, extract the comments
    # by searching for comment tokens directly.

    translation_unit = cursor.translation_unit

    if cursor.kind == CursorKind.MACRO_DEFINITION:
        # The extent for macro definitions skips the initial "#define". As a
        # workaround, set the end location to the beginning of the line.
        orig_location = cursor.location
        end_location = SourceLocation.from_position(
            translation_unit, orig_location.file, orig_location.line, 1
        )
    else:
        for token in cursor.get_tokens():
            end_location = token.location
            break
        else:
            end_location = cursor.location

    if (
        doc_comment_start_bound.file is None
        or end_location.file is None
        or doc_comment_start_bound.file.name != end_location.file.name  # type: ignore[attr-defined]
    ):
        doc_comment_start_bound = SourceLocation.from_offset(
            translation_unit, end_location.file, 0
        )

    tokens = list(
        translation_unit.get_tokens(
            extent=SourceRange.from_locations(doc_comment_start_bound, end_location)
        )
    )

    tokens.reverse()

    COMMENT = TokenKind.COMMENT
    comment_tokens: list[Token] = []
    for token in tokens:
        token_location = token.extent.end
        if token_location.file.name != end_location.file.name:  # type: ignore[attr-defined]
            break
        if token_location.line < end_location.line - 1:
            break
        if token_location.offset >= end_location.offset:
            continue
        if token.kind != COMMENT:
            break
        end_location = token_location
        comment_tokens.append(token)

    if not comment_tokens:
        return None

    comment_tokens.reverse()
    # Convert comment tokens back into a string, preserving indentation and line
    # breaks.

    comment_text_parts = []
    prev_line = None
    prev_indent = 0
    first_doc_comment_token_i = -1
    doc_comment_end_part_i = 0
    for token_i, token in enumerate(comment_tokens):
        spelling = token.spelling
        is_doc_comment = _DOC_COMMENT_START.match(spelling) is not None
        if first_doc_comment_token_i == -1:
            if not is_doc_comment:
                continue
            first_doc_comment_token_i = token_i
        token_location = token.location
        line = token_location.line
        if prev_line is not None and prev_line != line:
            comment_text_parts.append("\n")
        prev_line = line
        prev_indent = 0
        token_end_location = token.extent.end
        column = token_location.column
        extra_indent = column - prev_indent - 1
        if extra_indent > 0:
            comment_text_parts.append(" " * extra_indent)
        comment_text_parts.append(spelling)
        if is_doc_comment:
            doc_comment_end_part_i = len(comment_text_parts)
        prev_line = token_end_location.line
        prev_indent = token_end_location.column

    if not comment_text_parts:
        return None

    return (
        "".join(comment_text_parts[:doc_comment_end_part_i]),
        comment_tokens[first_doc_comment_token_i].location,
    )


def _get_raw_comments_after(
    tu, location: SourceLocation
) -> Optional[tuple[str, SourceLocation]]:
    buf = memoryview(_get_file_contents(tu, location.file))
    m = _DOC_COMMENT_AFTER.match(buf, location.offset + 1)
    if m is None:
        return None
    return (" " * (location.column - 1) + m.group(0).decode("utf-8") + "\n", location)


# Matches a single multi-line comment, a single-line non-doc comment, or a
# sequence of single-line same-style doc comments.
_COMMENT_PATTERN = re.compile(
    r"""
    (                  # "//" comment (capture group 1)
      [ \t]*           # Skip leading whitespace on first line
      //               # Comment introducer
      ((?:/|!)<?)?     # Optional doc comment indicator (capture group 2)
      [^\n]*           # Comment text
      \n               # End of first line.
      (?:              # Zero or more lines with the same doc comment indicator
        [ \t]*         # Skip leading whitspace
        //\2           # Comment introducer and doc comment indicator.
        [^\n]*         # Comment text
        \n             # End of comment line
      )*
    )
    |
    (                  # "/*" comment (capture group 3)
      [ \t]*           # Skip leading whitespace
      /\*              # Comment introducer
      ((?:\*|!)<?)     # Optional doc comment indicator (capture group 4)
      (?:.|\n)*?       # Comment text
      \*/              # Comment terminator
    )
    """,
    re.VERBOSE,
)


def _convert_raw_comment_into_doc_comment(raw_comment: str) -> str:
    # Eliminate CR characters
    raw_comment = raw_comment.replace("\r", "") + "\n"
    pos = 0
    parts: list[str] = []
    while (m := _COMMENT_PATTERN.match(raw_comment, pos)) is not None:
        pos = m.end(0)
        if not m.group(2) and not m.group(4):
            # Non-doc comment, replace with empty lines to preserve line number mapping
            parts.append("\n" * m.group(0).count("\n"))
            continue

        if m.group(1):
            # // comment
            without_comment_prefix = re.sub(
                r"^[ \t]*//" + re.escape(m.group(2)), "", m.group(0), flags=re.MULTILINE
            )
        else:
            # /* comment
            without_comment_prefix = (
                raw_comment[m.start(0) : m.start(4) - 2]
                + " " * (2 + len(m.group(4)))
                + raw_comment[m.end(4) : m.end(0) - 2]
            )
            # Check if every line is prefixed with an asterisk at the same
            # column as the initial "/*".
            orig_text = m.group(0)
            if re.fullmatch(r"([ \t]*)/\*[^\n]*(\n\1 \*[^\n]*)*(\s*\*/)?", orig_text):
                without_comment_prefix = re.sub(
                    r"^([ \t]*)\*", r"\1 ", without_comment_prefix, flags=re.MULTILINE
                )
        parts.append(dedent(without_comment_prefix))
    assert not raw_comment[pos:].strip(), "Unexpected syntax in raw comment"
    return "".join(parts).rstrip()


_CURSOR_KINDS_THAT_ALLOW_DOC_COMMENTS_AFTER = frozenset(
    [
        CursorKind.VAR_DECL,
        CursorKind.FIELD_DECL,
        # May be variable template.
        CursorKind.UNEXPOSED_DECL,
        CursorKind.TYPE_ALIAS_DECL,
        CursorKind.TYPEDEF_DECL,
        CursorKind.TYPE_ALIAS_TEMPLATE_DECL,
        CursorKind.ENUM_CONSTANT_DECL,
    ]
)


def _get_doc_comment(
    config: Config, cursor: Cursor, doc_comment_start_bound: SourceLocation
) -> Optional[JsonDocComment]:
    raw_comment = _get_raw_comments(cursor, doc_comment_start_bound)

    if (
        raw_comment is None
        and cursor.kind in _CURSOR_KINDS_THAT_ALLOW_DOC_COMMENTS_AFTER
    ):
        raw_comment = _get_raw_comments_after(
            cursor.translation_unit, cursor.extent.end
        )

    if raw_comment is None:
        return None

    raw_comment_text, comment_location = raw_comment
    comment_text = _convert_raw_comment_into_doc_comment(raw_comment_text)
    return {
        "text": comment_text,
        "location": _get_location_json(config, comment_location),
    }


class Extractor:
    def __init__(self, config: Config):
        self.config = config

        input_path = config.input_path

        input_content = config.input_content
        if input_content is None:
            input_content = pathlib.Path(input_path).read_bytes()

        input_content = re.sub(
            b"#pragma clang module", b"//#pragma clang module", input_content
        )

        self.input_source = input_content

        self.index = clang.cindex.Index.create()
        start_time = time.time()
        self.tu = self.index.parse(
            input_path,
            unsaved_files=[(input_path, input_content)],
            args=tuple(config.compiler_flags) + ("-ferror-limit=0",),
            options=(  # TranslationUnit.PARSE_SKIP_FUNCTION_BODIES +
                TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD
            ),
        )
        end_time = time.time()
        if config.verbose:
            logger.info("Parsed C++ input in %.5f seconds", end_time - start_time)

        for diag in self.tu.diagnostics:
            if config.ignore_diagnostics_pattern.search(diag.spelling):
                if config.verbose:
                    logger.info(
                        diag.spelling,
                        location=_get_location_string(config, diag.location),
                    )
                continue
            logger.error(
                diag.spelling, location=_get_location_string(config, diag.location)
            )

        def _allow_file(path: str) -> bool:
            path = config.map_include_path(path)
            if not config.allow_path_pattern.search(path):
                return False
            if config.disallow_path_pattern.search(path):
                return False
            return True

        self.decls = list(
            _get_all_decls(
                config, self.tu.cursor, functools.lru_cache(maxsize=None)(_allow_file)
            )
        )


EXCLUDED_COMPILER_FLAGS = frozenset(
    [
        "-Xclang=-disable-noundef-analysis",
    ]
)


def _transform_type_alias_decl(config: Config, decl: Cursor):
    underlying_type: Optional[str] = _substitute_internal_type_names(
        config, decl.underlying_typedef_type.spelling
    )
    assert underlying_type is not None
    if config.hide_types_pattern.search(underlying_type):
        underlying_type = None

    return {
        "kind": "alias",
        "name": decl.spelling,
        "underlying_type": underlying_type,
    }


def get_extent_spelling(translation_unit: TranslationUnit, extent: SourceRange) -> str:
    """Returns the C++ source representation for the specified extent.

    Comments are excluded and for simplicity all tokens are separated by
    whitespace.  This results in excessive whitespace, but that does not matter
    because this is intended to be parsed by the Sphinx cpp domain anyway.
    """

    def get_spellings():
        prev_token = None
        COMMENT = TokenKind.COMMENT
        for token in translation_unit.get_tokens(extent=extent):
            if prev_token is not None:
                yield prev_token.spelling
                prev_token = None
            if token.kind == COMMENT:
                continue
            prev_token = token
        # We need to handle the last token specially, because clang sometimes parses
        # ">>" as a single token but the extent may cover only the first of the two
        # angle brackets.
        if prev_token is not None:
            spelling = prev_token.spelling
            token_end = cast(SourceLocation, prev_token.extent.end)
            offset_diff = token_end.offset - cast(SourceLocation, extent.end).offset
            if offset_diff != 0:
                yield spelling[:-offset_diff]
            else:
                yield spelling

    return " ".join(get_spellings())


def get_related_comments(decl: Cursor):
    # casts below are workaround for: https://github.com/tgockel/types-clang/pull/2
    start = cast(SourceLocation, decl.extent.start)
    end = cast(SourceLocation, decl.extent.end)
    # Move forward one line to avoid skipping any comments on the last line
    tu = decl.translation_unit
    end = SourceLocation.from_position(tu, end.file, end.line + 1, 1)
    COMMENT = TokenKind.COMMENT
    for token in tu.get_tokens(
        extent=SourceRange.from_locations(cast(int, start), cast(int, end))
    ):
        if token.kind != COMMENT:
            continue
        yield token


NONITPICK_PATTERN = re.compile(r"//\s*NONITPICK:\s*(.*[^\s])\s*")


def get_nonitpick_directives(decl: Cursor) -> List[str]:
    directives = []
    for comment in get_related_comments(decl):
        text = comment.spelling
        m = NONITPICK_PATTERN.match(text)
        if m is None:
            continue
        directives.append(m.group(1))
    return directives


TEMPLATE_CURSOR_KINDS = frozenset(
    [
        CursorKind.FUNCTION_TEMPLATE,
        CursorKind.CLASS_TEMPLATE,
        CursorKind.CLASS_TEMPLATE_PARTIAL_SPECIALIZATION,
        CursorKind.TYPE_ALIAS_TEMPLATE_DECL,
    ]
)

TEMPLATE_PARAMETER_KIND_TO_JSON_KIND = {
    CursorKind.TEMPLATE_TYPE_PARAMETER: "type",
    CursorKind.TEMPLATE_NON_TYPE_PARAMETER: "non_type",
    CursorKind.TEMPLATE_TEMPLATE_PARAMETER: "template",
}


def _clang_template_parameter_to_json(config: Config, decl: Cursor):
    param_decl_str = get_extent_spelling(decl.translation_unit, decl.extent)
    param = _parse_template_parameter(param_decl_str)
    spelling = decl.spelling
    if param is None:
        return {
            "declaration": param_decl_str,
            "name": spelling,
            "kind": TEMPLATE_PARAMETER_KIND_TO_JSON_KIND[decl.kind],
            # Heuristic to determine if it is a pack.
            "pack": "..." in param_decl_str,
        }
    return _sphinx_ast_template_parameter_to_json(config, param)


def _get_template_parameters(config: Config, decl: Cursor):
    if decl.kind not in TEMPLATE_CURSOR_KINDS:
        return None
    result = []
    for child in decl.get_children():
        if child.kind not in (
            CursorKind.TEMPLATE_TYPE_PARAMETER,
            CursorKind.TEMPLATE_NON_TYPE_PARAMETER,
            CursorKind.TEMPLATE_TEMPLATE_PARAMETER,
        ):
            continue
        result.append(_clang_template_parameter_to_json(config, child))
    return result


def _get_non_template_kind(cursor: Cursor):
    kind = cursor.kind
    if kind not in TEMPLATE_CURSOR_KINDS:
        return kind
    return _get_template_cursor_kind(cursor)


def _transform_type_alias_template_decl(
    config: Config, decl: Cursor
) -> TypeAliasEntity:
    underlying_type: Optional[str]
    for child in decl.get_children():
        if child.kind == CursorKind.TYPE_ALIAS_DECL:
            underlying_type = _substitute_internal_type_names(
                config, child.underlying_typedef_type.spelling
            )
            break
    else:
        raise ValueError("Could not determine underlying type")

    requires = []

    if re.search(r"^\s*std\s*::\s*enable_if_t\s*<", underlying_type) is not None:
        presumed_file, presumed_line, _ = get_presumed_location(decl.location)
        parser = sphinx.domains.cpp.DefinitionParser(
            underlying_type,
            location=(presumed_file, presumed_line),
            config=cast(sphinx.config.Config, SphinxConfig()),
        )
        ast = parser._parse_type(False)
        parser.skip_ws()
        parser.assert_end()
        assert isinstance(ast, sphinx.domains.cpp.ASTType)
        requires_expr = _extract_requires_from_enable_if_t_type(config, ast)
        if requires_expr is not None:
            requires.append(requires_expr)
            underlying_type = str(ast)

    if config.hide_types_pattern.search(underlying_type) is not None:
        underlying_type = None
    return {
        "kind": "alias",
        "name": decl.spelling,
        "underlying_type": underlying_type,
        "requires": requires,
    }


def _get_class_keyword(kind: CursorKind) -> ClassKeyword:
    return "class" if kind == CursorKind.CLASS_DECL else "struct"


def _get_bases(config: Config, decl: Cursor):
    for child in decl.get_children():
        if child.kind != CursorKind.CXX_BASE_SPECIFIER:
            continue
        type_spelling = _substitute_internal_type_names(config, child.type.spelling)
        if config.hide_types_pattern.search(type_spelling) is not None:
            continue
        yield {"type": type_spelling, "access": child.access_specifier.name.lower()}


def _transform_class_decl(config: Config, decl: Cursor) -> ClassEntity:
    obj: ClassEntity = {
        "kind": "class",
        "keyword": _get_class_keyword(decl.kind),
        "name": decl.displayname,
        "prefix": _parse_declaration_prefix(decl, is_class=True),
        "bases": list(_get_bases(config, decl)),
    }
    specializes = _get_specialized_cursor_template(decl)
    if specializes:
        obj["specializes"] = get_entity_id(specializes)
    return obj


def _transform_class_template_decl(config: Config, decl: Cursor) -> ClassEntity:
    return {
        "kind": "class",
        "keyword": _get_class_keyword(_get_template_cursor_kind(decl)),
        "name": decl.spelling,
        "prefix": _parse_declaration_prefix(decl, is_class=True),
        "bases": list(_get_bases(config, decl)),
    }


def _transform_class_template_partial_specialization_decl(
    config: Config, decl: Cursor
) -> ClassEntity:
    return {
        "kind": "class",
        "keyword": _get_class_keyword(_get_template_cursor_kind(decl)),
        "name": decl.displayname,
        "specializes": get_entity_id(
            cast(Cursor, _get_specialized_cursor_template(decl))
        ),
        "prefix": _parse_declaration_prefix(decl, is_class=True),
        "bases": list(_get_bases(config, decl)),
    }


def _get_function_parameters(decl: Cursor):
    if decl.kind == CursorKind.FUNCTION_DECL:
        yield from decl.get_arguments()
        return
    for child in decl.get_children():
        if child.kind != CursorKind.PARM_DECL:
            continue
        yield child


FUNCTION_CURSOR_KIND_TO_JSON_KIND = {
    CursorKind.FUNCTION_DECL: "function",
    CursorKind.CXX_METHOD: "method",
    CursorKind.CONSTRUCTOR: "constructor",
    CursorKind.DESTRUCTOR: "destructor",
    CursorKind.CONVERSION_FUNCTION: "conversion_function",
}


def _parse_declaration_prefix(decl: Cursor, is_class: bool) -> typing.List[str]:
    decl_extent = decl.extent
    start_location = decl_extent.start
    end_location = None
    prefix_parts = []
    for child in decl.get_children():
        # Skip template introduction
        if child.kind in (
            CursorKind.TEMPLATE_TYPE_PARAMETER,
            CursorKind.TEMPLATE_NON_TYPE_PARAMETER,
            CursorKind.TEMPLATE_TEMPLATE_PARAMETER,
        ):
            start_location = child.extent.end
            continue
        if child.kind.is_attribute():
            attr_spelling = get_extent_spelling(decl.translation_unit, child.extent)
            prefix_parts.append(f"[[{attr_spelling}]]")
            continue
        end_location = child.extent.start
        break

    if not is_class:
        for token in decl.translation_unit.get_tokens(
            extent=SourceRange.from_locations(
                start_location, end_location or decl_extent.end
            )
        ):
            # skip `inline` since that is not an important part of the API
            if token.spelling in ("explicit", "constexpr"):
                prefix_parts.append(token.spelling)
    return prefix_parts


def _get_declaration_spelling(decl: Cursor) -> str:
    decl_extent = decl.extent
    start_location = decl_extent.start
    end_location = None
    for child in decl.get_children():
        if child.kind.is_statement():
            end_location = child.extent.start
            break
    else:
        end_location = decl_extent.end
    return get_extent_spelling(
        decl.translation_unit,
        extent=SourceRange.from_locations(start_location, end_location),
    )


def _transform_function_decl(config: Config, decl: Cursor):
    name = decl.spelling
    if name.startswith("<deduction guide for "):
        # Exclude deduction guides for now
        return None
    non_template_kind = decl.kind
    if decl.kind == CursorKind.FUNCTION_TEMPLATE:
        non_template_kind = _get_template_cursor_kind(decl)

    specializes = _get_specialized_cursor_template(decl)

    if non_template_kind == CursorKind.CONSTRUCTOR:
        # TODO: handle = default, = delete
        first_bracket = name.find("<")
        if first_bracket != -1:
            name = name[:first_bracket]

        prefix = _parse_declaration_prefix(decl, is_class=False)
        if decl.storage_class == clang.cindex.StorageClass.STATIC:
            prefix.insert(0, "static")
        source_code = _get_declaration_spelling(decl)
        name_substitute = _pick_name_substitute(source_code)
        decl_string = (
            "".join(x + " " for x in prefix)
            + name_substitute
            + "("
            + ", ".join(
                get_extent_spelling(decl.translation_unit, arg.extent)
                for arg in _get_function_parameters(decl)
            )
            + ")"
        )
        requires_expr = None
    else:
        (
            decl_string,
            bare_name,
            template_args,
            name_substitute,
            requires_expr,
        ) = _parse_function(config, decl)
        name = bare_name
        if specializes and template_args is not None:
            name += template_args

    arity = sum(x.kind == CursorKind.PARM_DECL for x in decl.get_children())

    obj = {
        "kind": FUNCTION_CURSOR_KIND_TO_JSON_KIND[non_template_kind],
        "name": name,
        "arity": arity,
        "declaration": decl_string,
        "name_substitute": name_substitute,
        "requires": [requires_expr] if requires_expr else None,
    }
    if specializes:
        obj["specializes"] = get_entity_id(specializes)
    return obj


def _transform_enum_decl(config: Config, decl: Cursor) -> EnumEntity:
    keyword = None
    tokens = list(decl.get_tokens())
    assert len(tokens) >= 2
    assert tokens[0].spelling == "enum"
    token1_spelling = tokens[1].spelling
    if token1_spelling in ("class", "struct"):
        keyword = cast(ClassKeyword, token1_spelling)

    enumerators: List[EnumeratorEntity] = []
    prev_decl_location = decl.location
    for child in decl.get_children():
        if child.kind == CursorKind.ENUM_CONSTANT_DECL:
            enumerators.append(
                {
                    "kind": "enumerator",
                    "id": get_entity_id(child),
                    "name": child.spelling,
                    "decl": get_extent_spelling(decl.translation_unit, child.extent),
                    "doc": _get_doc_comment(config, child, prev_decl_location),
                    "location": _get_location_json(config, child.location),
                }
            )
        prev_decl_location = child.extent.end
    return {
        "kind": "enum",
        "keyword": keyword,
        "name": decl.spelling,
        "enumerators": enumerators,
    }


def _pick_name_substitute(code: str) -> str:
    i = 0
    while True:
        substitute = f"__x{i}"
        if substitute not in code:
            return substitute
        i += 1


def _transform_var_decl(config: Config, decl: Cursor) -> VarEntity:
    exprs = [x for x in decl.get_children() if x.kind.is_expression()]
    presumed_filename, presumed_line, _ = get_presumed_location(decl.location)
    if len(exprs) > 1:
        raise ValueError(
            "%s:%d: Expected VAR decl to have at most one expression as a child: %r, but has: %d"
            % (presumed_filename, presumed_line, decl.spelling, len(exprs))
        )

    prefix = _parse_declaration_prefix(decl, is_class=False)

    type_spelling = decl.type.spelling
    if "(lambda at " in type_spelling:
        type_spelling = "auto"
    name_substitute = _pick_name_substitute(type_spelling)

    initializer = None
    if len(exprs) == 1:
        initializer = "= " + get_extent_spelling(
            decl.translation_unit, exprs[0].extent
        ).rstrip(";")
        if _is_internal_initializer(config, initializer):
            initializer = None
    declaration = " ".join(prefix) + " " + type_spelling + " " + name_substitute
    return {
        "kind": "var",
        "name": decl.spelling,
        "declaration": declaration,
        "name_substitute": name_substitute,
        "initializer": initializer,
    }


class SphinxConfig:
    cpp_id_attributes: Any = []
    cpp_paren_attributes: Any = []


def _parse_name(name: str, template_prefix: str) -> sphinx.domains.cpp.ASTNestedName:
    parser = sphinx.domains.cpp.DefinitionParser(
        f"{template_prefix} int {name}",
        location=("", 0),
        config=cast(sphinx.config.Config, SphinxConfig()),
    )
    ast = parser.parse_declaration("member", "member")
    parser.skip_ws()
    parser.assert_end(allowSemicolon=True)
    return ast.name


def _substitute_name(
    top_ast: sphinx.domains.cpp.ASTDeclaration,
    ast: sphinx.domains.cpp.ASTType,
    source_code: str,
) -> str:
    name_substitute = _pick_name_substitute(source_code)
    template_args = ast.name.names[-1].templateArgs
    name_substitute_with_args = name_substitute
    if template_args is not None:
        name_substitute_with_args += str(template_args)

    template_prefix = ""
    if (
        top_ast.templatePrefix is not None
        and top_ast.templatePrefix.templates is not None
    ):
        template_prefix = str(top_ast.templatePrefix.templates[-1])

    ast.name = _parse_name(name_substitute_with_args, template_prefix=template_prefix)
    return name_substitute_with_args


def _maybe_wrap_requires_expr_in_parentheses(expr: str) -> str:
    parser = sphinx.domains.cpp.DefinitionParser(
        "requires " + expr,
        location=("", 0),
        config=cast(sphinx.config.Config, SphinxConfig()),
    )
    try:
        parser._parse_requires_clause()
        parser.skip_ws()
        parser.assert_end()
        return expr
    except Exception:
        return f"({expr})"


def _extract_requires_from_enable_if_t_type(
    config: Config, ast: sphinx.domains.cpp.ASTType
) -> typing.Optional[str]:
    if not isinstance(
        ast.declSpecs.trailingTypeSpec, sphinx.domains.cpp.ASTTrailingTypeSpecName
    ):
        return None
    decl_specs = ast.declSpecs
    trailing_type_spec = decl_specs.trailingTypeSpec
    if not str(trailing_type_spec).startswith("std::enable_if_t<"):
        return None
    template_args = trailing_type_spec.name.names[1].templateArgs.args  # type: ignore[attr-defined]
    requires_expr = str(template_args[0])
    if len(template_args) == 2:
        result_type = str(template_args[1])
    else:
        result_type = "void"

    parser = sphinx.domains.cpp.DefinitionParser(
        result_type, location=("", 0), config=cast(sphinx.config.Config, SphinxConfig())
    )
    new_ast = parser._parse_type(False)
    parser.skip_ws()
    parser.assert_end()

    new_decl_specs = new_ast.declSpecs

    def copy_qualifiers(
        orig_d: sphinx.domains.cpp.ASTDeclarator,
        new_d: sphinx.domains.cpp.ASTDeclarator,
    ):
        if isinstance(new_d, sphinx.domains.cpp.ASTDeclaratorRef):
            return sphinx.domains.cpp.ASTDeclaratorRef(
                next=copy_qualifiers(orig_d, new_d.next), attrs=new_d.attrs
            )
        if isinstance(new_d, sphinx.domains.cpp.ASTDeclaratorPtr):
            return sphinx.domains.cpp.ASTDeclaratorPtr(
                next=copy_qualifiers(orig_d, new_d.next),
                volatile=new_d.volatile,
                const=new_d.const,
                attrs=new_d.attrs,
            )
        return orig_d

    ast.decl = copy_qualifiers(ast.decl, new_ast.decl)

    decl_specs.trailingTypeSpec = new_decl_specs.trailingTypeSpec
    decl_specs.leftSpecs.const = (
        decl_specs.leftSpecs.const or new_decl_specs.leftSpecs.const
    )
    decl_specs.leftSpecs.volatile = (
        decl_specs.leftSpecs.volatile or new_decl_specs.leftSpecs.volatile
    )
    decl_specs.rightSpecs.const = (
        decl_specs.rightSpecs.const or new_decl_specs.rightSpecs.const
    )
    decl_specs.rightSpecs.volatile = (
        decl_specs.rightSpecs.volatile or new_decl_specs.rightSpecs.volatile
    )

    return _substitute_internal_type_names(config, requires_expr)


_FUNCTION_NAME_REPLACEMENTS = {
    "operator[ ]": "operator[]",
    "operator( )": "operator()",
}


def _parse_function(config: Config, decl: Cursor):
    presumed_file, presumed_line, _ = get_presumed_location(decl.location)
    source_code = _get_declaration_spelling(decl)
    parser = sphinx.domains.cpp.DefinitionParser(
        source_code,
        location=(presumed_file, presumed_line),
        config=cast(sphinx.config.Config, SphinxConfig()),
    )
    ast = parser.parse_declaration("function", "function")
    parser.skip_ws()
    parser.assert_end(allowSemicolon=True)
    assert isinstance(ast.declaration, sphinx.domains.cpp.ASTType)

    requires_expr = _extract_requires_from_enable_if_t_type(config, ast.declaration)

    last_name_element = ast.declaration.name.names[-1]

    bare_name = str(last_name_element.identOrOp)
    bare_name = _FUNCTION_NAME_REPLACEMENTS.get(bare_name, bare_name)
    template_args = last_name_element.templateArgs

    template_args_str = str(template_args) if template_args is not None else None

    name_substitute = _substitute_name(ast, ast.declaration, source_code)

    # Exclude `inline` specifier since it isn't really informative in API
    # documentation.
    ast.declaration.declSpecs.leftSpecs.inline = False

    decl_string = _substitute_internal_type_names(config, str(ast.declaration))
    return decl_string, bare_name, template_args_str, name_substitute, requires_expr


def _is_internal_initializer(config: Config, initializer: str) -> bool:
    return (
        config.hide_initializers_pattern.search(initializer) is not None
        or config.hide_types_pattern.search(initializer) is not None
    )


def _sphinx_ast_template_parameter_to_json(
    config: Config, param: sphinx.domains.cpp.ASTTemplateParam
) -> TemplateParameter:
    if isinstance(param, sphinx.domains.cpp.ASTTemplateParamType):
        kind = "type"
    elif isinstance(param, sphinx.domains.cpp.ASTTemplateParamTemplateType):
        kind = "template"
    else:
        kind = "non_type"

    identifier = param.get_identifier()

    return {
        "declaration": _substitute_internal_type_names(config, str(param)),
        "name": str(identifier) if identifier else "",
        "kind": cast(TemplateParameterKind, kind),
        "pack": param.isPack,  # type: ignore[attr-defined]
    }


def _transform_unexposed_decl(config: Config, decl: Cursor) -> Optional[VarEntity]:
    # libclang unfortunately does not support variable templates; they are only
    # exposed as an unexposed decl.

    source_code = get_extent_spelling(decl.translation_unit, decl.extent)

    # Note: Since `source_code` is reconstructed from the tokens, we don't need to
    # worry about inconsistency in spacing.
    if not source_code.startswith("template <"):
        return None

    # Assume that it is a variable template
    # Attempt to parse it via sphinx's c++ domain parser

    presumed_file, presumed_line, _ = get_presumed_location(decl.location)

    try:
        parser = sphinx.domains.cpp.DefinitionParser(
            source_code,
            location=(presumed_file, presumed_line),
            config=cast(sphinx.config.Config, SphinxConfig()),
        )
        ast = parser.parse_declaration("member", "member")
        parser.skip_ws()
        parser.assert_end(allowSemicolon=True)

        declaration = cast(
            Union[
                sphinx.domains.cpp.ASTTypeWithInit,
                sphinx.domains.cpp.ASTTemplateParamConstrainedTypeWithInit,
            ],
            ast.declaration,
        )
        template_args = declaration.type.name.names[-1].templateArgs
        name = str(declaration.type.name.names[-1])
        name_substitute = _substitute_name(ast, declaration.type, source_code)

        decl_string = _substitute_internal_type_names(config, str(declaration.type))
        decl_string = re.sub("(^| )inline ", " ", decl_string)

        initializer: Optional[str] = _substitute_internal_type_names(
            config, str(declaration.init).strip().rstrip(";").strip()
        )
        assert initializer is not None
        if _is_internal_initializer(config, initializer):
            initializer = None
        template_params = []
        templates = cast(
            sphinx.domains.cpp.ASTTemplateDeclarationPrefix, ast.templatePrefix
        ).templates
        assert templates is not None
        for templ_param in templates[-1].params:
            template_params.append(
                _sphinx_ast_template_parameter_to_json(
                    config, cast(sphinx.domains.cpp.ASTTemplateParam, templ_param)
                )
            )
        obj: VarEntity = {
            "kind": "var",
            "name": name,
            "template_parameters": template_params,
            "declaration": decl_string,
            "name_substitute": name_substitute,
            "initializer": initializer,
        }
        if template_args is not None:
            obj["specializes"] = True
        return obj

    except Exception as e:
        raise ValueError("Failed to parse unexposed") from e
    return None


def _parse_macro_parameters(decl: Cursor) -> typing.Optional[typing.List[str]]:
    # Check if the macro is a function-like macro
    # `cast` below is workaround for: https://github.com/tgockel/types-clang/pull/2
    token_iterator = cast(typing.Iterator[Token], decl.get_tokens())
    first_token = next(token_iterator)
    assert first_token.spelling == decl.spelling
    def_start_offset = cast(SourceLocation, first_token.extent.end).offset
    try:
        next_token = next(token_iterator)
    except StopIteration:
        return None
    if next_token.spelling != "(":
        return None
    if next_token.location.offset != def_start_offset:
        # There is a space between the macro name and the first "(", which means
        # this is not a function-like macro.
        return None

    parameters = []
    for token in token_iterator:
        if token.kind == TokenKind.COMMENT:
            continue
        spelling = token.spelling
        if spelling == ")":
            break
        if spelling == ",":
            continue
        parameters.append(spelling)
    else:
        presumed_file, presumed_line, _ = get_presumed_location(decl.location)
        raise ValueError(
            "%s:%d: Failed to parse macro %s"
            % (presumed_file, presumed_line, decl.spelling)
        )
    return parameters


def _transform_macro(config: Config, decl: Cursor) -> Optional[MacroEntity]:
    name = decl.spelling
    if config.disallow_macros_pattern.search(name) is not None:
        return None
    return {
        "kind": "macro",
        "name": name,
        "parameters": _parse_macro_parameters(decl),
    }


TRANSFORMERS: Dict[CursorKind, Callable[[Config, Cursor], Optional[CppApiEntity]]] = {
    CursorKind.TYPE_ALIAS_DECL: _transform_type_alias_decl,
    CursorKind.TYPEDEF_DECL: _transform_type_alias_decl,
    CursorKind.TYPE_ALIAS_TEMPLATE_DECL: _transform_type_alias_template_decl,
    CursorKind.STRUCT_DECL: _transform_class_decl,
    CursorKind.CLASS_DECL: _transform_class_decl,
    CursorKind.CLASS_TEMPLATE: _transform_class_template_decl,
    CursorKind.CLASS_TEMPLATE_PARTIAL_SPECIALIZATION: _transform_class_template_partial_specialization_decl,
    CursorKind.FUNCTION_DECL: _transform_function_decl,
    CursorKind.CXX_METHOD: _transform_function_decl,
    CursorKind.CONVERSION_FUNCTION: _transform_function_decl,
    CursorKind.CONSTRUCTOR: _transform_function_decl,
    CursorKind.DESTRUCTOR: _transform_function_decl,
    CursorKind.FUNCTION_TEMPLATE: _transform_function_decl,
    CursorKind.ENUM_DECL: _transform_enum_decl,
    CursorKind.VAR_DECL: _transform_var_decl,
    CursorKind.FIELD_DECL: _transform_var_decl,
    CursorKind.UNEXPOSED_DECL: _transform_unexposed_decl,
    CursorKind.MACRO_DEFINITION: _transform_macro,
}

ALLOWED_KINDS = frozenset(list(TRANSFORMERS.keys()) + [CursorKind.FRIEND_DECL])


def _parse_args(output_required: bool):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=str, required=True)
    ap.add_argument("--output", type=str, required=output_required)
    return ap.parse_args()


def _merge_decl_json(existing_json, new_json):
    if existing_json["doc"] and new_json["doc"]:
        raise ValueError("Duplicate doc strings: %r and %r" % (existing_json, new_json))
    existing_json["doc"] = existing_json["doc"] or new_json["doc"]
    template_parameters = existing_json.get("template_parameters")
    if template_parameters:
        new_template_parameters = new_json.get("template_parameters")
        for i, old_param in enumerate(template_parameters):
            new_param = new_template_parameters[i]
            if new_param.startswith(old_param):
                template_parameters[i] = new_param
            elif not old_param.startswith(new_param):
                raise ValueError(
                    "Conflicting template parameter %d: %r and %r"
                    % (i, existing_json, new_json)
                )


def _get_location_json(config: Config, location: SourceLocation) -> JsonLocation:
    filename, line, col = get_presumed_location(location)
    filename = config.map_include_path(filename)
    return {"file": filename, "line": line, "col": col}


def _get_location_string(config: Config, location: SourceLocation) -> str:
    filename, line, col = get_presumed_location(location)
    filename = config.map_include_path(filename)
    return f"{filename}:{line}:{col}"


def _is_immediately_after(decl: Cursor, prev_decl: Cursor) -> bool:
    # casts below are workaround for: https://github.com/tgockel/types-clang/pull/2
    prev_end = cast(SourceLocation, prev_decl.extent.end)
    cur_start = cast(SourceLocation, decl.extent.start)
    cur_file, cur_line, _ = get_presumed_location(cur_start)
    prev_file, prev_line, _ = get_presumed_location(prev_end)
    return cur_file == prev_file and cur_line == prev_line + 1


_NORMALIZED_KIND = {
    "constructor": "function",
    "conversion_function": "function",
    "method": "function",
    "function": "function",
    "class": "class",
    "alias": "alias",
    "enum": "enum",
    "macro": "macro",
    "var": "var",
}


def _kinds_are_compatible(a: str, b: str) -> bool:
    return _NORMALIZED_KIND[a] == _NORMALIZED_KIND[b]


class JsonApiGenerator:
    def __init__(self, extractor):
        self.extractor = extractor
        self.config = extractor.config
        self.seen_decls = {}
        self.output_json = []
        self._prev_decl = None
        self._document_with_parent = {}
        self._seen_unexposed_entities: set[tuple[str, int, str]] = set()

    def _resolve_document_with(self, entity_id: EntityId) -> EntityId:
        while True:
            document_with_parent = self._document_with_parent.get(entity_id)
            if document_with_parent is None:
                break
            entity_id = document_with_parent
        return entity_id

    def _transform_cursor_to_json(
        self,
        decl: Cursor,
        parent: Optional[Cursor],
        doc_comment_start_bound: SourceLocation,
    ):
        doc = _get_doc_comment(self.config, decl, doc_comment_start_bound)
        document_with = None
        location = _get_location_json(self.config, decl.location)
        if not doc:
            if self._prev_decl is not None and _is_immediately_after(
                decl, self._prev_decl[0]
            ):
                document_with = self._resolve_document_with(self._prev_decl[1]["id"])
            else:
                # Exclude undocumented entities
                return None
        else:
            if (
                self._prev_decl is not None
                and self._prev_decl[1]["location"] == location
            ):
                # Same line as previous declaration, presumably due to macro expansion
                # generating multiple declarations.
                #
                # Document as a sibling of the previous declaration.
                document_with = self._resolve_document_with(self._prev_decl[1]["id"])
        transformer = TRANSFORMERS.get(decl.kind)
        if transformer is None:
            return None
        json_repr = transformer(self.config, decl)
        if json_repr is None:
            return None
        if parent is None or parent.kind in (
            CursorKind.NAMESPACE,
            CursorKind.TRANSLATION_UNIT,
        ):
            json_repr["scope"] = _get_full_nested_name(parent)
        else:
            json_repr["parent"] = get_entity_id(parent)
        if decl.kind != CursorKind.UNEXPOSED_DECL:
            template_parameters = _get_template_parameters(self.config, decl)
            if json_repr.get("specializes") and template_parameters is None:
                template_parameters = []
            json_repr["template_parameters"] = template_parameters

        # Exclude duplicate UNEXPOSED_DECL entities.
        #
        # Some versions of libclang seem to also generate an UNEXPOSED_DECL for
        # instantations of variable templates. These occur at the same source
        # location as the original declaration, and are assumed to always occur
        # after the original declaration.
        if decl.kind == CursorKind.UNEXPOSED_DECL:
            duplicate_key = (
                decl.location.file.name,  # type: ignore[attr-defined]
                decl.location.offset,
                json.dumps(json_repr),
            )
            if duplicate_key in self._seen_unexposed_entities:
                return None
            self._seen_unexposed_entities.add(duplicate_key)

        entity_id = get_entity_id(decl)
        if document_with:
            prev_json = cast(Any, self._prev_decl)[1]
            if (
                prev_json is None
                or not _kinds_are_compatible(prev_json["kind"], json_repr["kind"])
                or prev_json.get("parent") != json_repr.get("parent")
                or prev_json.get("scope") != json_repr.get("scope")
            ):
                if not doc:
                    # Undocumented and can't document with previous decl
                    return None
                document_with = None
            if document_with is not None:
                doc = None
                self._document_with_parent[entity_id] = document_with
                json_repr["document_with"] = document_with
        json_repr["location"] = location
        nonitpick = get_nonitpick_directives(decl)
        if nonitpick:
            json_repr["nonitpick"] = nonitpick
        json_repr["doc"] = doc
        json_repr["id"] = entity_id
        return json_repr

    def add(self, decl: Cursor, doc_comment_start_bound: SourceLocation):
        is_friend = False
        if decl.kind == CursorKind.FRIEND_DECL:
            # Check if this is a hidden friend function.
            children = list(decl.get_children())
            if len(children) != 1:
                return
            decl = children[0]
            if not decl.kind.is_declaration():
                return
            is_friend = True
            parent = decl.lexical_parent
        else:
            parent = decl.semantic_parent
        json_repr = self._transform_cursor_to_json(
            decl, parent, doc_comment_start_bound
        )
        if json_repr is None:
            self._prev_decl = None
            return
        json_repr["friend"] = is_friend
        parent_id = json_repr.get("parent")
        if parent_id is not None and parent_id not in self.seen_decls:
            # Parent is undocumented, skip.
            return
        self._prev_decl = (decl, json_repr)
        entity_id = json_repr["id"]
        existing_json_repr = self.seen_decls.get(entity_id)
        if existing_json_repr is not None:
            _merge_decl_json(existing_json_repr, json_repr)
            return
        self.seen_decls[entity_id] = json_repr


def _parse_template_parameter(
    decl: str,
) -> Optional[sphinx.domains.cpp.ASTTemplateParam]:
    # Note: We must include an extra trailing ">" because
    # `_parse_template_parameter` fails if the parameter is not followed by "," or
    # ">".
    parser = sphinx.domains.cpp.DefinitionParser(
        decl + ">", location=("", 0), config=cast(sphinx.config.Config, SphinxConfig())
    )
    parser.allowFallbackExpressionParsing = False
    try:
        param = parser._parse_template_parameter()
        assert parser.skip_string(">")
        parser.assert_end()
        return param
    except sphinx.domains.cpp.DefinitionError:
        return None


def _extract_sfinae_replacement(template_parameter: str) -> Optional[Tuple[str, str]]:
    param = _parse_template_parameter(template_parameter)
    if param is None:
        return None

    name = str(param.get_identifier())

    if not name.lower().startswith("sfinae"):
        return None

    if isinstance(param, sphinx.domains.cpp.ASTTemplateParamType):
        default_type = param.data.default
        if default_type is None:
            return None
        return (name, str(default_type))

    if isinstance(param, sphinx.domains.cpp.ASTTemplateParamNonType):
        default_value: Optional[sphinx.domains.cpp.ASTBase] = param.param.init
        if default_value is None:
            return None
        if isinstance(default_value, sphinx.domains.cpp.ASTInitializer):
            default_value = default_value.value
        return (name, str(default_value))

    return None


CONDITIONALLY_EXPLICIT_PATTERN = re.compile(r"\(ExplicitRequires\((.+)\)\)")


def _match_template_parameter_enable_if_pattern(
    config: Config, decl: str
) -> Optional[str]:
    for pattern in config.template_parameter_enable_if_patterns:
        m = pattern.fullmatch(decl)
        if m is not None:
            return m.group(1)
    return None


def _transform_template_parameters(config: Config, template_parameters: List[Any]):
    """Transforms template parameters to C++20 form."""

    requires = []
    new_template_parameters = []
    replacements: Dict[str, str] = {}

    for template_parameter in template_parameters:
        decl = template_parameter["declaration"]
        requires_expr = _match_template_parameter_enable_if_pattern(config, decl)
        if requires_expr is not None:
            requires.append(requires_expr)
            continue
        if config.ignore_template_parameters_pattern.fullmatch(decl):
            continue
        # If the template parameter is of the form `YYY SfinaeXXX = Condition`, then
        # we want to exclude it from the template parameter list and instead return
        # the substitution `{"SfinaeXXX": "Condition"}`.  To avoid parsing in cases
        # that can't possibly match, first look to see if the name starts with
        # `"sfinae"`.
        if re.match(r"sfinae", template_parameter["name"], re.IGNORECASE) is not None:
            # Possibly match, parse to verify.
            replacement = _extract_sfinae_replacement(decl)
            if replacement is not None:
                replacements[replacement[0]] = replacement[1]
                continue
        new_template_parameters.append(template_parameter)

    return (
        new_template_parameters,
        requires,
        replacements,
    )


def _strip_return_type(
    declaration: str, template_prefix: str, location: Tuple[str, int]
) -> str:
    parser = sphinx.domains.cpp.DefinitionParser(
        template_prefix + declaration,
        location=location,
        config=cast(sphinx.config.Config, SphinxConfig()),
    )
    ast = parser.parse_declaration("function", "function")
    parser.skip_ws()
    parser.assert_end()
    assert isinstance(ast.declaration, sphinx.domains.cpp.ASTType)
    ast.declaration.declSpecs.trailingTypeSpec = (
        sphinx.domains.cpp.ASTTrailingTypeSpecFundamental(["auto"], ["auto"])
    )
    return str(ast.declaration)


_OPERATOR_PAGE_NAMES = {
    ("operator+", 1): "operator-unary_plus",
    ("operator-", 1): "operator-negate",
    ("operator*", 1): "operator-dereference",
    ("operator~", 1): "operator-complement",
    ("operator!", 1): "operator-logical_not",
    ("operator++", 1): "operator-pre_inc",
    ("operator++", 2): "operator-post_inc",
    ("operator--", 1): "operator-pre_dec",
    ("operator--", 2): "operator-post_dec",
    ("operator<<", 2): "operator-shift_left",
    ("operator>>", 2): "operator-shift_right",
    ("operator+", 2): "operator-plus",
    ("operator-", 2): "operator-minus",
    ("operator*", 2): "operator-multiplies",
    ("operator/", 2): "operator-divides",
    ("operator%", 2): "operator-modulus",
    ("operator<", 2): "operator-less",
    ("operator<=", 2): "operator-less_equal",
    ("operator>=", 2): "operator-greater_equal",
    ("operator==", 2): "operator-equal_to",
    ("operator!=", 2): "operator-not_equal_to",
    ("operator=", 2): "operator-assign",
    ("operator<<=", 2): "operator-shift_left_assign",
    ("operator>>=", 2): "operator-shift_right_assign",
    ("operator*=", 2): "operator-multiplies_assign",
    ("operator/=", 2): "operator-divides_assign",
    ("operator%=", 2): "operator-modulus_assign",
    ("operator+=", 2): "operator-plus_assign",
    ("operator-=", 2): "operator-minus_assign",
    ("operator&=", 2): "operator-bitwise_and_assign",
    ("operator|=", 2): "operator-bitwise_or_assign",
    ("operator^=", 2): "operator-bitwise_xor_assign",
    ("operator&&", 2): "operator-logical_and",
    ("operator||", 2): "operator-logical_or",
    ("operator|", 2): "operator-bitwise_or",
    ("operator&", 2): "operator-bitwise_and",
    ("operator^", 2): "operator-bitwise_xor",
    ("operator,", 2): "operator-comma",
    ("operator->", 1): "operator-arrow",
    ("operator&", 1): "operator-address_of",
    "operator()": "operator-call",
    "operator[]": "operator-subscript",
}

DEFAULT_MEMBER_GROUP_FOR_MEMBER_ENTITY_TYPE = {
    "constructor": "Constructors",
    "destructor": "Constructors",
    "class": "Types",
    "method": "Methods",
    "enum": "Types",
    "alias": "Types",
    "conversion_function": "Conversion operators",
    "var": "Data members",
    "function": "Friend functions",
}

DEFAULT_MEMBER_GROUP_FOR_NON_MEMBER_ENTITY_TYPE = {
    "alias": "Related Types",
    "enum": "Related Types",
    "class": "Related Types",
    "function": "Related Functions",
    "var": "Related Constants",
    "macro": "Related Macros",
}


def _get_default_member_group(entity: CppApiEntity) -> str:
    if entity.get("parent"):
        return DEFAULT_MEMBER_GROUP_FOR_MEMBER_ENTITY_TYPE[entity["kind"]]
    return DEFAULT_MEMBER_GROUP_FOR_NON_MEMBER_ENTITY_TYPE[entity["kind"]]


def _normalize_doc_text(text: str) -> str:
    text = re.sub(r"^((?:\\|@)(?:brief|details)\s+)", "", text, flags=re.MULTILINE)
    text = re.sub(
        r"^(?:\\|@)(t?param)(\[(?:in|out|in,\sout)\])?\s+([a-zA-Z_][^ ]*)",
        ":\\1 \\3\\2:",
        text,
        flags=re.MULTILINE,
    )
    text = re.sub(
        r"^(?:\\|@)(error)\s+`([^`]+)`", ":\\1 \\2:", text, flags=re.MULTILINE
    )
    text = re.sub(
        r"^(?:\\|@)(returns?|pre|post|[ds]?checks|invariant|requires)(?: |\n )",
        ":\\1: ",
        text,
        flags=re.MULTILINE,
    )
    text = re.sub(r"^(?:\\|@)(retval)\s+(\S+)", ":\\1 \\2:", text, flags=re.MULTILINE)
    text = SPECIAL_GROUP_COMMAND_PATTERN.sub("", text)
    return text


FUNCTION_ENTITY_KINDS = frozenset(
    ["function", "method", "constructor", "destructor", "conversion_function"]
)


def _is_function(entity: CppApiEntity) -> bool:
    return entity["kind"] in FUNCTION_ENTITY_KINDS


def _get_path_component_from_special_id(special_id: str) -> str:
    special_id = re.sub("[^a-zA-Z0-9_]+", "-", special_id)
    return special_id.strip("-")


def _apply_identifier_replacements(
    requires_term: str, replacements: Dict[str, str]
) -> str:
    for orig_identifier, replacement in replacements.items():
        requires_term = re.sub(
            r"\b" + re.escape(orig_identifier) + r"\b", replacement, requires_term
        )
    return requires_term


def _make_explicit_conditional(decl: str, explicit: str) -> str:
    new_str = re.sub(r"\bexplicit\b", f"explicit({explicit})", decl, 1)
    if new_str == decl:
        raise ValueError(
            "Failed to insert explicit condition %r into: %s"
            % (
                explicit,
                decl,
            )
        )
    return new_str


def _is_uniform_binary_expr(
    expr: sphinx.domains.cpp.ASTBase, allowed_ops: Tuple[str, ...]
) -> bool:
    if not isinstance(expr, sphinx.domains.cpp.ASTBinOpExpr):
        return False
    return all(op in allowed_ops for op in expr.ops)


def _is_logical_and_expr(expr: sphinx.domains.cpp.ASTBase) -> bool:
    return _is_uniform_binary_expr(expr, ("&&", "and"))


def _is_primary_expr(expr: sphinx.domains.cpp.ASTBase) -> bool:
    return isinstance(
        expr,
        (
            sphinx.domains.cpp.ASTLiteral,
            sphinx.domains.cpp.ASTIdExpression,
            sphinx.domains.cpp.ASTThisLiteral,
        ),
    )


def _normalize_requires_terms(terms: List[str]) -> List[str]:
    if not terms:
        return terms
    expr = " && ".join(f"({term})" for term in terms)
    parser = sphinx.domains.cpp.DefinitionParser(
        "requires " + expr,
        location=("", 0),
        config=cast(sphinx.config.Config, SphinxConfig()),
    )
    # If we allow fallback parsing, we end up with incorrect parsing and a
    # spurious warning.
    parser.allowFallbackExpressionParsing = False
    ast = parser._parse_requires_clause()
    parser.skip_ws()
    parser.assert_end()

    assert ast is not None

    new_terms = []

    def process(
        expr: Union[sphinx.domains.cpp.ASTType, sphinx.domains.cpp.ASTExpression],
    ):
        while True:
            if isinstance(expr, sphinx.domains.cpp.ASTParenExpr):
                expr = expr.expr
                continue
            if isinstance(expr, sphinx.domains.cpp.ASTBinOpExpr) and not expr.ops:
                expr = expr.exprs[0]
                continue
            if (
                isinstance(expr, sphinx.domains.cpp.ASTPostfixExpr)
                and not expr.postFixes
            ):
                expr = expr.prefix
                continue
            break
        if _is_logical_and_expr(expr):
            for sub_expr in cast(sphinx.domains.cpp.ASTBinOpExpr, expr).exprs:
                process(sub_expr)
            return
        if _is_primary_expr(expr):
            new_terms.append(str(expr))
            return
        new_terms.append(f"({expr})")

    process(ast.expr)

    return new_terms


def _format_template_arguments(entity: CppApiEntity) -> str:
    if entity.get("specializes"):
        # Template arguments already included in `entity["name"]`.
        return ""
    template_parameters = entity.get("template_parameters")
    if not template_parameters:
        return ""
    strs = []
    for param in template_parameters:
        arg = param["name"]
        if not arg:
            continue
        if param["pack"]:
            arg += "..."
        strs.append(arg)
    args_str = ", ".join(strs)
    return f"<{args_str}>"


def _get_entity_base_page_name_component(entity: CppApiEntity) -> str:
    base_name = entity["name"]
    if (entity["kind"] == "class" or entity["kind"] == "var") and entity.get(
        "specializes"
    ):
        # Strip any template arguments
        base_name = re.sub("([^<]*).*", r"\1", base_name)
    elif entity["kind"] == "conversion_function":
        base_name = "operator-cast"
    elif entity["kind"] in ("function", "method") and re.match(
        r"operator\b", base_name
    ):
        arity = cast(FunctionEntity, entity)["arity"]
        if entity["kind"] == "method":
            arity += 1
        op_page_name = _OPERATOR_PAGE_NAMES.get((base_name, arity))
        if op_page_name is None:
            op_page_name = _OPERATOR_PAGE_NAMES[base_name]
        base_name = op_page_name

    return base_name


def _get_entity_page_name_component(entity: CppApiEntity) -> str:
    page_name = _get_entity_base_page_name_component(entity)
    special_id = entity.get("special_id")
    if special_id is not None:
        page_name += f"-{_get_path_component_from_special_id(special_id)}"
    return page_name


def _ensure_unique_page_names(
    entities_with_page_names: List[EntityId],
    entities: Dict[EntityId, CppApiEntity],
    warning,
) -> None:
    names: Dict[
        Tuple[Optional[str], Optional[str], str, Optional[str]], List[EntityId]
    ] = {}

    for entity_id in entities_with_page_names:
        entity = entities[entity_id]
        parent_id = entity.get("parent")
        special_id = entity.get("special_id")
        scope = entity.get("scope")
        base_name = _get_entity_base_page_name_component(entity)
        key = (parent_id, scope, base_name, special_id)
        names.setdefault(key, []).append(entity_id)

    for (parent_id, scope, base_name, special_id), entity_ids in names.items():
        if len(entity_ids) == 1:
            continue
        page_entities = [entities[entity_id] for entity_id in entity_ids]
        warning(
            "Disambiguating %d overloads of %s using numerical ids.  Definitions at %s",
            len(entity_ids),
            base_name,
            ", ".join(
                "%s:%d" % (entity["location"]["file"], entity["location"]["line"])
                for entity in page_entities
            ),
        )

        for i, entity in enumerate(page_entities):
            entity["special_id"] = str(i + 1)


class JsonDiagnostic(TypedDict):
    message: str
    location: Optional[JsonLocation]


class JsonNitpickExclusion(TypedDict):
    file: str
    line: int
    target: str


class JsonApiData(TypedDict):
    errors: List[JsonDiagnostic]
    warnings: List[JsonDiagnostic]
    nonitpick: List[JsonNitpickExclusion]
    groups: Dict[str, List[EntityId]]
    entities: Dict[str, CppApiEntity]


def organize_entities(
    config: Config, entities: Dict[EntityId, CppApiEntity]
) -> JsonApiData:
    errors: List[JsonDiagnostic] = []
    warnings: List[JsonDiagnostic] = []

    def error(msg: str, *args, location: Optional[JsonLocation] = None):
        errors.append({"message": msg % args, "location": location})

    def warning(msg: str, *args, location: Optional[JsonLocation] = None):
        warnings.append({"message": msg % args, "location": location})

    def _handle_document_with(entity: CppApiEntity) -> bool:
        document_with = entity.get("document_with")
        if document_with is None:
            return False
        sibling_entity: Optional[CppApiEntity] = entities.get(document_with)
        if sibling_entity is None:
            return False
        sibling_entity.setdefault("siblings", []).append(entity["id"])
        return True

    def _normalize_entity_requires(entity: CppApiEntity):
        template_parameters = entity.get("template_parameters")
        if template_parameters:
            (
                template_parameters,
                requires,
                replacements,
            ) = _transform_template_parameters(config, template_parameters)
            if entity.get("specializes") is None and not template_parameters:
                entity["template_parameters"] = None
            else:
                entity["template_parameters"] = template_parameters
        else:
            requires = []
            replacements = None
            explicit = None

        existing_requires = entity.get("requires")
        if existing_requires:
            requires = existing_requires + requires

        if _is_function(entity):
            func_entity = cast(FunctionEntity, entity)
            declaration = func_entity["declaration"]
            if replacements:
                declaration = _apply_identifier_replacements(declaration, replacements)
            if (
                func_entity["kind"] != "constructor"
                and config.hide_types_pattern.search(
                    declaration[: declaration.index(func_entity["name_substitute"])]
                )
                is not None
            ):
                declaration = _strip_return_type(
                    declaration,
                    "template <> " if template_parameters is not None else "",
                    location=(entity["location"]["file"], entity["location"]["line"]),
                )
            func_entity["declaration"] = declaration
        else:
            if replacements:
                for key in cast(
                    Tuple[Literal["declaration", "underlying_type"], ...],
                    ("declaration", "underlying_type"),
                ):
                    x = cast(Optional[str], entity.get(key, None))
                    if x is not None:
                        entity[key] = _apply_identifier_replacements(x, replacements)  # type: ignore[typeddict-item]

        if replacements:
            requires = [
                _apply_identifier_replacements(x, replacements) for x in requires
            ]

        requires = _normalize_requires_terms(requires)
        new_requires = []
        explicit = None
        for term in requires:
            m = CONDITIONALLY_EXPLICIT_PATTERN.fullmatch(term)
            if m is not None:
                if explicit is not None:
                    raise ValueError(
                        "cannot have more than one conditionally-explicit term"
                    )
                explicit = m.group(1)
            else:
                new_requires.append(term)
        requires = new_requires

        if explicit:
            if entity["kind"] != "constructor":
                raise ValueError(
                    "conditionally-explicit terms only valid on constructors"
                )
            entity["declaration"] = _make_explicit_conditional(
                entity["declaration"], explicit
            )

        requires = [x for x in requires if config.hide_types_pattern.search(x) is None]
        entity["requires"] = requires

    def get_entity_page_name(entity: CppApiEntity) -> str:
        components = []
        cur_entity = entity
        while True:
            components.append(_get_entity_page_name_component(cur_entity))
            parent_id = cur_entity.get("parent")
            if parent_id is None:
                break
            parent_entity = entities.get(parent_id)
            assert parent_entity is not None
            cur_entity = parent_entity
        components.reverse()
        page_name = (cur_entity["scope"] + "::".join(components)).replace("::", ".")
        return page_name

    def _parse_entity_doc(entity: CppApiEntity):
        doc = entity["doc"]
        if doc is None:
            if _handle_document_with(entity):
                return True
            return False
        doc_text = doc["text"]
        for m in SPECIAL_GROUP_COMMAND_PATTERN.finditer(doc_text):
            entity[cast(Literal["special_id"], "special_" + m.group(1))] = m.group(  # noqa: F821
                2
            ).strip()
        return True

    def get_entity_scope(entity: CppApiEntity) -> str:
        components = []
        cur_entity = entity
        while True:
            parent_id = cur_entity.get("parent")
            if parent_id is None:
                break
            parent_entity = entities.get(parent_id)
            assert parent_entity is not None
            cur_entity = parent_entity
            name_with_args = cur_entity["name"]
            if not cur_entity.get("specializes"):
                name_with_args += _format_template_arguments(cur_entity)
            components.append(name_with_args)
        components.reverse()
        if components:
            components.append("")
        return cur_entity.get("scope", "") + "::".join(components)

    def get_entity_object_name(entity: CppApiEntity) -> str:
        name = get_entity_scope(entity) + entity["name"]
        special_id = entity.get("special_id")
        if special_id:
            name += f"[{special_id}]"
        return name

    unspecialized_names: Dict[
        Tuple[Optional[EntityId], Optional[str], str], EntityId
    ] = {}

    names: Dict[str, EntityId] = {}

    def resolve_entity_name(
        scope: str, relative_entity_name: str
    ) -> Optional[EntityId]:
        if relative_entity_name.startswith("::"):
            resolved = relative_entity_name[2:]
            entity_id = names.get(resolved)
            if entity_id is None:
                return None
            return entity_id
        truncate_idx = len(scope)
        while True:
            full_name = scope[:truncate_idx] + relative_entity_name
            entity_id = names.get(full_name)
            if entity_id is not None:
                return entity_id
            if truncate_idx == 0:
                return None
            truncate_idx = scope.rfind("::", 0, truncate_idx - 2)
            if truncate_idx == -1:
                truncate_idx = 0
            else:
                truncate_idx = truncate_idx + 2

    must_resolve_specializes: List[CppApiEntity] = []

    all_nonitpick: List[JsonNitpickExclusion] = []

    def _handle_nitpick(entity: CppApiEntity, targets: List[str]) -> None:
        document_with = entity.get("document_with")
        if document_with:
            entity = entities[document_with]
        location: JsonLocation = entity["location"]
        filename: str = location["file"]
        line: int = location["line"]
        for target in targets:
            all_nonitpick.append({"file": filename, "line": line, "target": target})

    entities_with_page_names: List[EntityId] = []

    for entity in entities.values():
        specializes = entity.get("specializes")
        if (
            entity["kind"] == "var"
            and entity.get("template_parameters") is not None
            and specializes is None
        ):
            key = (entity.get("parent"), entity.get("scope"), entity["name"])
            entity_id = entity["id"]
            if unspecialized_names.setdefault(key, entity_id) != entity_id:
                other_entity_id = unspecialized_names[key]
                other_entity = entities[other_entity_id]
                raise ValueError(
                    "Duplicate unspecialized entity name: %r %r %r"
                    % (
                        key,
                        entity,
                        other_entity,
                    )
                )
        if specializes is True:
            must_resolve_specializes.append(entity)
        if not _parse_entity_doc(entity):
            continue
        _normalize_entity_requires(entity)
        nonitpick = entity.get("nonitpick")
        if nonitpick:
            _handle_nitpick(entity, nonitpick)
        if not entity["doc"]:
            continue
        entities_with_page_names.append(entity["id"])

    for entity in must_resolve_specializes:
        name = cast(str, entity["name"])
        name = name[: name.index("<")]
        unspecialized_key = (entity.get("parent"), entity.get("scope"), name)
        unspecialized_id = unspecialized_names.get(unspecialized_key)
        if unspecialized_id is not None:
            entity["specializes"] = unspecialized_id

    _ensure_unique_page_names(entities_with_page_names, entities, warning)
    for entity_id in entities_with_page_names:
        entity = entities[entity_id]
        names[get_entity_object_name(entity)] = entity_id
        entity["page_name"] = get_entity_page_name(entity)
        doc = entity["doc"]
        assert doc is not None
        doc["text"] = _normalize_doc_text(doc["text"])

    groups: Dict[str, List[EntityId]] = {}

    for entity in entities.values():
        entity_id = entity["id"]
        doc = entity["doc"]
        if doc is None:
            continue
        ingroup = entity.get("special_ingroup")
        relates_name = entity.get("special_relates")
        member_group = entity.get("special_membergroup")

        if (ingroup is not None) and (relates_name is not None):
            error(
                "Cannot specify both \\ingroup and \\relates for %r",
                entity,
                location=doc["location"],
            )
            continue

        if ingroup is not None:
            ingroup = docutils.nodes.make_id(ingroup)
            groups.setdefault(ingroup, []).append(entity_id)
            if member_group is not None:
                error(
                    "Cannot specify both \\ingroup and \\membergroup for %r",
                    entity,
                    location=doc["location"],
                )
            continue

        parent_id = entity.get("parent")
        if relates_name is not None:
            scope = get_entity_scope(entity)
            relates_id = resolve_entity_name(scope, relates_name)
            if relates_id is None:
                error(
                    "Cannot resolve entity reference %r from scope %r",
                    relates_name,
                    scope,
                    location=doc["location"],
                )
                continue
            parent_id = None
        else:
            if parent_id is None:
                warning(
                    "No group or relates specified for entity %s%s",
                    entity.get("scope"),
                    entity["name"],
                    location=doc["location"],
                )
                continue
            relates_id = parent_id

        if member_group is None:
            member_group = _get_default_member_group(entity)
        assert relates_id is not None
        entities[relates_id].setdefault(
            cast(
                Literal["related_members", "related_nonmembers"],
                "related_members" if parent_id is not None else "related_nonmembers",
            ),
            cast(Dict[str, List[EntityId]], {}),
        ).setdefault(member_group, []).append(entity_id)

    return {
        "entities": entities,
        "groups": groups,
        "errors": errors,
        "warnings": warnings,
        "nonitpick": all_nonitpick,
    }


def _get_output_json(extractor: Extractor) -> JsonApiData:
    generator = JsonApiGenerator(extractor)
    if extractor.config.verbose:
        logger.info("Found %d C++ declarations", len(extractor.decls))
    for decl, doc_comment_start_bound in extractor.decls:
        generator.add(decl, doc_comment_start_bound)
    return organize_entities(extractor.config, generator.seen_decls)


def generate_output(config: Config) -> JsonApiData:
    extractor = Extractor(config)
    return _get_output_json(extractor)


def _load_config(config_path: str) -> Config:
    config_content = pathlib.Path(config_path).read_text(encoding="utf-8")
    context: dict = {}
    exec(config_content, context)

    config = context["config"]
    assert isinstance(config, Config)
    return config


def main():
    args = _parse_args(output_required=True)
    config = _load_config(args.config)
    output_json = generate_output(config)

    if args.output is not None:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output_json, f)


if __name__ == "__main__":
    main()
