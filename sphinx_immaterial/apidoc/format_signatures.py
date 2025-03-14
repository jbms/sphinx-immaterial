"""Sphinx extension that formats signatures using an external tool.

Currently black and clang-format are supported.
"""

import collections
import difflib
import hashlib
import io
import json
import re
import subprocess
from typing import (
    Any,
    Callable,
    Dict,
    List,
    NamedTuple,
    Optional,
    Tuple,
    Type,
    Union,
    cast,
)

import docutils.nodes
import pydantic.dataclasses
import sphinx.addnodes
import sphinx.application
import sphinx.environment
import sphinx.ext.viewcode
import sphinx.transforms
import sphinx.util.logging

from . import object_description_options

logger = sphinx.util.logging.getLogger(__name__)

_SIGNATURE_FORMAT_ID = "signature_format_id"

_FORMATTED_SIGNATURES = "sphinx_immaterial_formatted_signatures"


def _get_collected_signatures(
    env: sphinx.environment.BuildEnvironment,
) -> Dict[Tuple[str, str], Dict[str, str]]:
    attr = "_sphinx_immaterial_collected_signatures_to_format"
    x = getattr(env, attr, None)
    if x is None:
        x = collections.defaultdict(dict)
        setattr(env, attr, x)
    return x


class SignatureText(docutils.nodes.Text):
    pass


def _html_visit_signature_text(self, node: SignatureText) -> None:
    encoded = self.encode(node.astext()).replace(" ", "&nbsp;").replace("\n", "<br>")
    self.body.append(encoded)


def _html_depart_signature_text(self, node: SignatureText) -> None:
    pass


def _latex_visit_signature_text(self, node: SignatureText) -> None:
    self.literal_whitespace += 1
    self.body.append(self.encode(node.astext()))
    self.literal_whitespace -= 1


def _latex_depart_signature_text(self, node: SignatureText) -> None:
    pass


class CollectSignaturesTransform(sphinx.transforms.SphinxTransform):
    """Collects signatures to be formatted.

    For clang-format, this merely collects the signatures into the environment.
    For efficiency, all of the collected signatures are formatted with a single
    call to clang-format to avoid the overhead of starting the clang-format
    process separately for each signature.

    For black, this formats the signature immediately.

    """

    # Late
    default_priority = 900

    def apply(self, **kwargs: Any) -> None:
        collected_signatures = _get_collected_signatures(self.env)
        for node in self.document.findall(sphinx.addnodes.desc_signature):
            parent = node.parent
            domain: str = parent.get("domain")
            objtype: str = parent.get("objtype")
            options = object_description_options.get_object_description_options(
                self.env, domain, objtype
            )
            if options.get("black_format_style") is not None:
                _format_signature_with_black(domain, objtype, node, options)
                continue

            if options.get("clang_format_style") is None:
                continue
            if "api-include-path" in node["classes"]:
                continue
            parts = []
            for child in node.children:
                parts.append(child.astext())
            signature = " ".join(parts)
            sig_id = hashlib.md5(
                (f"{domain}:{objtype}:" + signature).encode("utf-8")
            ).hexdigest()
            node[_SIGNATURE_FORMAT_ID] = sig_id
            collected_signatures[domain, objtype][sig_id] = signature


def _transform_node_list(
    source: list[docutils.nodes.Node],
    transform,
    *args,
) -> list[docutils.nodes.Node]:
    transformed = []
    for node in source:
        t = transform(*args, node)
        transformed.extend(t)
    return transformed


