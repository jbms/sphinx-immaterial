"""C++ API documentation generation extension."""

import collections
import contextlib
import dataclasses
import json
import os
import re
from typing import cast, Dict, List, Optional, Tuple, Set, Type, Literal

import docutils.core
import docutils.nodes
import docutils.parsers.rst.directives
import docutils.utils
import pydantic
import pydantic.dataclasses
import sphinx.application
import sphinx.builders
import sphinx.builders.html
import sphinx.domains.c
import sphinx.domains.cpp
import sphinx.environment
import sphinx.errors
import sphinx.util.cfamily
import sphinx.util.docfields
import sphinx.util.logging


from .. import apigen_utils
from ... import sphinx_utils
from . import api_parser
from .signodes import desc_cpp_explicit

logger = sphinx.util.logging.getLogger(__name__)

APIDOC_SECTION_ID_PREFIX = "cpp-api-"


@pydantic.dataclasses.dataclass
class ApigenConfig:
    """Specifies a C++ API generation configuration."""

    document_prefix: str
    """Sphinx document path prefix for the per-entity documentation pages.

    .. important::
        This should use the Linux path separator :python:`"/"` (even if
        building on Windows).
    """

    api_parser_config: Optional[api_parser.Config] = None
    """Configuration for generating an API description.

    This option and `.api_data` are mutually exclusive.
    """

    api_data: Optional[str] = None
    """Path to already-parsed API description.

    This option and `.api_parser_config` are mutually exclusive.
    """


CppApiEntity = api_parser.CppApiEntity
EntityId = str


@dataclasses.dataclass
class CppApiData:
    groups: Dict[str, List[EntityId]] = dataclasses.field(default_factory=dict)
    entities: Dict[EntityId, CppApiEntity] = dataclasses.field(default_factory=dict)
    nonitpick: Set[Tuple[str, str, int]] = dataclasses.field(default_factory=set)

    def get_entity_sub_groups(
        self, entity_id: str, member: bool
    ) -> Dict[str, List[EntityId]]:
        entity = self.entities[entity_id]
        return entity.get(
            cast(
                Literal["related_members", "related_nonmembers"],
                "related_members" if member else "related_nonmembers",
            ),
            cast(Dict[str, List[EntityId]], {}),
        )

    def get_documented_entities(self):
        seen = set()

        def process_group(entity_ids: List[str]):
            for entity_id in entity_ids:
                if entity_id in seen:
                    continue
                seen.add(entity_id)
                yield entity_id
                for member in (True, False):
                    for related_ids in self.get_entity_sub_groups(
                        entity_id, member=member
                    ).values():
                        yield from process_group(related_ids)

        for group_members in self.groups.values():
            yield from process_group(group_members)

    def get_entity_toc_title(self, entity: CppApiEntity) -> str:
        return entity["name"]

    def get_entity_scope(self, entity: CppApiEntity) -> str:
        components = []
        cur_entity = entity
        while True:
            parent_id = cur_entity.get("parent")
            if parent_id is None:
                break
            parent_entity = self.entities.get(parent_id)
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

    def get_entity_object_name(self, entity: CppApiEntity) -> str:
        name = self.get_entity_scope(entity) + entity["name"]
        special_id = entity.get("special_id")
        if special_id:
            name += f"[{special_id}]"
        return name

    def get_entity_page_name(self, entity: CppApiEntity) -> str:
        return entity["page_name"]

    def get_entity_page_path(self, entity: CppApiEntity) -> str:
        return entity["document_prefix"] + self.get_entity_page_name(entity)


