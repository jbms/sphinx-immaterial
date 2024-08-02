"""Python API documentation generation extension.

A separate page is generated for each class/function/member/constant to be
documented.

As with sphinx.ext.autosummary, we have to physically write a separate rST file
to the source tree for each object to document, as an initial preprocesing step,
since that provides the simplest way to get Sphinx to process those pages.  It
is recommended to run the build with the source tree copied to a temporary
directory in order to avoid modifying the real source tree.

Unlike the sphinx.ext.autosummary extension, we use Sphinx Python domain
directives for the "summaries" as well, rather than a plain table, in order to
display the signatures nicely.
"""

import copy
import dataclasses
import importlib
import inspect
import json
import re
import typing
from typing import (
    List,
    Tuple,
    Any,
    Optional,
    Type,
    cast,
    Dict,
    NamedTuple,
    Iterator,
    Set,
)

import docutils.nodes
import docutils.parsers.rst.states
import docutils.statemachine
import sphinx
import sphinx.addnodes
import sphinx.application
from sphinx.domains.python import PythonDomain
import sphinx.environment
import sphinx.ext.autodoc
import sphinx.ext.autodoc.directive
import sphinx.ext.napoleon.docstring
import sphinx.pycode
import sphinx.util.docstrings
import sphinx.util.docutils
import sphinx.util.inspect
import sphinx.util.logging
import sphinx.util.typing

from .. import object_description_options
from ... import sphinx_utils
from .. import apigen_utils
from . import type_param_utils
from .parameter_objects import TYPE_PARAM_SYMBOL_PREFIX_ATTR_KEY

if sphinx.version_info >= (6, 1):
    stringify_annotation = sphinx.util.typing.stringify_annotation
else:
    stringify_annotation = sphinx.util.typing.stringify  # type: ignore[attr-defined]

if sphinx.version_info >= (7, 3):
    from sphinx.domains.python._annotations import _parse_annotation  # type: ignore[import-not-found]
else:
    from sphinx.domains.python import _parse_annotation

logger = sphinx.util.logging.getLogger(__name__)

_UNCONDITIONALLY_DOCUMENTED_MEMBERS = frozenset(
    [
        "__init__",
        "__class_getitem__",
        "__call__",
        "__getitem__",
        "__setitem__",
    ]
)
"""Special members to include even if they have no docstring."""


class ParsedOverload(NamedTuple):
    """Parsed representation of a single overload.

    For non-function types and non-overloaded functions, this just represents the
    object itself.

    Sphinx does not really support pybind11-style overloaded functions directly.
    It has minimal support functions with multiple signatures, with a single
    docstring.  However, pybind11 produces overloaded functions each with their
    own docstring.  This module adds support for documenting each overload as an
    independent function.

    Additionally, we need a way to identify each overload, for the purpose of
    generating a page name, listing in the table of contents sidebar, and
    cross-referencing.  Sphinx does not have a native solution to this problem
    because it is not designed to support overloads.  Doxygen uses some sort of
    hash as the identifier, but that means links break with even minor changes to
    the signature.

    Instead, we require that a unique id be manually assigned to each overload,
    and specified as:

        Overload:
          XXX

    in the docstring.  Then the overload will be identified as
    `module.Class.function(overload)`, and will be documented using the page name
    `module.Class.function-overload`.  Typically the overload id should be chosen
    to be a parameter name that is unique to the overload.
    """

    doc: Optional[str]
    """Docstring for individual overload.  First line is the signature."""

    overload_id: Optional[str] = None
    """Overload id specified in the docstring.

    If there is just a single overload, will be `None`.  Otherwise, if no overload
    id is specified, a warning is produced and the index of the overload,
    i.e. "1", "2", etc., is used as the id.
    """


def _extract_field(doc: str, field: str) -> Tuple[str, Optional[str]]:
    pattern = f"\n\\s*\n{field}:\\s*\n\\s+([^\n]+)\n"
    m = re.search(pattern, doc)
    if m is None:
        return doc, None
    start, end = m.span()
    return f"{doc[:start]}\n\n{doc[end:]}", m.group(1).strip()


_OVERLOADED_FUNCTION_RE = "^([^(]+)\\([^\n]*\nOverloaded function.\n"


def _parse_overloaded_function_docstring(doc: Optional[str]) -> List[ParsedOverload]:
    """Parses a pybind11 overloaded function docstring.

    If the docstring is not for an overloaded function, just returns the full
    docstring as a single "overload".

    :param doc: Original docstring.
    :returns: List of parsed overloads.
    :raises ValueError: If docstring has unexpected format.
    """

    if doc is None:
        return [ParsedOverload(doc=doc, overload_id=None)]
    m = re.match(_OVERLOADED_FUNCTION_RE, doc)
    if m is None:
        # Non-overloaded function
        doc, overload_id = _extract_field(doc, "Overload")
        return [ParsedOverload(doc=doc, overload_id=overload_id)]

    display_name = m.group(1)
    doc = doc[m.end() :]
    i = 1

    def get_prefix(i: int):
        return "\n%d. %s(" % (i, display_name)

    prefix = get_prefix(i)
    parts: List[ParsedOverload] = []
    while doc:
        if not doc.startswith(prefix):
            raise ValueError(
                "Docstring does not contain %r as expected: %r"
                % (
                    prefix,
                    doc,
                )
            )
        doc = doc[len(prefix) - 1 :]
        nl_index = doc.index("\n")
        part_sig = doc[:nl_index]
        doc = doc[nl_index + 1 :]
        i += 1
        prefix = get_prefix(i)
        end_index = doc.find(prefix)
        if end_index == -1:
            part = doc
            doc = ""
        else:
            part = doc[:end_index]
            doc = doc[end_index:]

        part, overload_id = _extract_field(part, "Overload")
        if overload_id is None:
            overload_id = str(i - 1)

        part_doc_with_sig = f"{display_name}{part_sig}\n{part}"
        parts.append(
            ParsedOverload(
                doc=part_doc_with_sig,
                overload_id=overload_id,
            )
        )
    return parts


def _get_overloads_from_documenter(
    documenter: sphinx.ext.autodoc.Documenter,
) -> List[ParsedOverload]:
    docstring = sphinx.util.inspect.getdoc(
        documenter.object,
        documenter.get_attr,
        documenter.env.config.autodoc_inherit_docstrings,
        documenter.parent,
        documenter.object_name,
    )
    return _parse_overloaded_function_docstring(docstring)


def _has_default_value(node: sphinx.addnodes.desc_parameter):
    for sub_node in node.findall(condition=docutils.nodes.literal):
        if "default_value" in sub_node.get("classes"):
            return True
    return False


def _summarize_signature(
    env: sphinx.environment.BuildEnvironment, node: sphinx.addnodes.desc_signature
) -> None:
    """Shortens a signature line to fit within `wrap_signatures_column_limit."""

    obj_desc = node.parent

    options = object_description_options.get_object_description_options(
        env, obj_desc["domain"], obj_desc["objtype"]
    )
    column_limit = options["wrap_signatures_column_limit"]

    def _must_shorten():
        return len(node.astext()) > column_limit

    parameterlist: Optional[sphinx.addnodes.desc_parameterlist] = None
    for parameterlist in node.findall(condition=sphinx.addnodes.desc_parameterlist):
        break

    if parameterlist is None:
        # Can't shorten a signature without a parameterlist
        return

    # Remove initial `self` parameter
    if parameterlist.children and parameterlist.children[0].astext() == "self":
        del parameterlist.children[0]

    added_ellipsis = False
    for next_parameter_index in range(len(parameterlist.children) - 1, -1, -1):
        if not _must_shorten():
            return

        # First remove type annotation of last parameter, but only if it doesn't
        # have a default value.
        last_parameter = parameterlist.children[next_parameter_index]
        if isinstance(
            last_parameter, sphinx.addnodes.desc_parameter
        ) and not _has_default_value(last_parameter):
            for child_i, child in enumerate(last_parameter.children):
                # Handle *args and **kwargs parameters.
                if not isinstance(child, sphinx.addnodes.desc_sig_operator):
                    del last_parameter[child_i + 1 :]
                    if not _must_shorten():
                        return
                    break

        # Elide last parameter entirely
        del parameterlist.children[next_parameter_index]
        if not added_ellipsis:
            added_ellipsis = True
            ellipsis_node = sphinx.addnodes.desc_sig_punctuation("", "...")
            # When using the `sphinx_immaterial.apidoc.format_signatures`
            # extension, replace the text of this node to make it valid Python
            # syntax.
            ellipsis_node["munged_text_for_formatting"] = "___"
            param = sphinx.addnodes.desc_parameter()
            param += ellipsis_node
            parameterlist += param