def _replace_text_nodes(
    nodes: list[docutils.nodes.Node],
    ignored: set[int],
    replacements: dict[int, list[docutils.nodes.Node]],
) -> list[docutils.nodes.Node]:
    """Replaces each text node descendant in `nodes` with the specified replacements.

    Args:
      nodes: List of nodes.
      replacements: Maps `id(text_node)` to the list of replacements.

    Returns:
      Deep copy of `nodes` with the replacements applied.
    """

    def _transform_node(node):
        if id(node) in ignored:
            return [node.deepcopy()]
        if isinstance(node, docutils.nodes.Text):
            return replacements.get(id(node)) or []
        new_node = node.copy()
        # Ensure the new node does not contain any children. `desc_sig_space`,
        # for example, adds a default child text node with content " ".
        del new_node[:]

        new_children = _transform_node_list(node.children, _transform_node)

        if isinstance(new_node, sphinx.addnodes.pending_xref):
            num_new_children = len(new_children)
            assert num_new_children != 0
            # A pending_xref with no children is an error and indicates a
            # problem with applying the format.

            if num_new_children != 1:
                # Wrap children in an `inline` node because Sphinx expects
                # pending_xref nodes to only have one child.
                wrapper = docutils.nodes.inline()
                wrapper.extend(new_children)
                new_children = [wrapper]

        new_node.extend(new_children)

        if len(new_node.children) == 0:
            # Exclude nodes with no content (presumably the content got moved to
            # a different node).
            return []

        return [new_node]

    return _transform_node_list(nodes, _transform_node)


class FormatInputComponent(NamedTuple):
    orig_text: str
    """Original text in the signature.

    Equal to `node.astext()` if `node` is not `None`.
    """

    input_text: str
    """Input text for the formatter.

    Must have the same length as `orig_text`. In most cases this is equal to
    `orig_text`, but in some cases may be modified in order to make the input
    syntactically valid for the formatter.
    """

    node: Optional[docutils.nodes.Text]
    """Corresponding text node.

    May be `None` if this component was added only to make the syntax valid for
    the formatter and should not be preserved.
    """

    not_preferred_for_inserts: bool
    """Try not to add text to this component.

    Set on pending_xref nodes to indicate that inserts should be associated with
    the next node if possible.
    """


_INDENTED_LINE_PATTERN = re.compile(r".*(?:^|\n)([ \t]+)$", re.DOTALL)


_ASCII_UPPERCASE_PATTERN = re.compile("[A-Z]+")
_ALPHANUMERIC_PATTERN = re.compile(r"\w+", re.UNICODE)


def _normalize_ascii_letters(x: str) -> str:
    """Convert all ASCII letters to lowercase.

    This ensures that any numeric literal normalization (e.g. hex A-F or "E" in
    exponents) is supported.
    """
    return _ASCII_UPPERCASE_PATTERN.sub(lambda m: m.group().lower(), x)


def _align_generic(
    a_offset: int,
    a: str,
    b_offset: int,
    b: str,
    ops: list[tuple[str, int, int, int, int]],
) -> None:
    """Generic alignment with offsets.

    This is used to align gaps between alphanumeric sequences.

    Appends the opcodes to `ops`.
    """
    if len(a) == 0:
        if len(b) == 0:
            return
        ops.append(("insert", a_offset, a_offset, b_offset, b_offset + len(b)))
        return
    if len(b) == 0:
        ops.append(("delete", a_offset, a_offset + len(a), b_offset, b_offset))
        return

    if a == b:
        a_len = len(a)
        ops.append(("equal", a_offset, a_offset + a_len, b_offset, b_offset + a_len))
        return

    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, False).get_opcodes():
        ops.append((tag, i1 + a_offset, i2 + a_offset, j1 + b_offset, j2 + b_offset))


