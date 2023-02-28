"""Defines the `cpp_strip_namespaces_from_signatures` config option."""

from typing import List

import docutils.nodes
import sphinx.addnodes
import sphinx.application


def _strip_namespaces_from_signature(
    node: docutils.nodes.Element, namespaces: List[str]
):
    # Collect nodes to remove first, then remove them in reverse order.
    removals = []
    for child in node.findall(condition=sphinx.addnodes.desc_sig_name):
        parent = child.parent
        if not isinstance(parent, sphinx.addnodes.pending_xref):
            continue
        if (
            parent["reftype"] != "identifier"
            or parent["refdomain"] != "cpp"
            or parent["reftarget"] not in namespaces
        ):
            continue
        grandparent = parent.parent
        if isinstance(grandparent, sphinx.addnodes.desc_addname):
            continue
        index = grandparent.index(parent)
        if index + 1 >= len(grandparent.children):
            continue
        sibling = grandparent[index + 1]
        if (
            not isinstance(sibling, sphinx.addnodes.desc_sig_punctuation)
            or sibling.astext() != "::"
        ):
            continue
        removals.append((grandparent, index))

    removals.reverse()

    for parent, index in removals:
        del parent[index : index + 2]


def _strip_namespaces_from_signatures(
    app: sphinx.application.Sphinx,
    domain: str,
    objtype: str,
    content: docutils.nodes.Element,
) -> None:
    """object-description-transform callback that strips namespaces."""
    if domain != "cpp":
        return

    namespaces = app.config.cpp_strip_namespaces_from_signatures
    if not namespaces:
        return

    signatures = content.parent[:-1]
    for signode in signatures:
        assert isinstance(signode, sphinx.addnodes.desc_signature)
        _strip_namespaces_from_signature(signode, namespaces)


def setup(app: sphinx.application.Sphinx):
    app.add_config_value(
        "cpp_strip_namespaces_from_signatures",
        default=[],
        rebuild="env",
        types=(List[str],),
    )
    app.connect("object-description-transform", _strip_namespaces_from_signatures)

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
