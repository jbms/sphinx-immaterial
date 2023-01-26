import re
from typing import cast, Optional, Dict, List, Tuple, Iterator, Type, Union

import docutils.nodes
import docutils.parsers.rst.states
import sphinx.directives
import sphinx.domains.c
import sphinx.domains.cpp
import sphinx.environment
import sphinx.util.docfields
import sphinx.util.logging

from . import last_resolved_symbol
from . import symbol_ids
from .signodes import desc_cpp_template_param

from .. import object_description_options
from ... import sphinx_utils
from . import synopses

logger = sphinx.util.logging.getLogger(__name__)


CPP_PARAM_KIND_PATTERN = re.compile(r"([^\[]+)\[([^\]]+)\]$")
"""Regular expression pattern for matching parameter names with a "kind" suffix.

For example, "param[in]" or "param[out]" or "param[in, out]" all match with
kinds of "in", "out", and "in, out" respectively.
"""


class CppParamField(sphinx.util.docfields.GroupedField):
    def make_field(
        self,
        types: Dict[str, List[docutils.nodes.Node]],
        domain: str,
        items: Tuple,
        env: Optional[sphinx.environment.BuildEnvironment] = None,
        inliner: Optional[docutils.parsers.rst.states.Inliner] = None,
        location: Optional[docutils.nodes.Node] = None,
    ) -> docutils.nodes.field:
        bodynode = docutils.nodes.definition_list()
        bodynode["classes"].append("api-field")
        bodynode["classes"].append("highlight")

        def handle_item(
            fieldarg: str, content: List[docutils.nodes.Node]
        ) -> docutils.nodes.Node:
            node = docutils.nodes.definition_list_item()
            term_node = docutils.nodes.term()
            m = CPP_PARAM_KIND_PATTERN.fullmatch(fieldarg)
            kind: Optional[str]
            if m is not None:
                param_name = m.group(1)
                kind = m.group(2).strip()
            else:
                param_name = fieldarg
                kind = None
            term_node["paramname"] = param_name
            if kind is not None:
                term_node["param_kind"] = kind
            term_node += sphinx.addnodes.desc_name(param_name, param_name)
            node += term_node
            def_node = docutils.nodes.definition()
            p = docutils.nodes.paragraph()
            p += content
            def_node += p
            node += def_node
            return node

        for fieldarg, content in items:
            bodynode += handle_item(fieldarg, content)
        fieldname = docutils.nodes.field_name("", cast(str, self.label))
        fieldbody = docutils.nodes.field_body("", bodynode)
        return docutils.nodes.field("", fieldname, fieldbody)


def _monkey_patch_cpp_parameter_fields(doc_field_types):
    for i, field in enumerate(doc_field_types):
        if field.name in ("parameter", "template parameter"):
            doc_field_types[i] = CppParamField(
                name=field.name,
                names=field.names,
                label=field.label,
                rolename=field.rolename,
                can_collapse=field.can_collapse,
            )


OBJECT_PRIORITY_DEFAULT = 1
OBJECT_PRIORITY_UNIMPORTANT = 2


def get_precise_template_parameter_object_type(
    object_type: str, symbol: Optional[sphinx.domains.cpp.Symbol]
) -> str:
    if object_type == "templateParam":
        # Determine more precise object type.
        if symbol is not None:
            assert symbol.declaration is not None
            if isinstance(
                symbol.declaration.declaration,
                sphinx.domains.cpp.ASTTemplateParamNonType,
            ):
                object_type = "templateNonTypeParam"
            elif isinstance(
                symbol.declaration.declaration,
                sphinx.domains.cpp.ASTTemplateParamTemplateType,
            ):
                object_type = "templateTemplateParam"
            else:
                object_type = "templateTypeParam"

    return object_type