def _get_cpp_api_data(
    env: sphinx.environment.BuildEnvironment, warn: bool = False
) -> CppApiData:
    KEY = "_sphinx_immaterial_cpp_apigen_data"
    data = getattr(env.app, KEY, None)
    if data is not None:
        return data

    apigen_configs = getattr(env.app, _CONFIG_ATTR)
    data = CppApiData()

    for apigen_config in apigen_configs:
        if apigen_config.api_parser_config is not None:
            json_data = api_parser.generate_output(apigen_config.api_parser_config)
        else:
            with open(
                os.path.join(env.app.srcdir, apigen_config.api_data),
                "r",
                encoding="utf-8",
            ) as f:
                json_data = cast(api_parser.JsonApiData, json.load(f))
        for entity in json_data["entities"].values():
            entity["document_prefix"] = apigen_config.document_prefix
        data.entities.update(json_data["entities"])
        for group_id, group in json_data["groups"].items():
            data.groups.setdefault(group_id, []).extend(group)
        data.nonitpick.update(
            set((x["target"], x["file"], x["line"]) for x in json_data["nonitpick"])
        )

        if warn:
            for diag in json_data["warnings"]:
                logger.warning(
                    diag["message"],
                    location=api_parser.json_location_to_string(diag["location"]),
                )
            for diag in json_data["errors"]:
                logger.error(
                    diag["message"],
                    location=api_parser.json_location_to_string(diag["location"]),
                )

    setattr(env.app, KEY, data)
    return data


def _transform_doc_comment(
    env: sphinx.environment.BuildEnvironment,
    doc: Optional[api_parser.JsonDocComment],
    summary: bool,
) -> Optional[docutils.statemachine.StringList]:
    if not doc:
        return None
    text = doc["text"]
    location = doc["location"]
    filename = location["file"]
    lineno = location["line"]

    if summary:
        # Find first blank line
        first_blank_line = re.search(r"^\s*$", text, flags=re.MULTILINE)
        if first_blank_line:
            text = text[: first_blank_line.start()]

    out = docutils.statemachine.StringList()
    sphinx_utils.append_multiline_string_to_stringlist(
        out,
        ".. highlight-push::\n\n" + env.config.cpp_apigen_rst_prolog + "\n\n",
        "<cpp_apigen_rst_prolog>",
        -2,
    )
    sphinx_utils.append_multiline_string_to_stringlist(out, text, filename, lineno - 1)
    sphinx_utils.append_multiline_string_to_stringlist(
        out,
        "\n\n" + env.config.cpp_apigen_rst_epilog + "\n\n.. highlight-pop::\n\n",
        "<cpp_apigen_rst_epilog>",
        -2,
    )
    return out


def _format_template_parameters(entity: CppApiEntity) -> str:
    template_parameters = entity.get("template_parameters")
    if template_parameters is None:
        return ""
    tparam_list_str = ", ".join(x["declaration"] for x in template_parameters)
    tparams = f"template <{tparam_list_str}> "
    requires = entity.get("requires")
    if requires:
        requires_expr = " && ".join(requires)
        tparams += f"requires {requires_expr} "
    return tparams


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


def _validate_signature_line_tags(
    strip_tags: List[Type[sphinx.addnodes.desc_sig_element]],
    children: List[docutils.nodes.Node],
):
    for strip_tag, child in zip(strip_tags, children):
        if isinstance(child, sphinx.addnodes.desc_signature_line) and child.children:
            child = child.children[0]
        if not isinstance(child, strip_tag):
            raise ValueError(
                f"Expected {strip_tag!r} tag, but received: {type(child)!r}"
            )


def _strip_template_parameters(
    api_data: CppApiData,
    entity: CppApiEntity,
    signode: sphinx.addnodes.desc_signature,
    strip_self_parameters: bool = False,
    strip_ancestors_parameters: bool = False,
):
    cur_entity = entity
    strip_leading: List[str] = []
    strip_trailing: List[str] = []
    if strip_self_parameters:
        if entity.get("requires") and entity.get("template_parameters") is None:
            strip_trailing.append("trailingRequiresClause")
    depth = 0
    while True:
        if depth > 0 and not strip_ancestors_parameters:
            break
        if depth > 0 or strip_self_parameters:
            if cur_entity.get("template_parameters") is not None:
                strip_leading.append("templateParams")
                if cur_entity.get("requires"):
                    strip_leading.append("requiresClause")
        depth += 1
        parent_id = cur_entity.get("parent")
        if parent_id is None:
            break
        cur_entity = api_data.entities[parent_id]

    signature_lines: List[Tuple[int, sphinx.addnodes.desc_signature_line]] = [
        (i, child)
        for i, child in enumerate(signode)
        if isinstance(child, sphinx.addnodes.desc_signature_line)
    ]
    if len(signature_lines) < len(strip_leading) + len(strip_trailing):
        raise ValueError("Missing children")
    for i, line_type in enumerate(strip_leading):
        assert signature_lines[i][1].sphinx_line_type == line_type

    for i, line_type in enumerate(strip_trailing):
        assert (
            signature_lines[len(signature_lines) - 1 - i][1].sphinx_line_type
            == line_type
        )

    remove = (
        signature_lines[: len(strip_leading)]
        + signature_lines[len(signature_lines) - len(strip_trailing) :]
    )
    remove.reverse()
    for i, _ in remove:
        del signode[i]