class _MemberDocumenterEntry(NamedTuple):
    """Represents a member of some outer scope (module/class) to document."""

    documenter: sphinx.ext.autodoc.Documenter
    is_attr: bool
    name: str
    """Member name within parent, e.g. class member name."""

    full_name: str
    """Full name under which to document the member.

    For example, "modname.ClassName.method".
    """

    parent_canonical_full_name: str

    overload: Optional[ParsedOverload] = None

    is_inherited: bool = False
    """Indicates whether this is an inherited member."""

    subscript: bool = False
    """Whether this is a "subscript" method to be shown with [] instead of ()."""

    type_param_substitutions: Optional[type_param_utils.TypeParamSubstitutions] = None

    @property
    def overload_suffix(self):
        if self.overload and self.overload.overload_id:
            return f"({self.overload.overload_id})"
        return ""

    @property
    def toc_title(self):
        return self.name + self.overload_suffix


class _ApiEntityMemberReference(NamedTuple):
    name: str
    canonical_object_name: str
    parent_canonical_object_name: str
    inherited: bool
    siblings: List["_ApiEntityMemberReference"]
    type_param_substitutions: Optional[type_param_utils.TypeParamSubstitutions]


@dataclasses.dataclass
class _ApiEntity:
    canonical_full_name: str
    objtype: str
    directive: str
    overload_id: str

    @property
    def canonical_object_name(self):
        return self.canonical_full_name + self.overload_suffix

    @property
    def object_name(self):
        return self.documented_full_name + self.overload_suffix

    @property
    def overload_suffix(self) -> str:
        overload_id = self.overload_id
        return f"({overload_id})" if overload_id else ""

    signatures: List[str]
    options: Dict[str, str]
    content: List[str]
    group_name: str
    order: Optional[int]
    subscript: bool

    members: List[_ApiEntityMemberReference]
    """Members of this entity."""

    parents: List[_ApiEntityMemberReference]
    """Parents that reference this entity as a member.

    Inverse of `members`."""

    docname: str = ""

    documented_full_name: str = ""
    documented_name: str = ""
    top_level: bool = False

    base_classes: Optional[List[str]] = None
    """List of base classes, as rST cross references."""

    siblings: Optional[Dict[str, bool]] = None
    """List of siblings that should be documented as aliases.

    The key is the canonical_object_name of the sibling.  The value is always `True`."""

    primary_entity: bool = True
    """Indicates if this is the primary sibling and should be documented."""

    type_params: Optional[Tuple[type_param_utils.TypeParam, ...]] = None
    parent_type_params: Optional[Tuple[str, Tuple[type_param_utils.TypeParam, ...]]] = (
        None
    )


def _is_constructor_name(name: str) -> bool:
    return name in ("__init__", "__new__", "__class_getitem__")


class _ApiData:
    entities: Dict[str, _ApiEntity]
    top_level_groups: Dict[str, List[_ApiEntityMemberReference]]

    def __init__(self):
        self.entities = {}
        self.top_level_groups = {}

    def get_name_for_signature(
        self, entity: _ApiEntity, member: Optional[_ApiEntityMemberReference]
    ) -> str:
        if member is not None:
            assert member.canonical_object_name == entity.canonical_object_name
            # Get name for summary
            if _is_constructor_name(member.name):
                parent_entity = self.entities.get(member.parent_canonical_object_name)
                if parent_entity is not None and parent_entity.objtype == "class":
                    # Display as the parent class name.
                    return parent_entity.documented_name
            # Display as the member name
            return member.name
        full_name = entity.documented_full_name
        if _is_constructor_name(entity.documented_name):
            full_name = full_name[: -len(entity.documented_name) - 1]
        module = entity.options.get("module")
        if module is not None and full_name.startswith(module + "."):
            # Strip module name, since it is specified separately.
            full_name = full_name[len(module) + 1 :]
        return full_name

    def sort_members(
        self, members: List[_ApiEntityMemberReference], alphabetical=False
    ):
        def get_key(member: _ApiEntityMemberReference):
            member_entity = self.entities[member.canonical_object_name]
            order = member_entity.order or 0
            if alphabetical:
                return (order, member.name.lower(), member.name)
            return order

        members.sort(key=get_key)


def _ensure_module_name_in_signature(signode: sphinx.addnodes.desc_signature) -> None:
    """Ensures non-summary objects are documented with the module name.

    Sphinx by default excludes the module name from class members, and does not
    provide an option to override that.  Since we display all objects on separate
    pages, we want to include the module name for clarity.

    :param signode: Signature to modify in place.
    """
    for node in signode.findall(condition=sphinx.addnodes.desc_addname):
        modname = signode.get("module")
        if modname and not node.astext().startswith(modname + "."):
            node.insert(0, docutils.nodes.Text(modname + "."))
        break


def _get_group_name(
    default_groups: List[Tuple[re.Pattern, str]], entity: _ApiEntity
) -> str:
    """Returns a default group name for an entry.

    This is used if the group name is not explicitly specified via "Group:" in the
    docstring.

    :param default_groups: Default group associations.
    :param entity: Entity to document.
    :returns: The group name.
    """
    s = f"{entity.objtype}:{entity.documented_full_name}"
    s_canonical = f"{entity.objtype}:{entity.canonical_full_name}"
    group = "Public members"
    for pattern, default_group in default_groups:
        if (
            pattern.fullmatch(s) is not None
            or pattern.fullmatch(s_canonical) is not None
        ):
            group = default_group
    return group


def _get_order(default_order: List[Tuple[re.Pattern, int]], entity: _ApiEntity) -> int:
    """Returns a default order value for an entry.

    This is used if the order is not explicitly specified via "Order:" in the
    docstring.

    :param default_order: Default order associations.
    :param entity: Entity to document.
    :returns: The order.
    """
    s = f"{entity.objtype}:{entity.documented_full_name}"
    order = 0
    for pattern, order_value in default_order:
        if pattern.fullmatch(s) is not None:
            order = order_value
    return order


def _mark_subscript_parameterlist(signode: sphinx.addnodes.desc_signature) -> None:
    """Modifies an object description to display as a "subscript method".

    A "subscript method" is a property that defines __getitem__ and is intended to
    be treated as a method invoked using [] rather than (), in order to allow
    subscript syntax like ':'.

    :param node: Signature to modify in place.
    """
    for sub_node in signode.findall(condition=sphinx.addnodes.desc_parameterlist):
        sub_node["parens"] = ("[", "]")


def _clean_init_signature(signode: sphinx.addnodes.desc_signature) -> None:
    """Modifies an object description of an __init__ method.

    Removes the return type (always None) and the self parameter (since these
    methods are displayed as the class name, without showing __init__).

    :param signode: Signature to modify in place.
    """
    # Remove first parameter.
    for param in signode.findall(condition=sphinx.addnodes.desc_parameter):
        if param.children[0].astext() == "self":
            param.parent.remove(param)
        break

    # Remove return type.
    for node in signode.findall(condition=sphinx.addnodes.desc_returns):
        node.parent.remove(node)


def _clean_class_getitem_signature(signode: sphinx.addnodes.desc_signature) -> None:
    """Modifies an object description of a __class_getitem__ method.

    Removes the `static` prefix since these methods are shown using the class
    name (i.e. as "subscript" constructors).

    :param signode: Signature to modify in place.

    """
    # Remove `static` prefix
    for prefix in signode.findall(condition=sphinx.addnodes.desc_annotation):
        prefix.parent.remove(prefix)
        break


