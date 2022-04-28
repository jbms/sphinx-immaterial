"""Sphinx extension that formats signatures using an external tool.

Currently only clang-format is supported.
"""

import collections
import hashlib
import io
import json
import re
import subprocess
from typing import Dict, List, Any, Union, Optional

import docutils.nodes
import sphinx.addnodes
import sphinx.application
import sphinx.environment
import sphinx.transforms
import sphinx.util.logging

from . import apidoc_formatting

logger = sphinx.util.logging.getLogger(__name__)

_SIGNATURE_FORMAT_ID = "signature_format_id"

_FORMATTED_SIGNATURES = "sphinx_immaterial_formatted_signatures"


def _get_collected_signatures(
    env: sphinx.environment.BuildEnvironment,
) -> Dict[str, Dict[str, str]]:
    attr = "_sphinx_immaterial_collected_signatures_to_format"
    x = getattr(env, attr, None)
    if x is None:
        x = collections.defaultdict(dict)
        setattr(env, attr, x)
    return x


class SignatureText(docutils.nodes.Text):
    pass


def visit_signature_text(self, node: SignatureText) -> None:
    encoded = self.encode(node.astext()).replace(" ", "&nbsp;").replace("\n", "<br>")
    self.body.append(encoded)


def depart_signature_text(self, node: SignatureText) -> None:
    pass


class CollectSignaturesTransform(sphinx.transforms.SphinxTransform):

    # Late
    default_priority = 900

    def apply(self, **kwargs: Any) -> None:
        collected_signatures = _get_collected_signatures(self.env)
        for node in self.document.traverse(sphinx.addnodes.desc_signature):
            parent = node.parent
            domain = parent.get("domain")
            objtype = parent.get("objtype")
            options = apidoc_formatting.get_object_description_options(
                self.env, domain, objtype
            )
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


def _append_child_copy_source_info(
    target: docutils.nodes.Node,
    source_node: docutils.nodes.Node,
    node: docutils.nodes.Node,
):
    source = source_node.source
    line = source_node.line
    target.append(node)
    node.source = source
    node.line = line


def _extend_children_copy_source_info(
    target: docutils.nodes.Node,
    source_node: docutils.nodes.Node,
    children: List[docutils.nodes.Node],
):
    source = source_node.source
    line = source_node.line
    target.extend(children)
    for child in children:
        child.source = source
        child.line = line