def _monkey_patch_cpp_add_precise_template_parameter_object_types():
    """Adds more precise template{Type,NonType,Template}Param object types."""
    sphinx.domains.cpp.CPPDomain.object_types["templateTypeParam"] = (
        sphinx.domains.ObjType(
            "type template parameter",
            "identifier",
            "class",
            "struct",
            "union",
            "type",
        )
    )
    sphinx.domains.cpp.CPPDomain.object_types["templateNonTypeParam"] = (
        sphinx.domains.ObjType(
            "non-type template parameter", "identifier", "member", "var"
        )
    )
    sphinx.domains.cpp.CPPDomain.object_types["templateTemplateParam"] = (
        sphinx.domains.ObjType(
            "template template parameter", "identifier", "member", "var"
        )
    )


def _monkey_patch_domain_get_objects(
    domain_class: Union[
        Type[sphinx.domains.cpp.CPPDomain], Type[sphinx.domains.c.CDomain]
    ],
):
    """Monkey patches `get_objects` to better handle parameter objects.

    Parameter objects are assigned `OBJECT_PRIORITY_UNIMPORTANT`.

    Also adds support for overridden symbol anchors.
    """

    def get_objects(
        self: Union[sphinx.domains.cpp.CPPDomain, sphinx.domains.c.CDomain],
    ) -> Iterator[Tuple[str, str, str, str, str, int]]:
        rootSymbol = self.data["root_symbol"]
        for symbol in rootSymbol.get_all_symbols():
            if (
                symbol.declaration is None
                or getattr(symbol.declaration, symbol_ids.AST_ID_OVERRIDE_ATTR, None)
                is None
            ):
                continue
            assert symbol.docname
            last_resolved_symbol.set_symbol(symbol)
            fullNestedName = symbol.get_full_nested_name()
            name = str(fullNestedName).lstrip(":")
            dispname = fullNestedName.get_display_string().lstrip(":")
            objectType = get_precise_template_parameter_object_type(
                symbol.declaration.objectType, symbol
            )
            docname = symbol.docname
            anchor = symbol_ids.get_symbol_anchor(symbol)
            if objectType in symbol_ids.PARAMETER_OBJECT_TYPES:
                priority = OBJECT_PRIORITY_UNIMPORTANT
            else:
                priority = OBJECT_PRIORITY_DEFAULT
            yield (name, dispname, objectType, docname, anchor, priority)

    domain_class.get_objects = get_objects  # type: ignore[assignment]


def _add_parameter_links_to_signature(
    env, signode: sphinx.addnodes.desc_signature, symbol, domain: str
) -> Dict[str, docutils.nodes.Element]:
    """Cross-links parameter names in signature to parameter objects.

    Returns:
      Map of parameter name to original (not linked) parameter node.
    """
    sig_param_nodes: Dict[str, docutils.nodes.Element] = {}

    replacements = []
    node_identifier_key = "sphinx_immaterial_param_name_identifier"

    def add_replacement(
        name_node: docutils.nodes.Element, param_node: docutils.nodes.Element
    ) -> docutils.nodes.Element:
        replacements.append((name_node, param_node))
        name = name_node.astext()
        # Mark `name_node` so that it can be identified after the deep copy of its
        # ancestor `param_node`.
        name_node[node_identifier_key] = True
        param_node_copy = param_node.deepcopy()
        source, line = docutils.utils.get_source_line(param_node)
        param_node_copy.source = source
        param_node_copy.line = line
        sig_param_nodes[name] = param_node_copy
        del name_node[node_identifier_key]
        for name_node_copy in param_node_copy.findall(condition=type(name_node)):
            if name_node_copy.get(node_identifier_key):
                return name_node_copy
        raise ValueError("Could not locate name node within parameter")

    for sig_param_node in signode.findall(condition=sphinx.addnodes.desc_sig_name):
        desc_param_node = sig_param_node.parent
        if not isinstance(desc_param_node, sphinx.addnodes.desc_parameter):
            continue
        while not isinstance(desc_param_node, sphinx.addnodes.desc_parameter):
            desc_param_node = desc_param_node.parent
        new_sig_param_node = add_replacement(sig_param_node, sig_param_node.parent)
        new_sig_param_node["classes"].append("sig-name")

    for desc_sig_name_node in signode.findall(condition=sphinx.addnodes.desc_sig_name):
        parent = desc_sig_name_node.parent
        if not isinstance(parent, sphinx.addnodes.desc_name):
            continue
        grandparent = parent.parent
        if not isinstance(grandparent, desc_cpp_template_param):
            continue
        new_sig_name_node = add_replacement(desc_sig_name_node, grandparent)
        new_sig_name_node.parent["classes"].remove("sig-name-nonprimary")

    lookup_key = symbol.get_lookup_key()

    for name_node, param_node in replacements:
        name = name_node.astext()
        refnode = sphinx.addnodes.pending_xref(
            "",
            name_node.deepcopy(),
            refdomain="cpp",
            reftype="identifier",
            reftarget=name,
            refwarn=True,
        )
        refnode[f"{domain}:parent_key"] = lookup_key
        name_node.replace_self(refnode)

    return sig_param_nodes