def _insert_parent_type_params(
    env: sphinx.environment.BuildEnvironment,
    signode: sphinx.addnodes.desc_signature,
    parent_symbol: str,
    parent_type_params: tuple[type_param_utils.TypeParam, ...],
    is_constructor: bool,
) -> bool:
    def _make_type_list_node() -> docutils.nodes.Element:
        tp_list = type_param_utils.stringify_type_params(parent_type_params)
        tp_list_node: docutils.nodes.Element = (
            sphinx.domains.python._annotations._parse_type_list(tp_list, env)
        )
        for desc_param_node in tp_list_node.findall(
            condition=sphinx.addnodes.desc_type_parameter
        ):
            desc_param_node[TYPE_PARAM_SYMBOL_PREFIX_ATTR_KEY] = parent_symbol

        if env.app.builder.name == "latex":
            # LaTeX builder can't handle additional type parameter lists nodes
            # inside a signature. Convert to text elements.
            #
            # https://github.com/sphinx-doc/sphinx/issues/12543
            converted = docutils.nodes.inline()
            converted.append(sphinx.addnodes.desc_sig_punctuation("[", "["))
            for i, p in enumerate(
                cast(list[sphinx.addnodes.desc_type_parameter], tp_list_node.children)
            ):
                if i != 0:
                    converted.append(sphinx.addnodes.desc_sig_punctuation(", ", ", "))
                p_new = docutils.nodes.inline()
                p_new["classes"] = p["classes"]
                p_new.extend(p.children)
                converted.append(p_new)
            converted.append(sphinx.addnodes.desc_sig_punctuation("]", "]"))
            tp_list_node = converted

        # Mark as parent type parameter list for detection by `format_signatures`.
        tp_list_node["sphinx_immaterial_parent_type_parameter_list"] = True
        return tp_list_node

    if is_constructor:
        for node in signode.findall(sphinx.addnodes.desc_name):
            break
        else:
            return False
        node.parent.insert(node.parent.index(node) + 1, _make_type_list_node())
        return True

    prev_name_node = None
    for node in signode.findall():
        if isinstance(node, sphinx.addnodes.desc_addname):
            prev_name_node = node
        elif isinstance(node, sphinx.addnodes.desc_name):
            break
    else:
        return False

    if prev_name_node is None:
        return False

    index = prev_name_node.parent.index(prev_name_node)
    prev_name_text = prev_name_node.astext().rstrip(".")
    prev_name_node.replace_self(
        sphinx.addnodes.desc_addname(prev_name_text, prev_name_text)
    )
    prev_name_node.parent.insert(
        index + 1,
        [
            _make_type_list_node(),
            sphinx.addnodes.desc_addname(".", "."),
        ],
    )
    return True


def _get_api_data(
    env: sphinx.environment.BuildEnvironment,
) -> _ApiData:
    return getattr(env.app, "_sphinx_immaterial_python_apigen_data")


def _generate_entity_desc_node(
    env: sphinx.environment.BuildEnvironment,
    entity: _ApiEntity,
    state: docutils.parsers.rst.states.RSTState,
    member: Optional[_ApiEntityMemberReference] = None,
    callback=None,
) -> sphinx.addnodes.desc:
    api_data = _get_api_data(env)

    summary = member is not None

    def object_description_transform(
        app: sphinx.application.Sphinx,
        domain: str,
        objtype: str,
        contentnode: sphinx.addnodes.desc_content,
    ) -> None:
        env = app.env
        assert env is not None

        obj_desc = contentnode.parent
        assert isinstance(obj_desc, sphinx.addnodes.desc)
        signodes = cast(List[sphinx.addnodes.desc_signature], obj_desc[:-1])
        if not signodes:
            return

        for signode in signodes:
            fullname = signode["fullname"]
            modname = signode["module"]
            object_name = (modname + "." if modname else "") + fullname
            if object_name != entity.object_name:
                # This callback may be invoked for additional members
                # documented within the body of `entry`, but we don't want
                # to transform them here.
                return
            assert isinstance(signode, sphinx.addnodes.desc_signature)
            if entity.subscript:
                _mark_subscript_parameterlist(signode)

            if entity.documented_name in ("__init__", "__new__"):
                _clean_init_signature(signode)
            if entity.documented_name == "__class_getitem__":
                _clean_class_getitem_signature(signode)

            if summary:
                obj_desc["classes"].append("summary")
                assert app.env is not None
                _summarize_signature(app.env, signode)
            elif entity.parent_type_params:
                # Insert additional type parameters
                if not _insert_parent_type_params(
                    app.env,
                    signode,
                    entity.parent_type_params[0],
                    entity.parent_type_params[1],
                    is_constructor=_is_constructor_name(entity.documented_name),
                ):
                    logger.warning(
                        "Failed to insert parent type parameters %r",
                        entity.parent_type_params[1],
                        location=signode,
                    )

            base_classes = entity.base_classes
            if base_classes:
                signode += sphinx.addnodes.desc_sig_punctuation("", "(")
                for i, base_class in enumerate(base_classes):
                    base_entity = api_data.entities.get(base_class)
                    if base_entity is not None:
                        base_class = base_entity.object_name
                    if i != 0:
                        signode += sphinx.addnodes.desc_sig_punctuation("", ",")
                        signode += sphinx.addnodes.desc_sig_space()
                    signode += _parse_annotation(base_class, env)
                signode += sphinx.addnodes.desc_sig_punctuation("", ")")

            if not summary:
                _ensure_module_name_in_signature(signode)

        if callback is not None:
            callback(contentnode)

    listener_id = env.app.connect(
        "object-description-transform", object_description_transform, priority=999
    )
    content = entity.content
    options = dict(entity.options)
    options["nonodeid"] = ""
    all_members: List[Optional[_ApiEntityMemberReference]]
    if member is not None:
        all_members = cast(
            List[Optional[_ApiEntityMemberReference]], [member] + member.siblings
        )
        all_entities = [
            api_data.entities[cast(_ApiEntityMemberReference, m).canonical_object_name]
            for m in all_members
        ]
    else:
        all_entities = [
            entity,
            *(api_data.entities[s] for s in (entity.siblings or {})),
        ]
        all_members = [None] * len(all_entities)

    options["object-ids"] = json.dumps(
        [e.object_name for e in all_entities for _ in e.signatures]
    )
    if summary:
        content = _summarize_rst_content(content)
        options["noindex"] = ""
    # Avoid "canonical" option because it results in duplicate object warnings
    # when combined with multiple signatures that produce different object ids.
    #
    # Instead, the canonical aliases are handled separately below.
    options.pop("canonical", None)
    try:
        with apigen_utils.save_rst_defaults(env):
            rst_input = docutils.statemachine.StringList()
            sphinx_utils.append_multiline_string_to_stringlist(
                rst_input,
                ".. highlight-push::\n\n"
                + env.config.python_apigen_rst_prolog
                + "\n\n",
                "<python_apigen_rst_prolog>",
                -2,
            )

            signatures: List[str] = []
            for e, m in zip(all_entities, all_members):
                name = api_data.get_name_for_signature(e, m)
                unnamed_signatures = e.signatures
                if m is not None and m.type_param_substitutions:
                    unnamed_signatures = [
                        type_param_utils.substitute_type_params(
                            sig, m.type_param_substitutions
                        )
                        for sig in unnamed_signatures
                    ]
                signatures.extend(name + sig for sig in unnamed_signatures)

            if (
                (m := all_members[0]) is not None
                and "type" in options
                and m.type_param_substitutions
            ):
                options["type"] = type_param_utils.substitute_type_params(
                    options["type"], m.type_param_substitutions
                )

            sphinx_utils.append_directive_to_stringlist(
                rst_input,
                entity.directive,
                signatures=signatures,
                content="\n".join(content),
                source_path=entity.object_name,
                source_line=0,
                options=options,
            )
            sphinx_utils.append_multiline_string_to_stringlist(
                rst_input,
                "\n\n"
                + env.config.python_apigen_rst_epilog
                + "\n\n.. highlight-pop::\n\n",
                "<python_apigen_rst_epilog>",
                -2,
            )
            nodes = [
                x
                for x in sphinx_utils.parse_rst(
                    state=state,
                    text=rst_input,
                )
                if isinstance(x, sphinx.addnodes.desc)
            ]
    finally:
        env.app.disconnect(listener_id)

    if len(nodes) != 1:
        raise ValueError("Failed to document entity: %r" % (entity.object_name,))
    node = nodes[0]

    if not summary:
        py = cast(PythonDomain, env.get_domain("py"))

        for e in all_entities:
            py.objects.setdefault(
                e.canonical_object_name,
                py.objects[e.object_name]._replace(aliased=True),
            )

    return node