def _format_signature(node: sphinx.addnodes.desc_signature, formatted: str) -> None:
    if "sig-wrap" in node["classes"]:
        node["classes"].remove("sig-wrap")
    children = list(node.children)
    del node[:]

    formatted_i = 0

    def format_next_text(text: str) -> str:
        nonlocal formatted_i
        if formatted[formatted_i : formatted_i + len(text)] == text:
            # Matches fully
            formatted_i += len(text)
            return text

        pattern = re.compile(
            r"\s*" + r"\s*".join(re.escape(x) for x in re.sub(r"\s", "", text))
        )
        m = pattern.match(formatted, formatted_i)
        if m is None:
            raise ValueError("Failed to match")
        formatted_i = m.end()
        return m.group(0)

    prev_text_node = None
    seen_name = False
    name_text_node_replacement = None

    def process(node: docutils.nodes.Node):
        nonlocal prev_text_node, seen_name, name_text_node_replacement
        if isinstance(node, docutils.nodes.Text):
            new_text = format_next_text(node.astext())
            new_node = SignatureText(new_text)
            if not seen_name:
                prev_text_node = new_node
            new_node.source = node.source
            new_node.line = node.line
            return [new_node]
        if not seen_name:
            if isinstance(node, sphinx.addnodes.desc_addname) or (
                isinstance(node, sphinx.addnodes.desc_name)
                and "sig-name-nonprimary" not in node["classes"]
            ):
                seen_name = True
                if prev_text_node is not None:
                    m = re.fullmatch(
                        r"(.*\n)(\s+)$", prev_text_node.astext(), re.DOTALL
                    )
                    if m is not None:
                        name_text_node_replacement = (
                            prev_text_node,
                            SignatureText(m.group(1)),
                        )

        if isinstance(node, sphinx.addnodes.desc_signature_line):
            # Exclude the `desc_signature_line` element and just include its children
            # directly.
            new_children = []
            for child in node.children:
                new_children.extend(process(child))
            return new_children
        if isinstance(node, sphinx.addnodes.pending_xref):
            old_children = list(node.children)
            del node[:]
            for child in old_children:
                _extend_children_copy_source_info(node, child, process(child))
            return [node]
        if isinstance(node, sphinx.addnodes.desc_parameter):
            new_node = docutils.nodes.inline("", "")
            new_node["classes"] = node["classes"]
            for child in node.children:
                _append_child_copy_source_info(new_node, child, child)
            new_node.source = node.source
            new_node.line = node.line
            node = new_node
        elif isinstance(node, sphinx.addnodes.desc_parameterlist):
            # First replace with other representation
            new_node = docutils.nodes.inline("", "")
            new_node += sphinx.addnodes.desc_sig_punctuation("(", "(")
            for i, child in enumerate(node.children):
                if i != 0:
                    new_node += sphinx.addnodes.desc_sig_punctuation(",", ",")
                _append_child_copy_source_info(new_node, child, child)
            new_node += sphinx.addnodes.desc_sig_punctuation(")", ")")
            node = new_node
        if isinstance(node, docutils.nodes.TextElement):
            assert node.child_text_separator == ""
            old_children = list(node.children)
            del node[:]
            for child in old_children:
                _extend_children_copy_source_info(node, child, process(child))
            return [node]
        raise ValueError("unexpected child")

    node["is_multiline"] = False
    for child in children:
        _extend_children_copy_source_info(node, child, process(child))

    if name_text_node_replacement is not None:
        (  # pylint: disable=unpacking-non-sequence
            existing_node,
            new_node,
        ) = name_text_node_replacement
        source = existing_node.source
        line = existing_node.line
        existing_node.parent.replace(existing_node, new_node)
        new_node.source = source
        new_node.line = line


class FormatSignaturesTransform(sphinx.transforms.SphinxTransform):

    # Early
    default_priority = 0

    def apply(self, **kwargs: Any) -> None:
        formatted_signatures = getattr(self.env, _FORMATTED_SIGNATURES, None)
        if formatted_signatures is None:
            return
        for node in self.document.traverse(sphinx.addnodes.desc_signature):
            signature_id = node.get(_SIGNATURE_FORMAT_ID)
            if signature_id is None:
                continue
            formatted_signature = formatted_signatures.get(signature_id)
            if formatted_signature is None:
                continue
            _format_signature(node, formatted_signature)


def merge_info(
    app: sphinx.application.Sphinx,
    env: sphinx.environment.BuildEnvironment,
    docnames: List[str],
    other: sphinx.environment.BuildEnvironment,
) -> None:
    _get_collected_signatures(env).update(_get_collected_signatures(other))


DOMAIN_CLANG_FORMAT_LANGUAGE = {
    "cpp": "Cpp",
    "c": "Cpp",
    "js": "JavaScript",
}

ClangFormatStyle = Union[str, Dict[str, Any]]


def env_updated(
    app: sphinx.application.Sphinx, env: sphinx.environment.BuildEnvironment
) -> None:
    all_signatures = _get_collected_signatures(env)
    formatted_signatures = {}

    signatures_for_style = collections.defaultdict(dict)

    for (domain, objtype), signatures in all_signatures.items():
        options = apidoc_formatting.get_object_description_options(env, domain, objtype)

        style: ClangFormatStyle = options["clang_format_style"]
        if isinstance(style, str):
            style = {"BasedOnStyle"}
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
    app.add_transform(CollectSignaturesTransform)
    app.add_post_transform(FormatSignaturesTransform)
    apidoc_formatting.add_object_description_option(
        app,
        "clang_format_style",
        default=None,
        type_constraint=Optional[ClangFormatStyle],
    )

    app.connect("env-merge-info", merge_info)
    app.connect("env-updated", env_updated)
    app.add_node(SignatureText, html=(visit_signature_text, depart_signature_text))
    app.add_config_value(
        name="clang_format_command",
        default="clang-format",
        rebuild="env",
        types=(str,),
    )
    return {"parallel_read_safe": True, "parallel_write_safe": True}