def _add_parameter_documentation_ids(
    env,
    obj_content: sphinx.addnodes.desc_content,
    sig_param_nodes_for_signature: List[Dict[str, docutils.nodes.Element]],
    symbols,
    domain_module,
    starting_id_version,
    signodes: List[sphinx.addnodes.desc_signature],
) -> None:
    domain = obj_content.parent["domain"]

    def cross_link_single_parameter(
        param_name: str, param_node: docutils.nodes.term
    ) -> None:
        kind = param_node.get("param_kind")

        # Determine the number of unique declarations of this parameter.
        #
        # If this single object description has multiple signatures, the same
        # parameter name may be declared in more than one of those signatures.
        # In the parameter description, we will replace the bare parameter name
        # with the list of all of the distinct declarations of the parameter.
        # Identical declarations in more than one signature will only be
        # included once.
        unique_decls: Dict[str, Tuple[int, docutils.nodes.Element]] = {}
        for i, sig_param_nodes in enumerate(sig_param_nodes_for_signature):
            desc_param_node = sig_param_nodes.get(param_name)
            if desc_param_node is None:
                continue
            decl_text = desc_param_node.astext().strip()
            unique_decls.setdefault(decl_text, (i, desc_param_node))
        if not unique_decls:
            all_params = {}
            for sig_param_nodes in sig_param_nodes_for_signature:
                all_params.update(sig_param_nodes)
            logger.warning(
                "Parameter name %r does not match any of the parameters %r "
                "defined in the signature(s): %r",
                param_name,
                list(all_params.keys()),
                [signode.astext() for signode in signodes],
                location=param_node,
            )
            return

        object_type = None
        synopsis = None
        param_id_suffix = f"p-{param_name}"

        # Set ids of the parameter node.
        for symbol_i, _ in unique_decls.values():
            parent_symbol = symbols[symbol_i]
            param_symbol = parent_symbol.find_identifier(
                domain_module.ASTIdentifier(param_name),
                matchSelf=False,
                recurseInAnon=False,
                searchInSiblings=False,
            )
            if param_symbol is None or param_symbol.declaration is None:
                logger.warning(
                    "Failed to find parameter symbol: %r",
                    param_name,
                    location=param_node,
                )
                continue

            if object_type is None:
                object_type = get_precise_template_parameter_object_type(
                    param_symbol.declaration.objectType, param_symbol
                )
                param_options = (
                    object_description_options.get_object_description_options(
                        env, domain, object_type
                    )
                )
                generate_synopses = param_options["generate_synopses"]
                if generate_synopses is not None:
                    synopsis = sphinx_utils.summarize_element_text(
                        cast(docutils.nodes.Element, param_node.parent[-1]),
                        generate_synopses,
                    )
                first_match = True
            else:
                first_match = False

            if synopsis:
                synopses.set_synopsis(param_symbol, synopsis)

            # Set symbol id, since by default parameters don't have unique ids,
            # they just use the same id as the parent symbol.  This is
            # necessary in order for cross links to correctly refer to the
            # parameter description.
            setattr(
                param_symbol.declaration,
                symbol_ids.AST_ID_OVERRIDE_ATTR,
                parent_symbol.declaration.get_newest_id() + "-" + param_id_suffix,
            )

            parent_symbol_anchor = getattr(
                parent_symbol.declaration, symbol_ids.ANCHOR_ATTR, None
            )

            if parent_symbol_anchor is None:
                # Generate a separate anchor for each id version.
                prev_parent_id = None
                id_prefixes = []

                for i in range(starting_id_version, domain_module._max_id + 1):
                    try:
                        parent_id = parent_symbol.declaration.get_id(version=i)
                        if parent_id == prev_parent_id:
                            continue
                        prev_parent_id = parent_id
                        id_prefixes.append(parent_id + "-")
                    except domain_module.NoOldIdError:
                        continue

                for id_prefix in id_prefixes:
                    param_id = id_prefix + param_id_suffix
                    param_node["ids"].append(param_id)
            else:
                # Use a single anchor
                param_id_prefix = (
                    f"{parent_symbol_anchor}-" if parent_symbol_anchor else ""
                )
                setattr(
                    param_symbol.declaration,
                    symbol_ids.ANCHOR_ATTR,
                    param_id_prefix + param_id_suffix,
                )
                if first_match:
                    param_node["ids"].append(param_id_prefix + param_id_suffix)

        if object_type is not None:
            if param_options["include_in_toc"]:
                toc_title = param_name
                if kind:
                    toc_title += f" [{kind}]"
                param_node["toc_title"] = toc_title

        del param_node[:]

        new_param_nodes = []

        # Add the parameter kind/direction (e.g. "in" or "out" or "in, out") if
        # present.
        if kind:
            kind_node = docutils.nodes.term(kind, kind)
            kind_node["classes"].append("api-parameter-kind")
            new_param_nodes.append(kind_node)

        # Replace the bare parameter name with the unique parameter
        # declarations.
        for i, desc_param_node in unique_decls.values():
            new_param_node = param_node.deepcopy()
            if i != 0:
                del new_param_node["ids"][:]
            source, line = docutils.utils.get_source_line(desc_param_node)
            new_children = list(c.deepcopy() for c in desc_param_node.children)
            new_param_node.extend(new_children)
            for child in new_children:
                child.source = source
                child.line = line
            new_param_nodes.append(new_param_node)
        param_node.parent[:1] = new_param_nodes

    # Find all parameter descriptions within the object description body.  Make
    # sure not to find parameter descriptions within nested object descriptions.
    # For example, if this is a class object description, we don't want to find
    # parameter descriptions within a nested function object description.
    for child in obj_content:
        if not isinstance(child, docutils.nodes.field_list):
            continue
        for field in child:
            assert isinstance(field, docutils.nodes.field)
            field_body = field[-1]
            assert isinstance(field_body, docutils.nodes.field_body)
            for field_body_child in field_body.children:
                if (
                    not isinstance(field_body_child, docutils.nodes.definition_list)
                    or "api-field" not in field_body_child["classes"]
                ):
                    continue
                for definition in field_body_child.children:
                    if (
                        not isinstance(definition, docutils.nodes.definition_list_item)
                        or len(definition.children) == 0
                    ):
                        continue
                    term = definition[0]
                    if not isinstance(term, docutils.nodes.term):
                        continue
                    param_name = term.get("paramname")
                    if not param_name:
                        continue
                    cross_link_single_parameter(param_name, term)