def _generate_entity_summary(
    env: sphinx.environment.BuildEnvironment,
    member: _ApiEntityMemberReference,
    state: docutils.parsers.rst.states.RSTState,
    include_in_toc: bool,
) -> sphinx.addnodes.desc:
    api_data = _get_api_data(env)
    entity = api_data.entities[member.canonical_object_name]
    objdesc = _generate_entity_desc_node(
        env=env, entity=entity, member=member, state=state
    )
    for sig_node in cast(List[sphinx.addnodes.desc_signature], objdesc.children[:-1]):
        # Insert a link around the `desc_name` field
        for sub_node in sig_node.findall(condition=sphinx.addnodes.desc_name):
            if include_in_toc:
                sub_node["classes"].append("pseudo-toc-entry")
            xref_node = sphinx.addnodes.pending_xref(
                "",
                sub_node.deepcopy(),
                refdomain="py",
                reftype="obj",
                reftarget=entity.object_name,
                refwarn=True,
                refexplicit=True,
            )
            sub_node.replace_self(xref_node)
            break
        # Only mark first signature as a `pseudo-toc-entry`.
        include_in_toc = False
    return objdesc


def _generate_group_summary(
    env: sphinx.environment.BuildEnvironment,
    members: List[_ApiEntityMemberReference],
    state: docutils.parsers.rst.states.RSTState,
    notoc: Optional[bool] = None,
):
    data = _get_api_data(env)

    nodes: List[docutils.nodes.Node] = []
    toc_entries: List[Tuple[str, str]] = []

    for member in members:
        member_entity = data.entities[member.canonical_object_name]
        include_in_toc = True
        if notoc is True:
            include_in_toc = False
        elif member is not member_entity.parents[0]:
            include_in_toc = False
        node = _generate_entity_summary(
            env=env, member=member, state=state, include_in_toc=include_in_toc
        )
        if node is None:
            continue
        nodes.append(node)

        if include_in_toc:
            toc_entries.append(
                (member.name + member_entity.overload_suffix, member_entity.docname)
            )

    nodes.extend(
        sphinx_utils.make_toctree_node(
            state,
            toc_entries,
            options={"hidden": True},
            source_path=__name__,
        )
    )
    return nodes


def _add_group_summary(
    env: sphinx.environment.BuildEnvironment,
    contentnode: docutils.nodes.Element,
    sections: Dict[str, docutils.nodes.section],
    group_name: str,
    members: List[_ApiEntityMemberReference],
    state: docutils.parsers.rst.states.RSTState,
) -> None:
    group_id = docutils.nodes.make_id(group_name)
    section = sections.get(group_id)
    if section is None:
        section = docutils.nodes.section()
        section["ids"].append(group_id)
        title = docutils.nodes.title("", group_name)
        section += title
        contentnode += section
        sections[group_id] = section

    section.extend(_generate_group_summary(env=env, members=members, state=state))


def _merge_summary_nodes_into(
    env: sphinx.environment.BuildEnvironment,
    entity: _ApiEntity,
    contentnode: docutils.nodes.Element,
    state: docutils.parsers.rst.states.RSTState,
) -> None:
    """Merges the member summary into `contentnode`.

    Members are organized into groups.  The group is either specified explicitly
    by a `Group:` field in the docstring, or determined automatically by
    `_get_group_name`.  If there is an existing section, the member summary is
    appended to it.  Otherwise, a new section is created.

    :param contentnode: The existing container to which the member summaries will be
        added.  If `contentnode` contains sections, those sections correspond to
        group names.
    """

    sections: Dict[str, docutils.nodes.section] = {}
    for section in contentnode.findall(condition=docutils.nodes.section):
        if section["ids"]:
            sections[section["ids"][0]] = section

    # Maps group name to the list of members.
    groups: Dict[str, List[_ApiEntityMemberReference]] = {}

    entities = _get_api_data(env).entities
    for member in entity.members:
        member_entity = entities[member.canonical_object_name]
        groups.setdefault(member_entity.group_name, []).append(member)

    for group_name, members in groups.items():
        _add_group_summary(
            env=env,
            contentnode=contentnode,
            sections=sections,
            group_name=group_name,
            members=members,
            state=state,
        )


class PythonApigenEntityPageDirective(sphinx.util.docutils.SphinxDirective):
    """Documents an entity and summarizes its members, if applicable."""

    has_content = False
    final_argument_whitespace = True
    required_arguments = 1
    optional_arguments = 0

    def run(self) -> List[docutils.nodes.Node]:
        entities = _get_api_data(self.env).entities
        object_name = self.arguments[0]
        entity = entities.get(object_name)
        if entity is None:
            logger.error(
                "Undefined Python entity: %r", object_name, location=self.get_location()
            )
            return []

        objdesc = _generate_entity_desc_node(
            self.env,
            entity,
            state=self.state,
            callback=lambda contentnode: _merge_summary_nodes_into(
                env=self.env,
                entity=entity,
                contentnode=contentnode,
                state=self.state,
            ),
        )

        # Wrap in a section
        section = docutils.nodes.section()
        section["ids"].append("")
        # Sphinx treates the first child of a `section` node as the title,
        # regardless of its type.  We use a comment node to avoid adding a title
        # that would be redundant with the object description.
        section += docutils.nodes.comment("", entity.object_name)
        section += objdesc
        return [section]


class PythonApigenTopLevelGroupDirective(sphinx.util.docutils.SphinxDirective):
    """Summarizes the members of a top-level group."""

    has_content = False
    final_argument_whitespace = True
    required_arguments = 1
    optional_arguments = 0

    option_spec = {
        "notoc": docutils.parsers.rst.directives.flag,
    }

    def run(self) -> List[docutils.nodes.Node]:
        env = self.env
        data = _get_api_data(env)
        top_level_groups = data.top_level_groups

        group_id = docutils.nodes.make_id(self.arguments[0])
        members = top_level_groups.get(group_id)

        if members is None:
            logger.warning(
                "No top-level Python API group named: %r, valid groups are: %r",
                group_id,
                list(data.top_level_groups.keys()),
                location=self.state_machine.get_source_and_line(self.lineno),
            )
            return []
        return _generate_group_summary(
            env=env, members=members, state=self.state, notoc="notoc" in self.options
        )


class PythonApigenEntitySummaryDirective(sphinx.util.docutils.SphinxDirective):
    """Generates a summary/link to a Python entity."""

    has_content = False
    final_argument_whitespace = True
    required_arguments = 1
    optional_arguments = 0

    option_spec = {
        "notoc": docutils.parsers.rst.directives.flag,
    }

    def run(self) -> List[docutils.nodes.Node]:
        env = self.env
        data = _get_api_data(env)
        object_name = self.arguments[0]
        entity = data.entities.get(object_name)
        if entity is None:
            logger.warning(
                "No Python entity named: %r",
                object_name,
                location=self.state_machine.get_source_and_line(self.lineno),
            )
            return []
        return _generate_group_summary(
            env=env,
            members=[entity.parents[0]],
            state=self.state,
            notoc="notoc" in self.options,
        )


class _FakeBridge(sphinx.ext.autodoc.directive.DocumenterBridge):
    def __init__(
        self,
        env: sphinx.environment.BuildEnvironment,
        tab_width: int,
        extra_options: dict,
    ) -> None:
        settings = docutils.parsers.rst.states.Struct(tab_width=tab_width)
        document = docutils.parsers.rst.states.Struct(settings=settings)
        state = docutils.parsers.rst.states.Struct(document=document)
        options = sphinx.ext.autodoc.Options()
        options["undoc-members"] = True
        options["class-doc-from"] = "class"
        options.update(extra_options)
        super().__init__(
            env=env,
            reporter=sphinx.util.docutils.NullReporter(),
            options=options,
            lineno=0,
            state=state,
        )


_EXCLUDED_SPECIAL_MEMBERS = frozenset(
    [
        "__module__",
        "__abstractmethods__",
        "__dict__",
        "__weakref__",
        "__class__",
        "__base__",
        # Exclude pickling members since they are never documented.
        "__getstate__",
        "__setstate__",
    ]
)