def _align_strings(a: str, b: str) -> list[tuple[str, int, int, int, int]]:
    """Aligns two strings with special handling of Unicode word characters.

    Using `difflib.SequenceMatcher` directly often produces poor alignments.

    This function improves on the alignment using the assumption that the
    subsequence of unicode word characters is identical in both `a` and `b`.

    Consequently, the unicode word characters can be aligned precisely, and
    `difflib.SequenceMatcher` is used only for the gaps between alphanumeric
    characters.

    """
    a = _normalize_ascii_letters(a)
    b = _normalize_ascii_letters(b)

    a_index = 0
    b_index = 0

    ops: list[tuple[str, int, int, int, int]] = []

    while True:
        m_a = _ALPHANUMERIC_PATTERN.search(a, a_index)
        m_b = _ALPHANUMERIC_PATTERN.search(b, b_index)

        if m_a is None or m_b is None:
            if (m_a is None) != (m_b is None):
                raise ValueError(
                    "Expected alphanumeric parts to be equal, but they differ starting at %r and %r"
                    % (a[a_index:], b[b_index:])
                )

            _align_generic(a_index, a[a_index:], b_index, b[b_index:], ops)
            break

        m_a_start = m_a.start()
        m_b_start = m_b.start()
        m_a_group = m_a.group()
        m_b_group = m_b.group()

        m_len = min(len(m_a_group), len(m_b_group))

        _align_generic(
            a_index, a[a_index:m_a_start], b_index, b[b_index:m_b_start], ops
        )

        a_index = m_a_start + m_len
        b_index = m_b_start + m_len

        if a[m_a_start:a_index] != b[m_b_start:b_index]:
            raise ValueError(
                "Expected alphanumeric parts to be equal, but they differ starting at %r and %r"
                % (a[m_a_start:], b[m_b_start:])
            )

        ops.append(("equal", m_a_start, a_index, m_b_start, b_index))

    merged_opcodes: list[tuple[str, int, int, int, int]] = []
    last_tag = None
    for tag, i1, i2, j1, j2 in ops:
        if tag == last_tag:
            _, prev_i1, prev_i2, prev_j1, prev_j2 = merged_opcodes[-1]
            assert prev_i2 == i1
            assert prev_j2 == j1
            merged_opcodes[-1] = (tag, prev_i1, i2, prev_j1, j2)
            continue
        merged_opcodes.append((tag, i1, i2, j1, j2))
        last_tag = tag

    return merged_opcodes


def _find_first_primary_entity_name_text_node(
    adjusted_nodes: list[docutils.nodes.Node],
) -> Optional[docutils.nodes.Text]:
    for adjusted_node in adjusted_nodes:
        node: docutils.nodes.Element
        for node in adjusted_node.findall(
            lambda node: (
                isinstance(node, sphinx.addnodes.desc_addname)
                or (
                    isinstance(node, sphinx.addnodes.desc_name)
                    and "sig-name-nonprimary" not in node["classes"]
                )
            )
        ):
            for text_node in cast(docutils.nodes.Element, node).findall(
                docutils.nodes.Text
            ):
                return text_node
    return None


def _findall(
    root: docutils.nodes.Node, condition, ancestor_condition, ancestor_matches: bool
):
    if isinstance(root, condition):
        yield (root, ancestor_matches)
    if isinstance(root, ancestor_condition):
        ancestor_matches = True
    for child in root.children:  # type: ignore[attr-defined]
        yield from _findall(child, condition, ancestor_condition, ancestor_matches)


# For debugging
def _dump_opcodes(ops, a, b):
    for tag, i1, i2, j1, j2 in ops:
        print(
            "%r : (%d..%d) %r -> (%d..%d) %r"
            % (tag, i1, i2, a[i1:i2], j1, j2, b[j1:j2])
        )