def _summarize_explicit(signode: sphinx.addnodes.desc_signature) -> None:
    for node in signode.findall(condition=desc_cpp_explicit):
        if len(node.children) == 1:
            continue
        node.children[2:-1] = sphinx.addnodes.desc_sig_punctuation("...", "...")


def _format_entity_alias(
    entity: api_parser.TypeAliasEntity, full_name: str
) -> Tuple[str, str]:
    underlying_type = entity["underlying_type"]
    signature = f"{full_name}"
    if underlying_type is not None:
        signature += f" = {underlying_type}"
    return ("cpp:type", signature)


def _format_entity_constructor(
    entity: api_parser.FunctionEntity, full_name: str
) -> Tuple[str, str]:
    return _format_entity_function(entity, full_name)


def _format_entity_class(
    entity: api_parser.ClassEntity, full_name: str
) -> Tuple[str, str]:
    prefix = " ".join(entity["prefix"])
    signature = f"{prefix} {full_name}"
    base_strs = []
    for base in entity["bases"]:
        base_strs.append(f'{base["access"]} {base["type"]}')
    if base_strs:
        signature += " : "
        signature += ", ".join(base_strs)

    return (f'cpp:{entity["keyword"]}', signature)


def _format_entity_function(
    entity: api_parser.FunctionEntity, full_name: str
) -> Tuple[str, str]:
    signature = entity["declaration"].replace(entity["name_substitute"], full_name)
    return ("cpp:function", signature)


def _format_entity_method(
    entity: api_parser.FunctionEntity, full_name: str
) -> Tuple[str, str]:
    return _format_entity_function(entity, full_name)


def _format_entity_conversion_function(
    entity: api_parser.FunctionEntity, full_name: str
) -> Tuple[str, str]:
    return _format_entity_function(entity, full_name)


def _format_entity_var(entity: api_parser.VarEntity, full_name: str) -> Tuple[str, str]:
    declaration = entity["declaration"].replace(entity["name_substitute"], full_name)
    signature = declaration
    initializer = entity["initializer"]
    if initializer is not None:
        signature += initializer
    return ("cpp:var", signature)


def _format_entity_enum(
    entity: api_parser.EnumEntity, full_name: str
) -> Tuple[str, str]:
    signature = full_name
    directive_name = "cpp:enum"
    if entity["keyword"]:
        directive_name += f'-{entity["keyword"]}'
    return (directive_name, signature)


def _format_entity_macro(
    entity: api_parser.MacroEntity, full_name: str
) -> Tuple[str, str]:
    signature = full_name
    parameters = entity["parameters"]
    if parameters is not None:
        signature += f'({", ".join(parameters)})'
    return ("c:macro", signature)


def _format_template_prefix(
    api_data: CppApiData, entity: CppApiEntity, summary: bool
) -> str:
    inner_prefix = _format_template_parameters(entity)
    if summary:
        return inner_prefix
    prefixes = [inner_prefix]
    while True:
        parent_id = entity.get("parent")
        if parent_id is None:
            break
        entity = api_data.entities[parent_id]
        prefixes.append(_format_template_parameters(entity))
    prefixes.reverse()
    return " ".join(prefixes)


def _format_trailing_requires(entity: CppApiEntity, summary: bool) -> str:
    template_parameters = entity.get("template_parameters")
    requires = entity.get("requires")
    if template_parameters is not None or not requires:
        return ""
    return " requires " + " && ".join(expr for expr in requires)