def _create_documenter(
    env: sphinx.environment.BuildEnvironment,
    documenter_cls: Type[sphinx.ext.autodoc.Documenter],
    name: str,
    tab_width: int = 8,
) -> sphinx.ext.autodoc.Documenter:
    """Creates a documenter for the given full object name.

    Since we are using the documenter independent of any autodoc directive, we use
    a `_FakeBridge` as the documenter bridge, similar to the strategy used by
    `sphinx.ext.autosummary`.

    :param env: Sphinx build environment.
    :param documenter_cls: Documenter class to use.
    :param name: Full object name, e.g. `my_module.MyClass.my_function`.
    :param tab_width: Tab width setting to use when parsing docstrings.
    :returns: The documenter object.
    """
    extra_options = {}
    if documenter_cls.objtype == "class":
        extra_options["special-members"] = sphinx.ext.autodoc.ALL
    bridge = _FakeBridge(env, tab_width=tab_width, extra_options=extra_options)
    documenter = documenter_cls(bridge, name)
    assert documenter.parse_name()
    assert documenter.import_object()
    try:
        documenter.analyzer = sphinx.pycode.ModuleAnalyzer.for_module(
            documenter.get_real_modname()
        )
        # parse right now, to get PycodeErrors on parsing (results will
        # be cached anyway)
        documenter.analyzer.find_attr_docs()
    except sphinx.pycode.PycodeError:
        # no source file -- e.g. for builtin and C modules
        documenter.analyzer = None  # type: ignore[assignment]
    return documenter


def _get_member_documenter(
    parent: sphinx.ext.autodoc.Documenter,
    member_name: str,
    member_value: Any,
    is_attr: bool,
) -> Optional[sphinx.ext.autodoc.Documenter]:
    """Creates a documenter for the given member.

    :param parent: Parent documenter.
    :param member_name: Name of the member.
    :param member_value: Value of the member.
    :param is_attr: Whether the member is an attribute.
    :returns: The documenter object.
    """
    classes = [
        cls
        for cls in parent.documenters.values()
        if cls.can_document_member(member_value, member_name, is_attr, parent)
    ]
    if not classes:
        return None
    # prefer the documenter with the highest priority
    classes.sort(key=lambda cls: cls.priority)
    full_mname = parent.modname + "::" + ".".join(parent.objpath + [member_name])
    documenter = _create_documenter(
        env=parent.env,
        documenter_cls=classes[-1],
        name=full_mname,
        tab_width=parent.directive.state.document.settings.tab_width,
    )
    return documenter


def _include_member(member_name: str, member_value: Any, is_attr: bool) -> bool:
    """Determines whether a member should be documented.

    :param member_name: Name of the member.
    :param member_value: Value of the member.
    :param is_attr: Whether the member is an attribute.
    :returns: True if the member should be documented.
    """
    del is_attr
    if member_name == "__init__":
        doc = getattr(member_value, "__doc__", None)
        if isinstance(doc, str) and doc.startswith("Initialize self. "):
            return False
    elif member_name in ("__hash__", "__iter__"):
        if member_value is None:
            return False
    return True


def _get_subscript_method(
    parent_documenter: sphinx.ext.autodoc.Documenter, entry: _MemberDocumenterEntry
) -> Any:
    """Checks for a property that defines a subscript method.

    A subscript method is a property like `Class.vindex` where `fget` has a return
    type of `Class._Vindex`, which is a class type.

    :param parent_documenter: Parent documenter for `entry`.
    :param entry: Entry to check.
    :returns: The type object (e.g. `Class._Vindex`) representing the subscript
        method, or None if `entry` does not define a subscript method.
    """
    if not isinstance(entry.documenter, sphinx.ext.autodoc.PropertyDocumenter):
        return None
    retann = entry.documenter.retann
    if not retann:
        return None

    config = entry.documenter.config
    pattern = config.python_apigen_subscript_method_types
    match = pattern.fullmatch(retann)
    if not match:
        return None

    # Attempt to import value
    try:
        mem_documenter = _create_documenter(
            env=entry.documenter.env,
            documenter_cls=sphinx.ext.autodoc.ClassDocumenter,
            name=retann,
        )
        mem = mem_documenter.object
    except ImportError:
        return None
    if not mem:
        return None
    getitem = getattr(mem, "__getitem__", None)
    if getitem is None:
        return None

    return mem


def _transform_member(
    parent_documenter: sphinx.ext.autodoc.Documenter, entry: _MemberDocumenterEntry
) -> Iterator[_MemberDocumenterEntry]:
    """Converts an individual member into a sequence of members to document.

    :param parent_documenter: The parent documenter.
    :param entry: The original entry to document.  For most entries we simply yield the
        entry unmodified.  For entries that correspond to subscript methods,
        though, we yield the __getitem__ member (and __setitem__, if applicable)
        separately.
    :returns: Iterator over modified entries to document.
    """
    if entry.name == "__class_getitem__":
        entry = entry._replace(subscript=True)

    mem = _get_subscript_method(parent_documenter, entry)
    if mem is None:
        yield entry
        return
    retann = entry.documenter.retann

    for suffix in ("__getitem__", "__setitem__"):
        method = getattr(mem, suffix, None)
        if method is None:
            continue
        import_name = f"{retann}.{suffix}"
        if import_name.startswith(entry.documenter.modname + "."):
            import_name = (
                entry.documenter.modname
                + "::"
                + import_name[len(entry.documenter.modname) + 1 :]
            )
        new_documenter = _create_documenter(
            env=parent_documenter.env,
            documenter_cls=sphinx.ext.autodoc.MethodDocumenter,
            name=import_name,
            tab_width=parent_documenter.directive.state.document.settings.tab_width,
        )
        if suffix != "__getitem__":
            new_member_name = f"{entry.name}.{suffix}"
            full_name = f"{entry.full_name}.{suffix}"
            subscript = False
        else:
            new_member_name = f"{entry.name}"
            full_name = entry.full_name
            subscript = True

        yield _MemberDocumenterEntry(
            documenter=new_documenter,
            name=new_member_name,
            is_attr=False,
            full_name=full_name,
            parent_canonical_full_name=entry.parent_canonical_full_name,
            subscript=subscript,
        )


def _prepare_documenter_docstring(entry: _MemberDocumenterEntry) -> None:
    """Initializes `entry.documenter` with the correct docstring.

    This overrides the docstring based on `entry.overload` if applicable.

    This must be called before using `entry.documenter`.

    :param entry: Entry to prepare.
    """

    if entry.overload and (
        entry.overload.overload_id is not None
        or
        # For methods, we don't need `ModuleAnalyzer`, so it is safe to always
        # override the normal mechanism of obtaining the docstring.
        # Additionally, for `__init__` and `__new__` we need to specify the
        # docstring explicitly to work around
        # https://github.com/sphinx-doc/sphinx/pull/9518.
        isinstance(entry.documenter, sphinx.ext.autodoc.MethodDocumenter)
    ):
        # Force autodoc to use the overload-specific signature.  autodoc already
        # has an internal mechanism for overriding the docstrings based on the
        # `_new_docstrings` member.
        tab_width = entry.documenter.directive.state.document.settings.tab_width
        setattr(
            entry.documenter,
            "_new_docstrings",
            [
                sphinx.util.docstrings.prepare_docstring(
                    entry.overload.doc or "", tabsize=tab_width
                )
            ],
        )
    else:
        # Force autodoc to obtain the docstring through its normal mechanism,
        # which includes the "ModuleAnalyzer" for reading docstrings of
        # variables/attributes that are only contained in the source code.
        setattr(entry.documenter, "_new_docstrings", None)

    # Workaround for https://github.com/sphinx-doc/sphinx/pull/9518
    orig_get_doc = entry.documenter.get_doc

    def get_doc(*args, **kwargs) -> List[List[str]]:
        doc_strings = getattr(entry.documenter, "_new_docstrings", None)
        if doc_strings is not None:
            return doc_strings
        return orig_get_doc(*args, **kwargs)  # type: ignore

    entry.documenter.get_doc = get_doc  # type: ignore[assignment]


def _is_conditionally_documented_entry(entry: _MemberDocumenterEntry):
    if entry.name in _UNCONDITIONALLY_DOCUMENTED_MEMBERS:
        return False
    return sphinx.ext.autodoc.special_member_re.match(entry.name)


