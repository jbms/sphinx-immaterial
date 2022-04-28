"""Support for cross-referencing externally-defined C++ symbols.

The builtin `sphinx.ext.intersphinx` extension does not work well for C++
because it only supports exact reference matches.  Consequently, a reference to
`std::vector<int>` will not find a more general `std::vector` entry.

This extension implements the simple solution of stripping off all template
arguments when matching, which is not perfect but handles the most common use
cases.
"""

import re
import typing

import docutils.nodes
import sphinx.application
import sphinx.environment
import sphinx.addnodes


class ObjectInfo(typing.NamedTuple):
    url: str
    desc: str
    object_type: str


def _strip_template_arguments(s: str) -> typing.Optional[str]:
    s = s.lstrip(":")
    prev_index = 0
    retained_parts = []
    nested = []
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
) -> typing.Optional[docutils.nodes.reference]:

    data = get_mappings(app)

    if node.get("refdomain") != "cpp":
        return None

    target = _strip_template_arguments(node["reftarget"])
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


def get_mappings(app: sphinx.application.Sphinx) -> typing.Dict[str, ObjectInfo]:
    cpp_objects = getattr(app.env, "cppreference_objects", None)
    if cpp_objects is None:
        cpp_objects = app.env.cppreference_objects = {}
    return cpp_objects


def _load_from_config(app: sphinx.application.Sphinx) -> None:
    mappings = get_mappings(app)

    for name, value in app.config.external_cpp_references.items():
        mappings[name] = ObjectInfo(**value)


def setup(app: sphinx.application.Sphinx):
    app.connect("missing-reference", _missing_reference)
    app.connect("builder-inited", _load_from_config)
    app.add_config_value(
        name="external_cpp_references",
        default={},
        types=(typing.Dict[str, "ExternalCppReference"],),
        rebuild="env",
    )
    return {"parallel_read_safe": True, "parallel_write_safe": True}