def _format_entity(
    api_data: CppApiData, entity: CppApiEntity, summary: bool, include_scope: bool
):
    full_name = api_data.get_entity_scope(entity) if include_scope else ""
    full_name += entity["name"]
    kind = entity["kind"]
    if summary and kind in ("class", "alias", "var"):
        # Add template arguments
        full_name += _format_template_arguments(entity)
    cpp_directive, signature_text = globals()[f"_format_entity_{kind}"](
        entity, full_name
    )
    signature_line = (
        _format_template_prefix(api_data, entity, summary=summary)
        + signature_text
        + _format_trailing_requires(entity, summary=summary)
    )
    if kind != "macro":
        signature_line += ";"
    return cpp_directive, signature_line


@contextlib.contextmanager
def save_cpp_scope(env: sphinx.environment.BuildEnvironment):
    parent_symbol = env.temp_data.get("cpp:parent_symbol", False)
    namespace_stack = env.temp_data.get("cpp:namespace_stack", False)
    if namespace_stack:
        namespace_stack = list(namespace_stack)
    parent_key = env.ref_context.get("cpp:parent_key", False)

    yield

    if parent_symbol is not False:
        env.temp_data["cpp:parent_symbol"] = parent_symbol
    else:
        env.temp_data.pop("cpp:parent_symbol", None)

    if namespace_stack is not False:
        env.temp_data["cpp:namespace_stack"] = namespace_stack
    else:
        env.temp_data.pop("cpp:namespace_stack", None)

    if parent_key is not False:
        env.ref_context["cpp:parent_key"] = parent_key
    else:
        env.ref_context.pop("cpp:parent_key", None)


def _add_entity_description(
    env: sphinx.environment.BuildEnvironment,
    api_data: CppApiData,
    entity: CppApiEntity,
    contentnode: docutils.nodes.Element,
    summary: bool,
    state: docutils.parsers.rst.states.RSTState,
) -> None:
    # kind = entity["kind"]
    out = docutils.statemachine.StringList()
    location = entity["location"]
    parent_id = entity.get("parent")
    if parent_id and summary:
        include_scope = False
    else:
        include_scope = True

    if parent_id:
        # parent = api_data.entities[parent_id]
        scope_template_prefix = _format_template_prefix(
            api_data, api_data.entities[parent_id], summary=False
        )
    else:
        # parent = None
        scope_template_prefix = ""

    scope = api_data.get_entity_scope(entity).rstrip(":")

    sphinx_utils.append_directive_to_stringlist(
        out,
        "cpp:namespace",
        scope_template_prefix + scope if not include_scope else "nullptr",
        source_path=location["file"],
        source_line=location["line"] - 1,
    )

    cpp_directive, signature_line = _format_entity(
        api_data, entity, summary, include_scope
    )

    signature_lines = []

    num_include_lines = 0

    if not summary:
        include_path = location["file"]
        signature_lines.append(f'#include "{include_path}"')
        num_include_lines = 1

    signature_lines.append(signature_line)
    siblings = entity.get("siblings")
    entity_ids = [entity["id"]]
    if siblings:
        for sibling_id in siblings:
            sibling = api_data.entities[sibling_id]
            other_cpp_directive, other_signature_line = _format_entity(
                api_data, sibling, summary, include_scope
            )
            assert other_cpp_directive == cpp_directive
            signature_lines.append(other_signature_line)
            entity_ids.append(sibling["id"])

    doc = entity["doc"]
    assert doc is not None
    body = _transform_doc_comment(env, doc, summary=summary)
    sphinx_utils.append_directive_to_stringlist(
        out,
        cpp_directive,
        "\n".join(signature_lines),
        options={
            "noindexentry": True,
            "noindex": summary,
            "node-id": "",
            "symbol-ids": json.dumps(entity_ids),
        },
        source_path=location["file"],
        source_line=location["line"] - 1,
        content=body,
    )

    with apigen_utils.save_rst_defaults(env), save_cpp_scope(env):
        nodes = [
            x
            for x in sphinx_utils.parse_rst(state=state, text=out)
            if isinstance(x, sphinx.addnodes.desc)
        ]
    assert len(nodes) == 1
    objdesc = nodes[0]

    desc_name_nodes: List[docutils.nodes.Element] = []

    for signode in objdesc.children[num_include_lines:-1]:
        assert isinstance(signode, sphinx.addnodes.desc_signature)
        # Find the node in the signature containing the actual unqualified name.
        for sub_node in signode.findall(condition=sphinx.addnodes.desc_name):
            if "sig-name-nonprimary" in sub_node["classes"]:
                continue
            desc_name_nodes.append(sub_node)
            break
        else:
            raise ValueError("Failed to find desc_name node")

    obj_content = cast(sphinx.addnodes.desc_content, objdesc.children[-1])

    for entity_id, signode in zip(entity_ids, objdesc.children[num_include_lines:-1]):
        assert isinstance(signode, sphinx.addnodes.desc_signature)
        _strip_template_parameters(
            api_data,
            api_data.entities[entity_id],
            signode,
            strip_ancestors_parameters=not summary,
            strip_self_parameters=summary,
        )
        if summary:
            _summarize_explicit(signode)

    if summary:
        objdesc["classes"].append("summary")
        # Insert a link around the `desc_name` field
        for i, desc_name_node in enumerate(desc_name_nodes):
            xref_node = sphinx.addnodes.pending_xref(
                "",
                desc_name_node.deepcopy(),
                refdomain="std",
                reftype="doc",
                reftarget="/" + api_data.get_entity_page_path(entity),
                refwarn=True,
                refexplicit=True,
            )
            desc_name_node.replace_self(xref_node)
            desc_name_nodes[i] = xref_node
    else:
        if entity["kind"] == "enum":
            _add_enumerators(
                env=env,
                api_data=api_data,
                entity=entity,
                obj_content=obj_content,
                parent_scope=scope_template_prefix + scope,
                state=state,
            )
        member_groups = api_data.get_entity_sub_groups(entity["id"], member=True)
        _merge_summary_nodes_into(
            env=env,
            api_data=api_data,
            state=state,
            contentnode=obj_content,
            groups=member_groups,
            top_level_group=False,
        )

    contentnode += nodes