def _get_member_overloads(
    entry: _MemberDocumenterEntry,
) -> Iterator[_MemberDocumenterEntry]:
    """Returns the list of overloads for a given entry."""

    if entry.name in _EXCLUDED_SPECIAL_MEMBERS:
        return

    overloads = _get_overloads_from_documenter(entry.documenter)
    for overload in overloads:
        # Shallow copy the documenter.  Certain methods on the documenter mutate it,
        # and we don't want those mutations to affect other overloads.
        documenter_copy = copy.copy(entry.documenter)
        documenter_copy.options = documenter_copy.options.copy()
        new_entry = entry._replace(
            overload=overload,
            documenter=documenter_copy,
        )
        if _is_conditionally_documented_entry(new_entry):
            # Only document this entry if it has a docstring.
            _prepare_documenter_docstring(new_entry)
            new_entry.documenter.format_signature()
            doc = new_entry.documenter.get_doc()
            if not doc:
                continue
            if not any(x for x in doc):
                # No docstring, skip.
                continue

            new_entry = entry._replace(
                overload=overload, documenter=copy.copy(entry.documenter)
            )

        yield new_entry


def _get_documenter_direct_members(
    documenter: sphinx.ext.autodoc.Documenter,
    canonical_full_name: str,
) -> Iterator[_MemberDocumenterEntry]:
    """Returns the sequence of direct members to document.

    The order is mostly determined by the definition order.

    This excludes inherited members.

    :param documenter: Documenter for which to obtain members.
    :returns: Iterator over members to document.
    """
    if not isinstance(
        documenter,
        (sphinx.ext.autodoc.ClassDocumenter, sphinx.ext.autodoc.ModuleDocumenter),
    ):
        # Only classes and modules have members.
        return

    members_check_module, members = documenter.get_object_members(want_all=True)
    del members_check_module
    if members:
        try:
            # get_object_members does not preserve definition order, but __dict__ does
            # in Python 3.6 and later.
            member_dict = sphinx.util.inspect.safe_getattr(
                documenter.object, "__dict__"
            )
            member_order = {k: i for i, k in enumerate(member_dict.keys())}

            if sphinx.version_info >= (7, 0):

                def member_sort_key(entry):
                    return member_order.get(entry.__name__, float("inf"))

            else:

                def member_sort_key(entry):
                    return member_order.get(entry[0], float("inf"))

            members.sort(key=member_sort_key)
        except AttributeError:
            pass
    filtered_members = [
        x
        for x in documenter.filter_members(members, want_all=True)
        if _include_member(*x)
    ]
    for member_name, member_value, is_attr in filtered_members:
        member_documenter = _get_member_documenter(
            parent=documenter,
            member_name=member_name,
            member_value=member_value,
            is_attr=is_attr,
        )
        if member_documenter is None:
            continue
        full_name = f"{documenter.fullname}.{member_name}"
        entry = _MemberDocumenterEntry(
            cast(sphinx.ext.autodoc.Documenter, member_documenter),
            is_attr,
            parent_canonical_full_name=canonical_full_name,
            name=member_name,
            full_name=full_name,
        )
        for transformed_entry in _transform_member(documenter, entry):
            yield from _get_member_overloads(transformed_entry)


def _get_documenter_members(
    app: sphinx.application.Sphinx,
    documenter: sphinx.ext.autodoc.Documenter,
    canonical_full_name: str,
) -> Iterator[_MemberDocumenterEntry]:
    """Returns the sequence of members to document, including inherited members.

    :param documenter: Parent documenter for which to find members.
    :returns: Iterator over members to document.
    """
    seen_members: Set[str] = set()

    def _get_unseen_members(
        members: Iterator[_MemberDocumenterEntry],
        is_inherited: bool,
        type_param_substitutions: Optional[type_param_utils.TypeParamSubstitutions],
    ) -> Iterator[_MemberDocumenterEntry]:
        for member in members:
            overload_name = member.toc_title
            if overload_name in seen_members:
                continue
            seen_members.add(overload_name)
            yield member._replace(
                is_inherited=is_inherited,
                type_param_substitutions=type_param_substitutions,
            )

    yield from _get_unseen_members(
        _get_documenter_direct_members(
            documenter, canonical_full_name=canonical_full_name
        ),
        is_inherited=False,
        type_param_substitutions=None,
    )

    if documenter.objtype != "class":
        return

    base_class_type_param_substitutions = (
        type_param_utils.get_base_class_type_param_substitutions(documenter.object)
    )

    for cls in inspect.getmro(documenter.object):
        if cls is documenter.object:
            continue
        skip_user = app.emit_firstresult("python-apigen-skip-base", object, cls)
        if skip_user is True:
            continue
        if skip_user is None:
            if cls.__module__ in ("builtins", "pybind11_builtins"):
                continue
            if cls is typing.Generic:
                continue
        class_name = f"{cls.__module__}::{cls.__qualname__}"
        parent_canonical_full_name = f"{cls.__module__}.{cls.__qualname__}"
        try:
            superclass_documenter = _create_documenter(
                env=documenter.env,
                documenter_cls=sphinx.ext.autodoc.ClassDocumenter,
                name=class_name,
                tab_width=documenter.directive.state.document.settings.tab_width,
            )
            yield from _get_unseen_members(
                _get_documenter_direct_members(
                    superclass_documenter,
                    canonical_full_name=parent_canonical_full_name,
                ),
                is_inherited=True,
                type_param_substitutions=base_class_type_param_substitutions.get(cls),
            )
        except Exception as e:
            logger.warning(
                "Cannot obtain documenter for base class %r of %r: %r",
                cls,
                documenter.fullname,
                e,
            )


class SplitAutodocRstOutput(NamedTuple):
    directive: str
    options: Dict[str, str]
    content: List[str]
    group_name: Optional[str]
    order: Optional[int]


def _split_autodoc_rst_output(
    rst_strings: docutils.statemachine.StringList,
) -> SplitAutodocRstOutput:
    m = re.fullmatch(r"\.\. ([^:]+:[^:]+):: (.*)", rst_strings[1], re.DOTALL)
    assert m is not None, repr(rst_strings[1])
    directive = m.group(1)
    signatures = [m.group(2)]
    signature_prefix = " " * (6 + len(directive))
    i = 2
    while i < len(rst_strings):
        line = rst_strings[i]
        if line.startswith(signature_prefix):
            signatures.append(line[len(signature_prefix) :])
            i += 1
        else:
            break
    options: Dict[str, str] = {}
    while i < len(rst_strings):
        line = rst_strings[i]
        m = re.fullmatch(r"   :([^:]+):(.*)", line, re.DOTALL)
        if m is None:
            break
        options[m.group(1)] = m.group(2).strip()
        i += 1
    assert i < len(rst_strings)
    assert rst_strings[i] == ""

    i += 1

    while i < len(rst_strings) and not rst_strings[i].strip():
        i += 1

    content_start_line = i

    def extract_field(name: str) -> Tuple[Optional[str], Optional[Tuple[str, int]]]:
        field_prefix = f"   :{name}:"
        for i in range(content_start_line, len(rst_strings)):
            line = rst_strings[i]
            if not line.startswith(field_prefix):
                continue
            value = line[len(field_prefix) :].strip()
            location = rst_strings.items[i]
            del rst_strings[i]
            return value, location
        return None, None

    group_name, group_location = extract_field("group")

    order_str, order_location = extract_field("order")
    order = None
    if order_str is not None:
        try:
            order = int(order_str)
        except ValueError:
            logger.error("Invalid order value: %r", order_str, location=order_location)

    # Strip 3 spaces of indent.
    content = [line[3:] for line in rst_strings.data[content_start_line:]]

    return SplitAutodocRstOutput(
        directive=directive,
        options=options,
        content=content,
        group_name=group_name,
        order=order,
    )


def _summarize_rst_content(content: List[str]) -> List[str]:
    i = 0
    # Skip over blank lines before start of directive content
    while i < len(content) and not content[i].strip():
        i += 1
    # Skip over first paragraph
    while i < len(content) and content[i].strip():
        i += 1

    return content[:i]


class _SiblingMatchKey(NamedTuple):
    """Lookup key for finding siblings of a `_MemberDocumenterEntry`.

    Normally siblings are determined based on the identity of the associated
    Python object.

    However, in the case of pybind11-overloaded functions, since all overloads
    share the same Python object, the overload_id must also be taken into
    account.
    """

    obj: Any
    overload_id: Optional[str]

    def __hash__(self):
        return hash((id(self.obj), self.overload_id))

    def __eq__(self, other):
        if not isinstance(other, _SiblingMatchKey):
            return False
        return self.obj is other.obj and self.overload_id == other.overload_id


