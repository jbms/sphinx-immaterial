"""Utilities for use with Sphinx."""

import io
from typing import Optional, Dict, Union, List

import docutils.nodes
import docutils.parsers.rst.states
import docutils.statemachine
import sphinx.util.docutils
from typing_extensions import Literal


def to_statemachine_stringlist(
    content: str, source_path: str, source_line: int = 0
) -> docutils.statemachine.StringList:
    """Converts to a docutils StringList with associated source info.

    All lines of `content` are assigned the same source info.

    :param content: Source text.
    :param source_path: Path to the source file, for error messages.
    :param source_line: Line number in source file, for error messages.

    :returns: The string list, which may be passed to `nested_parse`.
    """
    list_lines = docutils.statemachine.string2lines(content)
    items = [(source_path, source_line)] * len(list_lines)
    return docutils.statemachine.StringList(list_lines, items=items)


def format_directive(
    name: str,
    *args: str,
    content: Optional[str] = None,
    options: Optional[Dict[str, Union[None, str, bool]]] = None,
) -> str:
    """Formats a RST directive into RST syntax.

    :param name: Directive name, e.g. "json:schema".
    :param args: List of directive arguments.
    :param content: Directive body content.
    :param options: Directive options.

    :returns: The formatted directive.
    """
    out = io.StringIO()
    out.write("\n\n")
    out.write(f".. {name}::")
    for arg in args:
        out.write(f" {arg}")
    out.write("\n")
    if options:
        for key, value in options.items():
            if value is False or value is None:  # pylint: disable=g-bool-id-comparison
                continue
            if value is True:  # pylint: disable=g-bool-id-comparison
                value = ""
            out.write(f"   :{key}: {value}\n")
    if content:
        out.write("\n")
        for line in content.splitlines():
            out.write(f"   {line}\n")
    out.write("\n")
    return out.getvalue()


def append_directive_to_stringlist(
    out: docutils.statemachine.StringList,
    name: str,
    *args: str,
    source_path: str,
    source_line: int,
    indent: int = 0,
    content: Union[str, docutils.statemachine.StringList, None] = None,
    options: Optional[Dict[str, Union[None, str, bool]]] = None,
) -> None:
    """Formats a RST directive into RST syntax and appends to a StringList.

    :param out: StringList to which directive should be appended.
    :param name: Directive name, e.g. "json:schema".
    :param args: List of directive arguments.
    :param source_path: Source path to associate with the first line of the directive
        (and content if specified as a string).
    :param source_line: Source line to associate with the first line of the directive
        (and content if specified as a string).
    :param indent: Base amount to indent every line.
    :param content: Directive body content.
    :param options: Directive options.
    """
    base_indent_str = " " * indent
    # Blank line at beginning to start new directive.
    out.append(base_indent_str, source_path, source_line)
    out.append(
        f"{base_indent_str}.. {name}::" + "".join(f" {arg}" for arg in args),
        source_path,
        source_line,
    )
    content_indent_str = base_indent_str + "   "
    if options:
        for key, value in options.items():
            if value is False or value is None:  # pylint: disable=g-bool-id-comparison
                continue
            if value is True:  # pylint: disable=g-bool-id-comparison
                value = ""
            out.append(f"{content_indent_str}:{key}: {value}", source_path, source_line)
    if isinstance(content, str):
        out.append(base_indent_str, source_path, source_line)
        for line in content.splitlines():
            out.append(content_indent_str + line, source_path, source_line)
    elif content is not None:
        for source, offset, line in content.xitems():
            out.append(content_indent_str + line, source, offset)
    # Blank line at end to denote end of directive.
    out.append(base_indent_str, source_path, source_line)


def parse_rst(
    state: docutils.parsers.rst.states.RSTState,
    text: Union[str, docutils.statemachine.StringList],
    source_path: str = "",
    source_line: int = 0,
) -> List[docutils.nodes.Node]:
    content = (
        to_statemachine_stringlist(text, source_path, source_line)
        if isinstance(text, str)
        else text
    )
    with sphinx.util.docutils.switch_source_input(state, content):
        node = docutils.nodes.container()
        # necessary so that the child nodes get the right source/line set
        node.document = state.document
        state.nested_parse(content, 0, node)
    return node.children


def summarize_element_text(
    node: docutils.nodes.Element,
    mode: Literal["first_paragraph", "first_sentence"] = "first_paragraph",
) -> str:
    """Extracts a short text synopsis, e.g. for use as a tooltip."""

    # Recurisvely extract first paragraph
    while True:
        for p in node.traverse(condition=docutils.nodes.paragraph):
            if p is node:
                continue
            node = p
            break
        else:
            break

    text = node.astext()
    if mode == "first_sentence":
        sentence_end = text.find(". ")
        if sentence_end != -1:
            text = text[: sentence_end + 1]
    text = text.replace("\n", " ")
    return text.strip()