_FIRST_PARAMETER_ID_VERSIONS: Dict[str, int] = {"c": 1, "cpp": 4}
"""First id version to include when generating parameter ids.

Multiple id versions allow old anchors to work on new versions of the
documentation (as long as the signatures remain identical).

However, there is no need to support id versions from before this support was
added to the theme.
"""


def _cross_link_parameters(
    app: sphinx.application.Sphinx,
    domain: str,
    content: sphinx.addnodes.desc_content,
    symbols,
) -> None:
    obj_desc = content.parent

    signodes = [
        signode
        for signode in cast(
            List[sphinx.addnodes.desc_signature], obj_desc.children[:-1]
        )
        if "api-include-path" not in signode["classes"]
    ]

    assert len(signodes) == len(symbols)

    # Collect the docutils nodes corresponding to the declarations of the
    # parameters in each signature, and turn the parameter names into
    # cross-links to the parameter description.
    #
    # In the parameter descriptions (e.g. in the "Parameters" or "Template
    # Parameters" fields), these declarations will be copied in to replace the
    # bare parameter name so that the parameter description shows e.g. `int x =
    # 10` or `typename T` rather than just `x` or `T`.
    sig_param_nodes_for_signature = []
    for signode, symbol in zip(signodes, symbols):
        sig_param_nodes_for_signature.append(
            _add_parameter_links_to_signature(app.env, signode, symbol, domain=domain)
        )

    # Find all parameter descriptions in the object description body, and mark
    # them as the target for cross links to that parameter.  Also substitute in
    # the parameter declaration for the bare parameter name, as described above.
    _add_parameter_documentation_ids(
        env=app.env,
        obj_content=content,
        sig_param_nodes_for_signature=sig_param_nodes_for_signature,
        symbols=symbols,
        domain_module=getattr(sphinx.domains, domain),
        starting_id_version=_FIRST_PARAMETER_ID_VERSIONS[domain],
        signodes=signodes,
    )