class FormatApplier:
    components: list[FormatInputComponent]
    adjusted_nodes: list[docutils.nodes.Node]
    ignored_nodes: set[int]

    def __init__(self):
        self.components = []
        self.adjusted_nodes = []
        self.ignored_nodes = set()

    def add_signature_child_nodes(
        self, signature_child_nodes: list[docutils.nodes.Node]
    ):
        new_adjusted_nodes = _sig_transform_nodes(
            self.ignored_nodes, signature_child_nodes
        )
        self.adjusted_nodes.extend(new_adjusted_nodes)
        for adjusted_node in new_adjusted_nodes:
            for text_node, in_xref in _findall(
                adjusted_node,
                condition=docutils.nodes.Text,
                ancestor_condition=sphinx.addnodes.pending_xref,
                ancestor_matches=False,
            ):
                orig_text = text_node.astext()
                text = orig_text
                parent = text_node.parent
                if parent is not None:
                    text = parent.get("munged_text_for_formatting", text)
                self.components.append(
                    FormatInputComponent(
                        orig_text=orig_text,
                        input_text=text,
                        node=text_node,
                        not_preferred_for_inserts=in_xref,
                    )
                )

    def get_format_input(self, start_index: int = 0) -> str:
        return "".join(c.input_text for c in self.components[start_index:])

    def apply(
        self,
        formatted_input: str,
        formatted_output: str,
        signature_to_modify: sphinx.addnodes.desc_signature,
    ):
        """Align formatted input and output and apply changes to the signature.

        Args:
          formatted_input: Input to the formatter.
          formatted_output: Formatted output.
          signature_to_modify: Signature to modify in place.
        """

        components = self.components
        component_i = 0
        max_component_i = len(components) - 1
        cur_component = components[0]
        component_start_offset = 0
        component_end_offset = len(cur_component.orig_text)
        replacements: dict[int, list[docutils.nodes.Node]] = collections.defaultdict(
            list
        )

        def _get_opcodes():
            return _align_strings(formatted_input, formatted_output)

        # Align `formatted_input` to `formatted_output`.

        try:
            opcodes = _get_opcodes()
        except ValueError as e:
            logger.warning(
                "Failed to align formatted output to input, skipping formatting: %s",
                e,
                location=signature_to_modify,
            )
            return

        # Find the first text node of the entity name.
        #
        # Sometimes the formatter may indent the primary entity name, e.g.:
        #
        #     std::integral_constant<ptrdiff_t, N>
        #         tensorstore::GetStaticOrDynamicExtent(span<X, N>);
        #
        # where the primary entity name is `tensorstore::GetStaticOrDynamicExtent`.
        #
        # This is not desirable for API documentation, and therefore is stripped
        # out.
        #
        # To check for and remove such indentation, first locate the Text node
        # corresponding to the start of the primary entity name.
        first_name_text_node = _find_first_primary_entity_name_text_node(
            self.adjusted_nodes
        )

        # Then determine the offests into `formatted_input` and
        # `formatted_output` corresponding to `first_name_text_node`.
        first_name_text_node_input_offset = 0
        for component in components:
            if component.node is first_name_text_node:
                break
            first_name_text_node_input_offset += len(component.orig_text)

        # Determine output offset of `first_name_text_node_input_offset`.
        first_name_text_node_output_offset = 0
        for tag, i1, i2, j1, j2 in opcodes:
            if i2 >= first_name_text_node_input_offset:
                if tag == "equal":
                    first_name_text_node_output_offset = j1 + (
                        first_name_text_node_input_offset - i1
                    )
                else:
                    first_name_text_node_output_offset = j1
            if i2 > first_name_text_node_input_offset:
                break

        # Check if `first_name_text_node` is indented on a new line.
        if (
            m := _INDENTED_LINE_PATTERN.fullmatch(
                formatted_output, 0, first_name_text_node_output_offset
            )
        ) is not None:
            # Strip leading whitespace, and recompute opcodes.
            formatted_output = (
                formatted_output[: m.start(1)]
                + formatted_output[first_name_text_node_output_offset:]
            )
            opcodes = _get_opcodes()

        # Compute the replacement text nodes for each component.
        for tag, i1, i2, j1, j2 in opcodes:
            while True:
                if i1 == component_end_offset and (
                    i1 != i2
                    or (
                        cur_component.not_preferred_for_inserts
                        and component_i != max_component_i
                    )
                ):
                    component_start_offset = component_end_offset
                    component_i += 1
                    cur_component = components[component_i]

                    component_end_offset = component_start_offset + len(
                        cur_component.orig_text
                    )
                cur_replacements = replacements[id(cur_component.node)]
                if tag == "equal":
                    value = cur_component.orig_text[
                        i1 - component_start_offset : i2 - component_start_offset
                    ]
                    i1 += len(value)
                    cur_replacements.append(SignatureText(value))
                else:
                    while j1 < j2:
                        if (
                            m := _PUNCTUATION_PATTERN.search(formatted_output, j1, j2)
                        ) is not None:
                            m_start = m.start()
                            m_end = m.end()
                        else:
                            m_start = m_end = j2
                        if j1 != m_start:
                            cur_replacements.append(
                                SignatureText(formatted_output[j1:m_start])
                            )
                        if m_start != m_end:
                            t = formatted_output[m_start:m_end]
                            cur_replacements.append(
                                sphinx.addnodes.desc_sig_punctuation(t, t)
                            )
                        j1 = m_end
                    i1 = min(i2, component_end_offset)
                if i1 == i2:
                    break

        try:
            replacement_nodes = _replace_text_nodes(
                self.adjusted_nodes, self.ignored_nodes, replacements
            )
        except Exception as e:
            logger.warning(
                "Failed to apply formatting, skipping formatting: %s",
                e,
                location=signature_to_modify,
            )
            return

        del signature_to_modify[:]
        signature_to_modify.extend(replacement_nodes)

        if "sig-wrap" in signature_to_modify["classes"]:
            signature_to_modify["classes"].remove("sig-wrap")

        signature_to_modify["is_multiline"] = False


