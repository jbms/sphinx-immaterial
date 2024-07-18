"""Utilities for use with Sphinx."""

import contextlib
import io
from typing import Optional, Union, List, Tuple, Mapping, Sequence, Literal

import docutils.nodes
import docutils.parsers.rst.roles
import docutils.parsers.rst.states
import docutils.statemachine
import sphinx.addnodes
import sphinx.util.docutils


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
    signatures: Optional[Sequence[str]] = None,
    content: Optional[str] = None,
    options: Optional[Mapping[str, Union[None, str, bool]]] = None,
) -> str:
    """Formats a RST directive into RST syntax.

    :param name: Directive name, e.g. "json:schema".
    :param args: List of directive arguments.
    :param signatures: List of signatures, alternative to ``args``.
    :param content: Directive body content.
    :param options: Directive options.

    :returns: The formatted directive.
    """
    out = io.StringIO()
    out.write("\n\n")
    assert not args or not signatures
    if not signatures:
        signatures = ["".join(f" {arg}" for arg in args)]
    prefix = f".. {name}:: "
    for i, signature in enumerate(signatures):
        if i == 1:
            prefix = " " * len(prefix)
        out.write(prefix + signature + "\n")
    if options:
        for key, value in options.items():
            if value is False or value is None:
                continue
            if value is True:
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
    signatures: Optional[Sequence[str]] = None,
    content: Union[str, docutils.statemachine.StringList, None] = None,
    options: Optional[Mapping[str, Union[None, str, bool]]] = None,
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
    prefix = f"{base_indent_str}.. {name}:: "
    assert not args or not signatures
    if not signatures:
        signatures = ["".join(f" {arg}" for arg in args)]
    for i, signature in enumerate(signatures):
        if i == 1:
            prefix = " " * len(prefix)
        out.append(prefix + signature, source_path, source_line)
    content_indent_str = base_indent_str + "   "
    if options:
        for key, value in options.items():
            if value is False or value is None:
                continue
            if value is True:
                value = ""
            out.append(f"{content_indent_str}:{key}: {value}", source_path, source_line)
    if content is not None:
        out.append(base_indent_str, source_path, source_line)
        if isinstance(content, str):
            append_multiline_string_to_stringlist(
                out, content, source_path, source_line, prefix=content_indent_str
            )
        else:
            for source, offset, line in content.xitems():
                out.append(content_indent_str + line, source, offset)
    # Blank line at end to denote end of directive.
    out.append(base_indent_str, source_path, source_line)


def append_multiline_string_to_stringlist(
    out: docutils.statemachine.StringList,
    text: str,
    source_path: str,
    source_line: int,
    prefix: str = "",
) -> None:
    for i, line in enumerate(text.splitlines()):
        out.append(prefix + line, source_path, source_line + i)


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
        for p in node.findall(condition=docutils.nodes.paragraph):
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


def make_toctree_node(
    state: docutils.parsers.rst.states.RSTState,
    toc_entries: List[Tuple[str, str]],
    options: dict,
    source_path: str,
    source_line: int = 0,
) -> List[docutils.nodes.Node]:
    if not toc_entries:
        return []

    # The Sphinx `toctree` directive parser cannot handle page names that
    # include angle brackets.  Therefore, we use the directive to create an
    # empty toctree node and then add the entries directly.
    toctree_nodes = parse_rst(
        state=state,
        text=format_directive("toctree", options=options),
        source_path=source_path,
        source_line=source_line,
    )
    toctree: Optional[sphinx.addnodes.toctree] = None
    for node in toctree_nodes[-1].findall(condition=sphinx.addnodes.toctree):
        toctree = node
        break
    if toctree is None:
        raise ValueError("No toctree node found")
    toctree["entries"].extend(toc_entries)
    toctree["includefiles"].extend([path for _, path in toc_entries])
    return toctree_nodes


def remove_css_file(app: sphinx.application.Sphinx, filename: str):
    """Removes a CSS file added by another extension."""
    app_css_files = app.registry.css_files
    app_indices = [i for i, x in enumerate(app_css_files) if x[0] == filename]
    for i in reversed(app_indices):
        del app_css_files[i]

    if hasattr(app, "builder") and hasattr(app.builder, "add_css_file"):
        builder_css_files = app.builder.css_files  # type: ignore[attr-defined]
        builder_indices = [
            i for i, x in enumerate(builder_css_files) if x.filename == filename
        ]
        for i in reversed(builder_indices):
            del builder_css_files[i]


@contextlib.contextmanager
def save_default_role(env: sphinx.environment.BuildEnvironment):
    orig_role_fn = docutils.parsers.rst.roles._roles.get("")  # type: ignore[attr-defined]
    orig_role_name = env.temp_data["default_role"]

    try:
        yield
    finally:
        if orig_role_fn is not None:
            docutils.parsers.rst.roles._roles[""] = orig_role_fn  # type: ignore[attr-defined]
        else:
            docutils.parsers.rst.roles._roles.pop("", None)  # type: ignore[attr-defined]
        env.temp_data["default_role"] = orig_role_name