def _get_sibling_match_key(entry: _MemberDocumenterEntry) -> Optional[_SiblingMatchKey]:
    obj = None
    if not isinstance(
        entry.documenter,
        (
            sphinx.ext.autodoc.FunctionDocumenter,
            sphinx.ext.autodoc.MethodDocumenter,
            sphinx.ext.autodoc.PropertyDocumenter,
        ),
    ):
        return None
    obj = entry.documenter.object
    overload_id: Optional[str] = None
    overload = entry.overload
    if overload is not None:
        overload_id = overload.overload_id

    return _SiblingMatchKey(obj, overload_id)


class _ApiEntityCollector:
    def __init__(
        self,
        app: sphinx.application.Sphinx,
        entities: Dict[str, _ApiEntity],
    ):
        self.app = app
        self.entities = entities

    def collect_entity_recursively(
        self,
        entry: _MemberDocumenterEntry,
        primary_entity: Optional[_ApiEntity] = None,
    ) -> str:
        canonical_full_name = None
        if isinstance(entry.documenter, sphinx.ext.autodoc.ClassDocumenter):
            canonical_full_name = entry.documenter.get_canonical_fullname()
        elif isinstance(entry.documenter, sphinx.ext.autodoc.FunctionDocumenter):
            canonical_full_name = (
                sphinx.ext.autodoc.ClassDocumenter.get_canonical_fullname(
                    entry.documenter  # type: ignore[arg-type]
                )
            )
        if canonical_full_name is None:
            canonical_full_name = f"{entry.parent_canonical_full_name}.{entry.name}"

        canonical_object_name = canonical_full_name + entry.overload_suffix
        existing_entity = self.entities.get(canonical_object_name)
        if existing_entity is not None:
            return canonical_object_name

        if (
            entry.overload
            and entry.overload.overload_id
            and re.fullmatch("[0-9]+", entry.overload.overload_id)
        ):
            logger.warning("Unspecified overload id: %s", canonical_object_name)

        if primary_entity is None:
            rst_strings = docutils.statemachine.StringList()
            entry.documenter.directive.result = rst_strings
            _prepare_documenter_docstring(entry)

            # Prevent autodoc from also documenting members, since this extension does
            # that separately.
            def document_members(*args, **kwargs):
                return

            entry.documenter.document_members = document_members  # type: ignore[assignment]
            entry.documenter.generate()

            split_result = _split_autodoc_rst_output(rst_strings)
            split_result.options.pop("module", None)

            group_name = split_result.group_name or ""
            order = split_result.order
            directive = split_result.directive
            options = split_result.options
            content = split_result.content
        else:
            group_name = primary_entity.group_name
            order = primary_entity.order
            directive = primary_entity.directive
            options = primary_entity.options
            content = primary_entity.content

        base_classes: Optional[List[str]] = None

        type_params: tuple[type_param_utils.TypeParam, ...] = ()

        if isinstance(entry.documenter, sphinx.ext.autodoc.ClassDocumenter):
            type_params = type_param_utils.get_class_type_params(
                entry.documenter.object
            )

            # By default (unless the `autodoc_class_signature` config option is
            # set to `"separated"`), autodoc will include the `__init__`
            # parameters in the signature.  Since that convention does not work
            # well with this extension, we just bypass that here.
            signatures = [type_param_utils.stringify_type_params(type_params)]

            if entry.documenter.config.python_apigen_show_base_classes:
                obj = entry.documenter.object
                bases = sphinx.util.inspect.getorigbases(obj)
                if bases is None:
                    bases = getattr(obj, "__bases__", None)
                if bases:
                    base_list = list(bases)
                    entry.documenter.env.events.emit(
                        "autodoc-process-bases",
                        entry.documenter.fullname,
                        obj,
                        entry.documenter.options,
                        base_list,
                    )
                    base_classes = [
                        stringify_annotation(base)
                        for base in base_list
                        if (
                            base is not object
                            and typing.get_origin(base) is not typing.Generic
                        )
                    ]
        else:
            if primary_entity is None:
                signatures = entry.documenter.format_signature().split("\n")
            else:
                signatures = primary_entity.signatures

        overload_id: Optional[str] = None
        if entry.overload is not None:
            overload_id = entry.overload.overload_id

        entity = _ApiEntity(
            documented_full_name="",
            canonical_full_name=canonical_full_name,
            objtype=entry.documenter.objtype,
            group_name=group_name,
            order=order,
            directive=directive,
            signatures=signatures,
            options=options,
            content=content,
            members=[],
            parents=[],
            subscript=entry.subscript,
            overload_id=overload_id or "",
            base_classes=base_classes,
            primary_entity=primary_entity is None,
            type_params=type_params,
        )

        self.entities[canonical_object_name] = entity

        entity.members = (
            self.collect_documenter_members(
                entry.documenter,
                canonical_object_name=canonical_object_name,
            )
            if primary_entity is None
            else primary_entity.members
        )

        return canonical_object_name

    def collect_documenter_members(
        self,
        documenter: sphinx.ext.autodoc.Documenter,
        canonical_object_name: str,
    ) -> List[_ApiEntityMemberReference]:
        members: List[_ApiEntityMemberReference] = []

        sibling_match_map: dict[_SiblingMatchKey, _ApiEntityMemberReference] = {}

        for entry in _get_documenter_members(
            self.app, documenter, canonical_full_name=canonical_object_name
        ):
            sibling_match_key = _get_sibling_match_key(entry)
            primary_sibling_entity: Optional[_ApiEntity] = None
            primary_sibling_member: Optional[_ApiEntityMemberReference] = None
            if (sibling_match_key := _get_sibling_match_key(entry)) is not None:
                primary_sibling_member = sibling_match_map.get(sibling_match_key)
                if primary_sibling_member is not None:
                    primary_sibling_entity = self.entities[
                        primary_sibling_member.canonical_object_name
                    ]
            member_canonical_object_name = self.collect_entity_recursively(
                entry,
                primary_entity=primary_sibling_entity,
            )
            child = self.entities[member_canonical_object_name]
            member = _ApiEntityMemberReference(
                name=entry.name,
                parent_canonical_object_name=canonical_object_name,
                canonical_object_name=member_canonical_object_name,
                inherited=entry.is_inherited,
                siblings=[],
                type_param_substitutions=entry.type_param_substitutions,
            )

            if primary_sibling_member is not None:
                primary_sibling_member.siblings.append(member)
                assert primary_sibling_entity is not None
                if primary_sibling_entity.siblings is None:
                    primary_sibling_entity.siblings = {}
                primary_sibling_entity.siblings.setdefault(
                    member_canonical_object_name, True
                )
            else:
                if sibling_match_key is not None:
                    sibling_match_map[sibling_match_key] = member
                members.append(member)

            child.parents.append(member)

        return members


def _get_base_docname(output_prefixes: Dict[str, str], full_name: str) -> str:
    end_idx = len(full_name)
    while True:
        output_path = output_prefixes.get(full_name[:end_idx])
        if output_path is not None:
            return output_path + full_name[end_idx + 1 :]
        new_end_idx = full_name.rfind(".", 0, end_idx)
        if new_end_idx == -1:
            raise ValueError(
                f"Could not find output prefix for {full_name!r} in {output_prefixes!r}"
            )
        end_idx = new_end_idx


def _get_docname(
    output_prefixes: Dict[str, str],
    documented_full_name: str,
    overload_id: str,
    case_insensitive_filesystem: bool,
):
    docname = _get_base_docname(output_prefixes, documented_full_name)
    if overload_id:
        docname += f"-{overload_id}"

    return apigen_utils.make_unique_docname(docname, case_insensitive_filesystem)