def _format_signature_with_black(
    domain: str, objtype: str, node: sphinx.addnodes.desc_signature, options
):
    import black

    black_format_style = options.get("black_format_style")
    assert black_format_style is not None

    mode = black.FileMode(
        line_length=black_format_style.line_length
        or options["wrap_signatures_column_limit"],
        string_normalization=black_format_style.string_normalization,
    )

    applier = FormatApplier()

    def _format_with_black(
        signature: str,
        ensure_prefix_choices: list[str],
        add_empty_body: bool,
        initial_indent: int,
    ) -> Optional[tuple[str, str]]:
        if add_empty_body:
            # Note: Use `pass` rather than `...` as the empty body because black
            # tries to put `...` on the same line, which impacts the line length
            # limit.
            signature += ":\n    pass"

        # Extract the initial prefix of `signature` to be munged.
        #
        # Sphinx signatures may be invalid Python syntax, such as:
        #
        #   foo.bar.func(a, b, c)
        #   class foo.bar.C
        #   class foo.bar.C[A, B]
        #   exception Foo(RuntimeError)
        #   property foo : T
        #   staticmethod foo(a, b, c)
        #   async classmethod foo(a, b, c)
        #
        # To munge these signatures into a form that is syntactically valid, they
        # are transformed as follows:
        #
        # 1. The initial prefix is defined to contain all of the initial
        #    space-separated optionally-dotted identifiers/keywords.
        m = re.match(r"^[^=:(\[]*[^\s=:(\[]", signature)
        if m is None:
            logger.warning(
                "Failed to extract initial prefix from %r for black formatting",
                signature,
                location=node,
            )
            return None
        initial_prefix = m[0]

        # 2. All spaces and dots in the initial prefix are replaced with
        #    underscores to produce a valid identifier.
        base_munged_prefix = re.sub("[ .]", "_", initial_prefix)

        for ensure_prefix_i, ensure_prefix in enumerate(ensure_prefix_choices):
            # 3. The first part of `base_munged_prefix` is replaced with
            #    `ensure_prefix` if it is longer than `ensure_prefix`. This
            #    ensures that adding `ensure_prefix` does not impact the
            #    effective line length. If `base_munged_prefix` is too short,
            #    the effective line length will be affected.
            ensure_prefix += "_" * max(0, initial_indent - len(ensure_prefix))
            extra_prefix_len = max(
                initial_indent, len(ensure_prefix) - len(base_munged_prefix) + 1
            )
            munged_prefix = (
                ensure_prefix
                + base_munged_prefix[len(ensure_prefix) - extra_prefix_len :]
            )
            extra_prefix = ensure_prefix[:extra_prefix_len]

            munged_signature = munged_prefix + signature[len(initial_prefix) :]

            try:
                formatted = black.format_str(munged_signature, mode=mode)
            except Exception as e:
                if ensure_prefix_i + 1 != len(ensure_prefix_choices):
                    continue
                logger.warning(
                    "Failed to format %r: %r", munged_signature, e, location=node
                )
                return None

            if not formatted.startswith(extra_prefix):
                logger.warning(
                    "Expected formatted output %r to start with %r",
                    formatted,
                    extra_prefix,
                    location=node,
                )
                return None

            munged_signature = munged_signature[extra_prefix_len:]
            formatted = formatted[extra_prefix_len:]

            SUFFIX_PATTERN = r"(?::\s*pass)?\s*$"

            formatted = re.sub(SUFFIX_PATTERN, "", formatted)
            munged_signature = re.sub(SUFFIX_PATTERN, "", munged_signature)
            return munged_signature, formatted

        assert False  # At least one prefix must be specified

    def _format_objtype_with_black(
        signature: str,
        objtype: str,
        initial_indent: int,
    ) -> Optional[tuple[str, str]]:
        if objtype in ("function", "method"):
            ensure_prefix_choices = ["def "]
        elif objtype in ("class", "exception"):
            # If formatting as a class fails, attempt to format as a `def` to
            # accommodate the Sphinx `class Foo(a: int, b: int = 3)` constructor
            # syntax.
            ensure_prefix_choices = ["class ", "def "]
        else:
            ensure_prefix_choices = [""]

        return _format_with_black(
            signature=signature,
            initial_indent=initial_indent,
            ensure_prefix_choices=ensure_prefix_choices,
            add_empty_body=objtype in ("class", "exception", "function", "method"),
        )

    parent_type_param_i = None
    for i, orig_child in enumerate(node.children):
        found_name = False
        for n in orig_child.findall(condition=sphinx.addnodes.desc_name):
            found_name = True
            break
        if found_name:
            break
        if (
            isinstance(orig_child, docutils.nodes.Element)
            and orig_child.get("sphinx_immaterial_parent_type_parameter_list") is True
        ):
            # This is the parent entity type parameter list added by apigen.
            parent_type_param_i = i
            break

    if parent_type_param_i is not None:
        # First format up to the end of the parent type parameters
        applier.add_signature_child_nodes(node.children[: parent_type_param_i + 1])
        format_result = _format_with_black(
            applier.get_format_input(),
            ["class " if objtype in ("class", "exception") else ""],
            add_empty_body=objtype in ("class", "exception"),
            initial_indent=0,
        )
        if format_result is None:
            return
        signature, formatted = format_result

        remaining_component_i = len(applier.components)

        # Format the remainder of the signature separately, prepending it with a
        # suitable prefix to match the object type and the length of the last
        # line of the previous formatted output.
        m = re.search("[^\n]*$", formatted)
        assert m is not None
        prefix_len = len(m[0])

        applier.add_signature_child_nodes(node.children[parent_type_param_i + 1 :])
        format_result = _format_objtype_with_black(
            signature=applier.get_format_input(remaining_component_i),
            initial_indent=prefix_len,
            objtype=objtype,
        )
        if format_result is None:
            return
        remaining_signature, remaining_formatted = format_result

        signature += remaining_signature
        formatted += remaining_formatted

    else:
        applier.add_signature_child_nodes(node.children)
        format_result = _format_objtype_with_black(
            signature=applier.get_format_input(),
            objtype=objtype,
            initial_indent=0,
        )
        if format_result is None:
            return
        signature, formatted = format_result

    applier.apply(signature, formatted, node)