def _add_enumerators(
    env: sphinx.environment.BuildEnvironment,
    api_data: CppApiData,
    entity: api_parser.EnumEntity,
    parent_scope: str,
    obj_content: sphinx.addnodes.desc_content,
    state: docutils.parsers.rst.states.RSTState,
) -> None:
    # parent_object_name = api_data.get_entity_object_name(entity)
    for child in entity["enumerators"]:
        name = child["name"]
        location = child["location"]
        out = docutils.statemachine.StringList()
        sphinx_utils.append_directive_to_stringlist(
            out,
            "cpp:namespace",
            f'{parent_scope}::{entity["name"]}',
            source_path=location["file"],
            source_line=location["line"] - 1,
        )
        anchor = f"e-{name}"
        child_doc = child["doc"]
        sphinx_utils.append_directive_to_stringlist(
            out,
            "cpp:enumerator",
            child["decl"],
            options={
                "noindexentry": True,
                "symbol-ids": json.dumps([child["id"]]),
                "node-id": anchor,
            },
            source_path=location["file"],
            source_line=location["line"] - 1,
            content=_transform_doc_comment(env, child_doc, summary=False),
        )
        with apigen_utils.save_rst_defaults(env), save_cpp_scope(env):
            nodes = [
                x
                for x in sphinx_utils.parse_rst(state=state, text=out)
                if isinstance(x, sphinx.addnodes.desc)
            ]
        assert len(nodes) == 1
        enumerator_objdesc = nodes[0]
        obj_content += enumerator_objdesc
        enumerator_signode, enumerator_doc_node = enumerator_objdesc.children
        assert isinstance(enumerator_signode, sphinx.addnodes.desc_signature)
        enumerator_signode["toc_title"] = name