def _assign_documented_full_names(
    entities: Dict[str, _ApiEntity],
    default_groups: List[Tuple[re.Pattern, str]],
    default_order: List[Tuple[re.Pattern, int]],
    output_prefixes: Dict[str, str],
    case_insensitive_filesystem: bool,
) -> None:
    """Determines the full name under which each entity will be documented."""

    def get_documented_full_name(entity: _ApiEntity) -> str:
        documented_full_name = entity.documented_full_name
        if documented_full_name:
            # Name already assigned
            return documented_full_name

        parents = entity.parents
        assert len(parents) > 0

        def parent_sort_key(parent_ref: _ApiEntityMemberReference):
            canonical_name_from_parent = (
                parent_ref.parent_canonical_object_name + "." + parent_ref.name
            )
            canonical = canonical_name_from_parent == entity.canonical_full_name
            inherited = parent_ref.inherited
            return (canonical is False, inherited, canonical_name_from_parent)

        parents.sort(key=parent_sort_key)

        parent_ref = parents[0]
        parent_entity = entities.get(parent_ref.parent_canonical_object_name)
        if parent_entity is None:
            # Parent is a module.
            parent_documented_name = parent_ref.parent_canonical_object_name
            entity.top_level = True
            entity.options["module"] = parent_ref.parent_canonical_object_name
        else:
            parent_documented_name = get_documented_full_name(parent_entity)
            entity.options["module"] = parent_entity.options["module"]
            if parent_entity.type_params:
                if entity.objtype != "method" or (
                    not entity.options.get("classmethod")
                    and not entity.options.get("staticmethod")
                ):
                    entity.parent_type_params = (
                        parent_entity.object_name,
                        parent_entity.type_params,
                    )

        # Resolve type parameters
        if entity.objtype != "class":
            for i, signature in enumerate(entity.signatures):
                type_params = type_param_utils.get_type_params_from_signature(signature)
                if entity.parent_type_params:
                    for param in entity.parent_type_params[1]:
                        type_params.pop(param.__name__, None)
                if type_params:
                    entity.signatures[i] = (
                        type_param_utils.stringify_type_params(type_params.values())
                        + signature
                    )

        documented_full_name = parent_documented_name + "." + parent_ref.name
        entity.documented_full_name = documented_full_name
        entity.documented_name = parent_ref.name

        # Assign default group name.
        if not entity.group_name:
            entity.group_name = _get_group_name(default_groups, entity)

        if entity.order is None:
            entity.order = _get_order(default_order, entity)

        entity.docname = _get_docname(
            output_prefixes,
            documented_full_name,
            entity.overload_id,
            case_insensitive_filesystem,
        )

        return documented_full_name

    for entity in list(entities.values()):
        get_documented_full_name(entity)
        entities[entity.object_name] = entity


def _builder_inited(app: sphinx.application.Sphinx) -> None:
    """Generates the rST files for API members."""

    env = app.env
    assert env is not None

    data = _ApiData()

    setattr(app, "_sphinx_immaterial_python_apigen_data", data)

    apigen_modules = app.config.python_apigen_modules
    if not apigen_modules:
        return

    for module_name, output_path in apigen_modules.items():
        try:
            importlib.import_module(module_name)
        except ImportError:
            logger.warning(
                "Failed to import module %s specified in python_apigen_modules",
                module_name,
                exc_info=True,
            )
            continue

        documenter = _create_documenter(
            env=env,
            documenter_cls=sphinx.ext.autodoc.ModuleDocumenter,
            name=module_name,
        )
        _ApiEntityCollector(
            app=app,
            entities=data.entities,
        ).collect_documenter_members(
            documenter=documenter,
            canonical_object_name=module_name,
        )

    writer = apigen_utils.GeneratedDocumentWriter(
        app=app,
        case_insensitive_filesystem=app.config.python_apigen_case_insensitive_filesystem,
        output_prefixes=list(apigen_modules.values()),
        generator_module=__name__,
    )

    writer.prepare_output_directories()

    default_groups = [
        (re.compile(pattern), group)
        for pattern, group in app.config.python_apigen_default_groups
    ]

    default_order = [
        (re.compile(pattern), order)
        for pattern, order in app.config.python_apigen_default_order
    ]

    _assign_documented_full_names(
        entities=data.entities,
        default_groups=default_groups,
        default_order=default_order,
        output_prefixes=apigen_modules,
        case_insensitive_filesystem=writer.case_insensitive_filesystem,
    )

    alphabetical = app.config.python_apigen_order_tiebreaker == "alphabetical"

    def get_pages():
        for object_name, entity in data.entities.items():
            if object_name != entity.object_name or not entity.primary_entity:
                # Alias
                continue

            data.sort_members(entity.members, alphabetical=alphabetical)

            if entity.top_level:
                group_id = docutils.nodes.make_id(entity.group_name)
                data.top_level_groups.setdefault(group_id, []).append(entity.parents[0])

            content = sphinx_utils.format_directive(
                "python-apigen-entity-page",
                entity.object_name,
            )
            yield entity.docname, entity.object_name, content

    writer.write_files(get_pages())

    for members in data.top_level_groups.values():
        data.sort_members(members, alphabetical=alphabetical)


def _monkey_patch_napoleon_to_add_group_field():
    """Adds support to sphinx.ext.napoleon for the "Group" and "Order" fields.

    This field is used by this module to organize members into groups.
    """
    orig_load_custom_sections = (
        sphinx.ext.napoleon.docstring.GoogleDocstring._load_custom_sections
    )

    def parse_section(
        self: sphinx.ext.napoleon.docstring.GoogleDocstring, section: str
    ) -> List[str]:
        lines = self._strip_empty(self._consume_to_next_section())
        lines = self._dedent(lines)
        name = section.lower()
        if len(lines) != 1:
            raise ValueError(f"Expected exactly one {name} in {section} section")
        return [f":{name}: " + lines[0], ""]

    def load_custom_sections(
        self: sphinx.ext.napoleon.docstring.GoogleDocstring,
    ) -> None:
        orig_load_custom_sections(self)
        self._sections["group"] = lambda section: parse_section(self, section)
        self._sections["order"] = lambda section: parse_section(self, section)

    sphinx.ext.napoleon.docstring.GoogleDocstring._load_custom_sections = (  # type: ignore[assignment]
        load_custom_sections
    )


def _config_inited(
    app: sphinx.application.Sphinx, config: sphinx.config.Config
) -> None:
    if isinstance(config.python_apigen_subscript_method_types, str):
        setattr(
            config,
            "python_apigen_subscript_method_types",
            re.compile(config.python_apigen_subscript_method_types),
        )


def setup(app: sphinx.application.Sphinx):
    """Initializes the extension."""
    _monkey_patch_napoleon_to_add_group_field()
    app.connect("builder-inited", _builder_inited)
    app.connect("config-inited", _config_inited)
    app.setup_extension("sphinx.ext.autodoc")
    app.add_directive("python-apigen-entity-page", PythonApigenEntityPageDirective)
    app.add_directive("python-apigen-group", PythonApigenTopLevelGroupDirective)
    app.add_directive(
        "python-apigen-entity-summary", PythonApigenEntitySummaryDirective
    )
    app.add_config_value(
        "python_apigen_modules", types=(Dict[str, str],), default={}, rebuild="env"
    )
    app.add_config_value(
        "python_apigen_default_groups",
        types=(List[Tuple[str, str]],),
        default=[(".*", "Public members"), ("class:.*", "Classes")],
        rebuild="env",
    )
    app.add_config_value(
        "python_apigen_default_order",
        types=(List[Tuple[str, int]],),
        default=[],
        rebuild="env",
    )
    app.add_config_value(
        "python_apigen_order_tiebreaker",
        types=sphinx.config.ENUM("definition_order", "alphabetical"),
        default="definition_order",
        rebuild="env",
    )
    app.add_config_value(
        "python_apigen_subscript_method_types",
        default=r".*\._[^.]*",
        types=(re.Pattern,),
        rebuild="env",
    )
    app.add_config_value(
        "python_apigen_case_insensitive_filesystem",
        default=None,
        types=(bool, type(None)),  # type: ignore[arg-type]
        rebuild="env",
    )
    app.add_config_value(
        "python_apigen_show_base_classes",
        default=True,
        types=(bool,),
        rebuild="env",
    )
    app.add_config_value(
        "python_apigen_rst_prolog", types=(str,), default="", rebuild="env"
    )
    app.add_config_value(
        "python_apigen_rst_epilog", types=(str,), default="", rebuild="env"
    )
    app.add_event("python-apigen-skip-base")

    return {"parallel_read_safe": True, "parallel_write_safe": True}