_PUNCTUATION_PATTERN = re.compile("[(),]")


def _make_text_node_from_source(
    cls: type, source: docutils.nodes.Node, text: str
) -> docutils.nodes.Element:
    node = cls(text, text)
    node.source = source.source
    node.line = source.line
    return node


def _sig_transform_nodes(
    ignored: set[int], nodes: list[docutils.nodes.Node]
) -> list[docutils.nodes.Node]:
    return _transform_node_list(nodes, _sig_transform_node, ignored)


def _sig_transform_generic(
    ignored: set[int], node: docutils.nodes.Element
) -> list[docutils.nodes.Node]:
    new_node = node.copy()
    # Ensure the new node does not contain any children. `desc_sig_space`, for
    # example, adds a default child text node with content " ".
    del new_node[:]
    new_node.extend(_sig_transform_nodes(ignored, node.children))
    return [new_node]


def _sig_transform_node_default(
    ignored: set[int], node: docutils.nodes.Node
) -> list[docutils.nodes.Node]:
    if isinstance(node, docutils.nodes.Text):
        return [node.copy()]
    assert isinstance(node, docutils.nodes.TextElement)
    assert node.child_text_separator == ""
    return _sig_transform_generic(ignored, node)


def _sig_transform_desc_signature_line(
    ignored: set[int], node: docutils.nodes.Element
) -> list[docutils.nodes.Node]:
    return _sig_transform_nodes(ignored, node.children)