def _add_group_summary(
    env: sphinx.environment.BuildEnvironment,
    api_data: CppApiData,
    state: docutils.parsers.rst.states.RSTState,
    entities: List[EntityId],
    parent: docutils.nodes.Element,
    notoc: bool = False,
) -> None:
    toc_entries = []

    name_counts = collections.Counter(
        api_data.entities[entity_id]["name"] for entity_id in entities
    )

    for entity_id in entities:
        entity = api_data.entities[entity_id]
        path = api_data.get_entity_page_path(entity)
        _add_entity_description(
            env=env,
            api_data=api_data,
            entity=entity,
            contentnode=parent,
            summary=True,
            state=state,
        )
        title = entity["name"]
        if name_counts[title] > 1:
            special_id = entity.get("special_id")
            if special_id is not None:
                title += f" [{special_id}]"
        if not notoc:
            toc_entries.append((title, path))

    parent.extend(
        sphinx_utils.make_toctree_node(
            state=state,
            toc_entries=toc_entries,
            options={"hidden": True},
            source_path=__name__,
        )
    )


def _merge_summary_nodes_into(
    env: sphinx.environment.BuildEnvironment,
    api_data: CppApiData,
    state: docutils.parsers.rst.states.RSTState,
    contentnode: docutils.nodes.Element,
    groups: Dict[str, List[EntityId]],
    top_level_group: bool,
) -> None:
    """Merges the member summary into `contentnode`.

    Members are organized into groups.  The group is either specified explicitly
    by a `Group:` field in the docstring, or determined automatically by
    `_get_group_name`.  If there is an existing section, the member summary is
    appended to it.  Otherwise, a new section is created.

    Args:
      contentnode: The existing container to which the member summaries will be
        added.  If `contentnode` contains sections, those sections correspond to
        group names.
    """

    apigen_utils.merge_groups_into(
        parent=contentnode,
        group_id_prefix=APIDOC_SECTION_ID_PREFIX if top_level_group else "",
        groups=groups,
        insert_group=lambda entities, section: _add_group_summary(
            env=env, api_data=api_data, state=state, entities=entities, parent=section
        ),
    )


class CppApigenEntityPageDirective(sphinx.util.docutils.SphinxDirective):
    """Documents an entity and summarizes its members, if applicable."""

    has_content = False
    final_argument_whitespace = True
    required_arguments = 1
    optional_arguments = 0

    def run(self) -> List[docutils.nodes.Node]:
        # Wrap in a section
        section = docutils.nodes.section()
        section["ids"].append("")

        # Sphinx treats the first child of a `section` node as the title,
        # regardless of its type.  We use a comment node to avoid adding a title
        # that would be redundant with the object description.
        comment_placeholder = docutils.nodes.comment("", "")
        section += comment_placeholder

        api_data = _get_cpp_api_data(self.env)

        entity_id = self.arguments[0]
        entity = api_data.entities.get(entity_id)
        if entity is None:
            logger.error(
                "Undefined C++ entity: %r", entity_id, location=self.get_location()
            )
            return []

        _add_entity_description(
            env=self.env,
            api_data=api_data,
            entity=entity,
            contentnode=section,
            summary=False,
            state=self.state,
        )
        comment_placeholder.replace_self(
            docutils.nodes.comment("", api_data.get_entity_object_name(entity))
        )

        non_member_groups = api_data.get_entity_sub_groups(entity_id, member=False)
        _merge_summary_nodes_into(
            env=self.env,
            api_data=api_data,
            state=self.state,
            contentnode=section,
            groups=non_member_groups,
            top_level_group=False,
        )
        return [section]


class CppApigenTopLevelGroupDirective(sphinx.util.docutils.SphinxDirective):
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
        api_data = _get_cpp_api_data(env)
        group_id = docutils.nodes.make_id(self.arguments[0])
        entities = api_data.groups.get(group_id)
        if not entities:
            logger.warning(
                "No entities in group %r",
                group_id,
                location=self.get_location(),
            )
            return []
        contentnode = docutils.nodes.section()
        _add_group_summary(
            env=self.env,
            api_data=api_data,
            state=self.state,
            entities=entities,
            parent=contentnode,
            notoc="notoc" in self.options,
        )
        return contentnode.children