def _monkey_patch_domain_to_cross_link_parameters_and_add_synopses(
    object_class: Type[sphinx.directives.ObjectDescription],
    domain: str,
):
    orig_after_content = object_class.after_content

    orig_transform_content = object_class.transform_content

    def transform_content(
        self: sphinx.directives.ObjectDescription,
        contentnode: sphinx.addnodes.desc_content,
    ) -> None:
        setattr(self, "contentnode", contentnode)
        orig_transform_content(self, contentnode)

    object_class.transform_content = transform_content  # type: ignore

    def after_content(self: sphinx.directives.ObjectDescription) -> None:
        symbols = [self.env.temp_data[f"{domain}:parent_symbol"]]
        while symbols[-1].siblingAbove:
            symbols.append(symbols[-1].siblingAbove)
        symbols.reverse()
        _cross_link_parameters(
            app=self.env.app,
            domain=domain,
            content=getattr(self, "contentnode"),
            symbols=symbols,
        )

        options = object_description_options.get_object_description_options(
            self.env, self.domain, self.objtype
        )
        generate_synopses = options["generate_synopses"]

        if generate_synopses is not None:
            synopsis = sphinx_utils.summarize_element_text(
                getattr(self, "contentnode"), generate_synopses
            )
            if synopsis:
                for symbol in symbols:
                    synopses.set_synopsis(symbol, synopsis)
        orig_after_content(self)

    object_class.after_content = after_content  # type: ignore


_monkey_patch_cpp_parameter_fields(sphinx.domains.cpp.CPPObject.doc_field_types)
_monkey_patch_cpp_parameter_fields(sphinx.domains.cpp.CPPFunctionObject.doc_field_types)
_monkey_patch_cpp_parameter_fields(sphinx.domains.c.CObject.doc_field_types)
_monkey_patch_cpp_parameter_fields(sphinx.domains.c.CFunctionObject.doc_field_types)
_monkey_patch_cpp_parameter_fields(sphinx.domains.c.CMacroObject.doc_field_types)
_monkey_patch_cpp_add_precise_template_parameter_object_types()

_monkey_patch_domain_to_cross_link_parameters_and_add_synopses(
    sphinx.domains.cpp.CPPObject, domain="cpp"
)
_monkey_patch_domain_to_cross_link_parameters_and_add_synopses(
    sphinx.domains.c.CObject, domain="c"
)
_monkey_patch_domain_get_objects(sphinx.domains.c.CDomain)
_monkey_patch_domain_get_objects(sphinx.domains.cpp.CPPDomain)