def _sig_transform_desc_parameter_list(
    ignored: set[int], node: docutils.nodes.Element, open_punct: str, close_punct: str
) -> list[docutils.nodes.Node]:
    new_nodes: list[docutils.nodes.Node] = [
        _make_text_node_from_source(
            sphinx.addnodes.desc_sig_punctuation, node, open_punct
        )
    ]
    for i, child in enumerate(node.children):
        if i != 0:
            new_nodes.append(
                _make_text_node_from_source(
                    sphinx.addnodes.desc_sig_punctuation, node, ","
                )
            )
        new_nodes.extend(_sig_transform_node(ignored, child))
    new_nodes.append(
        _make_text_node_from_source(
            sphinx.addnodes.desc_sig_punctuation, node, close_punct
        )
    )
    return new_nodes


def _sig_transform_desc_returns(
    ignored: set[int], node: docutils.nodes.Element
) -> list[docutils.nodes.Node]:
    return [
        _make_text_node_from_source(sphinx.addnodes.desc_sig_punctuation, node, "->"),
        *_sig_transform_nodes(ignored, node.children),
    ]


def _sig_transform_viewcode_anchor(
    ignored: set[int], node: docutils.nodes.Element
) -> list[docutils.nodes.Node]:
    new_node = node.deepcopy()
    ignored.add(id(new_node))
    return [new_node]


def _sig_transform_parameter(
    ignored: set[int], node: docutils.nodes.Element
) -> list[docutils.nodes.Node]:
    new_node = _make_text_node_from_source(docutils.nodes.inline, node, "")
    new_node["classes"] = node["classes"]
    new_node.extend(_sig_transform_nodes(ignored, node.children))
    return [new_node]


_SIG_TRANSFORM_FUNCS: dict[
    type, Callable[[set[int], docutils.nodes.Element], list[docutils.nodes.Node]]
] = {
    sphinx.addnodes.desc_signature_line: _sig_transform_desc_signature_line,
    sphinx.addnodes.desc_parameterlist: (
        lambda ignored, node: _sig_transform_desc_parameter_list(
            ignored, node, "(", ")"
        )
    ),
    sphinx.addnodes.desc_parameter: _sig_transform_parameter,
    sphinx.addnodes.desc_returns: _sig_transform_desc_returns,
    sphinx.addnodes.pending_xref: _sig_transform_generic,
    sphinx.ext.viewcode.viewcode_anchor: _sig_transform_viewcode_anchor,
}

if sphinx.version_info >= (7, 3):
    _SIG_TRANSFORM_FUNCS[sphinx.addnodes.desc_type_parameter_list] = (
        lambda ignored, node: _sig_transform_desc_parameter_list(
            ignored, node, "[", "]"
        )
    )
    _SIG_TRANSFORM_FUNCS[sphinx.addnodes.desc_type_parameter] = _sig_transform_parameter


def _sig_transform_node(
    ignored: set[int], node: docutils.nodes.Node
) -> list[docutils.nodes.Node]:
    return _SIG_TRANSFORM_FUNCS.get(type(node), _sig_transform_node_default)(
        ignored,
        node,  # type: ignore[arg-type]
    )


class FormatSignaturesTransform(sphinx.transforms.SphinxTransform):
    """Applies the clang-format changes previously-computed by `env_updated` to
    each individual signature.
    """

    # Early
    default_priority = 0

    def apply(self, **kwargs: Any) -> None:
        formatted_signatures = getattr(self.env, _FORMATTED_SIGNATURES, None)
        if formatted_signatures is None:
            return
        for node in self.document.findall(sphinx.addnodes.desc_signature):
            signature_id = node.get(_SIGNATURE_FORMAT_ID)
            if signature_id is None:
                continue
            formatted_signature = formatted_signatures.get(signature_id)
            if formatted_signature is None:
                continue
            applier = FormatApplier()
            applier.add_signature_child_nodes(node.children)
            applier.apply(applier.get_format_input(), formatted_signature, node)