class CppApigenEntitySummaryDirective(sphinx.util.docutils.SphinxDirective):
    """Generates a summary/link to a C++ entity."""

    has_content = False
    final_argument_whitespace = True
    required_arguments = 1
    optional_arguments = 0

    option_spec = {
        "notoc": docutils.parsers.rst.directives.flag,
    }

    def run(self) -> List[docutils.nodes.Node]:
        env = self.env
        api_data = _get_cpp_api_data(env)
        entity_id = self.arguments[0]
        entity = api_data.entities.get(entity_id)
        if entity is None:
            logger.warning(
                "No C++ entity named: %r",
                entity_id,
                location=self.get_location(),
            )
            return []
        contentnode = docutils.nodes.section()
        _add_group_summary(
            env=self.env,
            api_data=api_data,
            state=self.state,
            entities=[entity_id],
            parent=contentnode,
            notoc="notoc" in self.options,
        )
        return contentnode.children


def _builder_inited(app: sphinx.application.Sphinx) -> None:
    """Generates the rST files for API members."""

    api_data = _get_cpp_api_data(app.env, warn=True)
    apigen_configs = getattr(app, _CONFIG_ATTR)

    writer = apigen_utils.GeneratedDocumentWriter(
        app=app,
        case_insensitive_filesystem=app.config.cpp_apigen_case_insensitive_filesystem,
        output_prefixes=[
            apigen_config.document_prefix for apigen_config in apigen_configs
        ],
        generator_module=__name__,
    )
    writer.prepare_output_directories()
    for entity in api_data.entities.values():
        page_name = entity.get("page_name")
        if page_name is None:
            continue
        entity["page_name"] = apigen_utils.make_unique_docname(
            page_name, writer.case_insensitive_filesystem
        )

    def get_entities():
        for entity_id in api_data.get_documented_entities():
            entity = api_data.entities[entity_id]
            content = sphinx_utils.format_directive(
                "cpp-apigen-entity-page",
                entity_id,
            )
            object_name = api_data.get_entity_object_name(entity)
            docname = api_data.get_entity_page_path(entity)
            yield (docname, object_name, content)

    writer.write_files(get_entities())


def _warn_missing_reference(
    app: sphinx.application.Sphinx, domain, node: sphinx.addnodes.pending_xref
) -> bool:
    if not isinstance(domain, sphinx.domains.cpp.CPPDomain):
        return False
    api_data = _get_cpp_api_data(app.env)
    source, line = docutils.utils.get_source_line(node)
    return (node["reftarget"], source, line) in api_data.nonitpick


_CONFIG_ATTR = "_sphinx_immaterial_cpp_apigen_configs"


def _config_inited(
    app: sphinx.application.Sphinx, config: sphinx.config.Config
) -> None:
    apigen_configs = cast(
        List[ApigenConfig],
        pydantic.TypeAdapter(List[ApigenConfig]).validate_python(
            config.cpp_apigen_configs
        ),
    )
    setattr(app, _CONFIG_ATTR, apigen_configs)


def setup(app: sphinx.application.Sphinx):
    app.connect("config-inited", _config_inited)
    app.connect("builder-inited", _builder_inited)
    app.connect("warn-missing-reference", _warn_missing_reference)
    app.add_directive("cpp-apigen-entity-page", CppApigenEntityPageDirective)
    app.add_directive("cpp-apigen-group", CppApigenTopLevelGroupDirective)
    app.add_directive("cpp-apigen-entity-summary", CppApigenEntitySummaryDirective)
    app.add_config_value(
        "cpp_apigen_configs", default=[], rebuild="env", types=(List[ApigenConfig],)
    )
    app.add_config_value(
        "cpp_apigen_case_insensitive_filesystem",
        default=None,
        types=(bool, type(None)),  # type: ignore[arg-type]
        rebuild="env",
    )
    app.add_config_value(
        "cpp_apigen_rst_prolog", types=(str,), default="", rebuild="env"
    )
    app.add_config_value(
        "cpp_apigen_rst_epilog", types=(str,), default="", rebuild="env"
    )
    return {"parallel_read_safe": True, "parallel_write_safe": True}
