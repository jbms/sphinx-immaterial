"""Support for cross-referencing externally-defined C++ symbols.

The builtin `sphinx.ext.intersphinx` extension does not work well for C++
because it only supports exact reference matches.  Consequently, a reference to
`std::vector<int>` will not find a more general `std::vector` entry.

This extension implements the simple solution of stripping off all template
arguments when matching, which is not perfect but handles the most common use
cases.
"""

import re
from typing import List, Dict, NamedTuple, Optional, TypedDict

import docutils.nodes
import sphinx.application
import sphinx.environment
import sphinx.addnodes


class ObjectInfo(NamedTuple):
    url: str
    desc: str
    object_type: str


class ExternalCppReference(TypedDict):
    """A class used to represent each dictionary field's value specified in
    :confval:`external_cpp_references`."""

    url: str
    """URL to use as the target for references to this symbol."""

    object_type: str
    """C++ object type.
    This should be one of the object types defined by the C++ domain:

    .. hlist::
        - :python:`"class"`
        - :python:`"union"`
        - :python:`"function"`
        - :python:`"member"`
        - :python:`"type"`
        - :python:`"concept"`
        - :python:`"enum"`
        - :python:`"enumerator"`
    """

    desc: str
    """Description text to include in the tooltip."""


def _strip_template_arguments(s: str) -> Optional[str]:
    s = s.lstrip(":")
    prev_index = 0
    retained_parts = []
    nested: List[str] = []
    pattern = re.compile("[()<>]")
    s_len = len(s)
    while prev_index < s_len:
        m = pattern.search(s, prev_index)
        if m is None:
            if not nested:
                retained_parts.append(s[prev_index:])
            break
        if not nested:
            retained_parts.append(s[prev_index : m.start()])
        ch = m.group(0)
        if nested and ch == nested[-1]:
            del nested[-1]
            prev_index = m.end()
            continue
        if ch == "(":
            nested.append(")")
            prev_index = m.end()
            continue
        if ch == "<":
            nested.append(">")
            prev_index = m.end()
            continue
        if ch == ")":
            while nested and nested[-1] != ")":
                del nested[-1]
            if not nested:
                # Mismatched parentheses
                return None
            prev_index = m.end()
            continue
        if ch == ">":
            # Unmatched
            prev_index = m.end()
            continue
    return "".join(retained_parts)


def _missing_reference(
    app: sphinx.application.Sphinx,
    env: sphinx.environment.BuildEnvironment,
    node: sphinx.addnodes.pending_xref,
    contnode: docutils.nodes.TextElement,
) -> Optional[docutils.nodes.reference]:
    data = get_mappings(app)

    if node.get("refdomain") != "cpp":
        return None

    target = _strip_template_arguments(node["reftarget"])
    if target is None:
        return None
    result = data.get(target)
    if result is None:
        return None

    reftitle = result.desc

    newnode = docutils.nodes.reference(
        "", "", internal=False, refuri=result.url, reftitle=reftitle
    )
    newnode.append(contnode)
    if result.object_type in ("class", "type alias", "enum"):
        newnode["classes"].append("desctype")

    return newnode


_CPPREFERENCE_APP_KEY = "_sphinx_immaterial_cppreference_objects"


def get_mappings(app: sphinx.application.Sphinx) -> Dict[str, ObjectInfo]:
    cpp_objects = getattr(app, _CPPREFERENCE_APP_KEY, None)
    if cpp_objects is None:
        cpp_objects = {}
        setattr(app, _CPPREFERENCE_APP_KEY, cpp_objects)
        return cpp_objects
    return cpp_objects


def _load_from_config(app: sphinx.application.Sphinx) -> None:
    mappings = get_mappings(app)

    for name, value in app.config.external_cpp_references.items():
        name = name.lstrip(":")
        mappings[name] = ObjectInfo(**value)


def setup(app: sphinx.application.Sphinx):
    app.connect("missing-reference", _missing_reference)
    app.connect("builder-inited", _load_from_config)
    app.add_config_value(
        name="external_cpp_references",
        default={},
        types=(Dict[str, "ExternalCppReference"],),
        rebuild="env",
    )
    return {"parallel_read_safe": True, "parallel_write_safe": True}