def merge_info(
    app: sphinx.application.Sphinx,
    env: sphinx.environment.BuildEnvironment,
    docnames: List[str],
    other: sphinx.environment.BuildEnvironment,
) -> None:
    """Merges collected signatures to be formatted by clang-format."""
    merged_sigs = _get_collected_signatures(env)
    for key, sigs in _get_collected_signatures(other).items():
        merged_sigs[key].update(sigs)


DOMAIN_CLANG_FORMAT_LANGUAGE = {
    "cpp": "Cpp",
    "c": "Cpp",
    "js": "JavaScript",
}

ClangFormatStyle = Union[str, Dict[str, Any]]


@pydantic.dataclasses.dataclass
class BlackFormatStyle:
    line_length: Optional[int] = None
    """Line length limit.

    Defaults to the value of :objconf:`wrap_signatures_column_limit`.
    """

    string_normalization: bool = True
    """Indicates whether to normalize quotes. This corresponds to the inverse of Black
    CLI's `--skip-string-normalization <https://black.readthedocs.io/en/stable/
    usage_and_configuration/the_basics.html#s-skip-string-normalization>`_ option."""


def env_updated(
    app: sphinx.application.Sphinx, env: sphinx.environment.BuildEnvironment
) -> None:
    """Hook for the `env-updated` event that invokes clang-format and stores the
    formatted output in the environment.

    This runs just once per build with all of the collected signatures.

    The formatted output is applied later to individual signatures in each
    individual writer process by `FormatSignaturesTransform`.
    """
    all_signatures = _get_collected_signatures(env)
    formatted_signatures = {}

    signatures_for_style: Dict[str, Dict[str, str]] = collections.defaultdict(dict)

    for (domain, objtype), signatures in all_signatures.items():
        options = object_description_options.get_object_description_options(
            env, domain, objtype
        )

        style: ClangFormatStyle = options["clang_format_style"]
        if isinstance(style, str):
            style = {"BasedOnStyle": style}
        else:
            style = style.copy()

        style.setdefault("ColumnLimit", options["wrap_signatures_column_limit"])
        language = DOMAIN_CLANG_FORMAT_LANGUAGE.get(domain)
        if language is not None:
            style.setdefault("Language", language)
        style_key = json.dumps(style, sort_keys=True)
        signatures_for_style[style_key].update(signatures)

    for style_key, signatures in signatures_for_style.items():
        source = io.StringIO()

        for sig_id, signature in signatures.items():
            source.write(f"// {sig_id}\n")
            source.write(signature.strip().strip(";"))
            source.write(";\n")

        result = subprocess.run(
            [app.config.clang_format_command, f"-style={style_key}"],
            input=source.getvalue(),
            encoding="utf-8",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if result.returncode != 0:
            logger.error(
                f"{app.config.clang_format_command} exited with code %d: %s",
                result.returncode,
                result.stderr,
            )
            return
        result.check_returncode()
        stdout = result.stdout

        for m in re.finditer(
            "^// ([0-9a-f]+)\n((?:(?!\n//).)+)", stdout, re.MULTILINE | re.DOTALL
        ):
            formatted_signatures[m.group(1)] = m.group(2)

    setattr(env, _FORMATTED_SIGNATURES, formatted_signatures)


def setup(app: sphinx.application.Sphinx):
    app.setup_extension("sphinx_immaterial.apidoc.object_description_options")
    app.add_transform(CollectSignaturesTransform)
    app.add_post_transform(FormatSignaturesTransform)
    object_description_options.add_object_description_option(
        app,
        "clang_format_style",
        default=None,
        type_constraint=Optional[ClangFormatStyle],
    )
    object_description_options.add_object_description_option(
        app,
        "black_format_style",
        default=None,
        type_constraint=Optional[BlackFormatStyle],
    )

    app.connect("env-merge-info", merge_info)
    app.connect("env-updated", env_updated)
    app.add_node(
        cast(Type[docutils.nodes.Element], SignatureText),
        html=(_html_visit_signature_text, _html_depart_signature_text),
        latex=(_latex_visit_signature_text, _latex_depart_signature_text),
    )
    app.add_config_value(
        name="clang_format_command",
        default="clang-format",
        rebuild="env",
        types=(str,),
    )
    return {"parallel_read_safe": True, "parallel_write_safe": True}
