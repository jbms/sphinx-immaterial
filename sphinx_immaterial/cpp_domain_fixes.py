"""Fixes for the C and C++ domains."""

import re
from typing import (
    cast,
    Tuple,
    Iterator,
    List,
    Dict,
    Type,
    Optional,
    Union,
    Any,
)

import docutils.nodes
import docutils.parsers.rst.states
import sphinx.addnodes
import sphinx.application
import sphinx.directives
import sphinx.domains.c
import sphinx.domains.cpp
import sphinx.util.logging

from . import apidoc_formatting
from . import sphinx_utils

logger = sphinx.util.logging.getLogger(__name__)

PARAMETER_OBJECT_TYPES = (
    "functionParam",
    "macroParam",
    "templateParam",
    "templateTypeParam",
    "templateTemplateParam",
    "templateNonTypeParam",
)

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
        fieldname = docutils.nodes.field_name("", self.label)
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


class desc_cpp_template_param(sphinx.addnodes.desc_sig_element):
    """Wraps a single template parameter.

    This allows template parameters to be more easily identified when
    transforming docutils nodes.
    """


class desc_cpp_template_params(sphinx.addnodes.desc_sig_element):
    """Wraps an entire template parameter list.

    This allows template parameter lists to be more easily identified when
    transforming docutils nodes.
    """


class desc_cpp_requires_clause(sphinx.addnodes.desc_sig_element):
    """Wraps a c++ requires clause.

    This allows requires clauses to be more easily identified when transforming
    docutils nodes.
    """


class desc_cpp_explicit(sphinx.addnodes.desc_sig_element):
    """Wraps an explicit spec.

    This allows template parameters to be more easily identified when
    transforming docutils nodes.
    """


def _monkey_patch_cpp_ast_template_params():
    ASTTemplateParams = sphinx.domains.cpp.ASTTemplateParams
    orig_describe_signature_as_introducer = (
        ASTTemplateParams.describe_signature_as_introducer
    )

    def describe_signature_as_introducer(
        self: ASTTemplateParams,
        parentNode: sphinx.addnodes.desc_signature,
        mode: str,
        env: sphinx.environment.BuildEnvironment,
        symbol: sphinx.domains.cpp.Symbol,
        lineSpec: bool,
    ) -> None:
        fake_parent = sphinx.addnodes.desc_signature("", "")
        signode = desc_cpp_template_params("", "")
        parentNode += signode
        orig_describe_signature_as_introducer(
            self, signode, mode, env, symbol, lineSpec
        )
        # Ensure the requires clause is not wrapped in
        # `desc_cpp_template_params`.
        if signode.children:
            last_child = signode.children[-1]
            if isinstance(last_child, desc_cpp_requires_clause):
                del signode.children[-1]
                parentNode += last_child
        for x in signode.traverse(condition=sphinx.addnodes.desc_name):
            # Ensure template parameter names aren't styled as the main entity
            # name.
            x["classes"].append("sig-name-nonprimary")

    ASTTemplateParams.describe_signature_as_introducer = (
        describe_signature_as_introducer
    )


def _monkey_patch_cpp_ast_wrap_signature_node(
    ast_type: Any, wrapper_type: Type[docutils.nodes.Element]
):
    """Patches an AST node type to wrap its signature with a docutils node."""
    orig_describe_signature = ast_type.describe_signature

    def describe_signature(
        self: ast_type, signode: docutils.nodes.TextElement, *args, **kwargs
    ) -> None:
        wrapper = wrapper_type("", "")
        signode += wrapper
        orig_describe_signature(self, wrapper, *args, **kwargs)

    ast_type.describe_signature = describe_signature


last_resolved_symbol = None
"""Symbol resolved by `_resolve_xref_inner` or `get_objects`.

This allows additional customizations of those functions to access the symbol.
"""


def _monkey_patch_resolve_xref_save_symbol(symbol_class, domain_class):
    """Monkey patches C/C++ resolve_xref to save the resolved symbol.

    This also other customizations to make use of the resolved symbol.
    """

    orig_resolve_xref_inner = domain_class._resolve_xref_inner

    def _resolve_xref_inner(
        self: sphinx.domains.cpp.CPPDomain,
        env: sphinx.environment.BuildEnvironment,
        fromdocname: str,
        builder: sphinx.builders.Builder,
        typ: str,
        target: str,
        node: sphinx.addnodes.pending_xref,
        contnode: docutils.nodes.Element,
    ) -> Tuple[Optional[docutils.nodes.Element], Optional[str]]:
        global last_resolved_symbol
        last_resolved_symbol = None

        orig_find_name = getattr(symbol_class, "find_name", None)

        if orig_find_name:

            def find_name(self: symbol_class, *args, **kwargs):
                global last_resolved_symbol
                symbols, failReason = orig_find_name(self, *args, **kwargs)
                if symbols:
                    last_resolved_symbol = symbols[0]
                return symbols, failReason

            symbol_class.find_name = find_name

        orig_find_declaration = symbol_class.find_declaration

        def find_declaration(self: symbol_class, *args, **kwargs):
            global last_resolved_symbol
            symbol = orig_find_declaration(self, *args, **kwargs)
            if symbol:
                last_resolved_symbol = symbol
            return symbol

        symbol_class.find_declaration = find_declaration

        try:
            return orig_resolve_xref_inner(
                self, env, fromdocname, builder, typ, target, node, contnode
            )
        finally:
            if orig_find_name:
                symbol_class.find_name = orig_find_name
            symbol_class.find_declaration = orig_find_declaration

    domain_class._resolve_xref_inner = _resolve_xref_inner


POSSIBLE_MACRO_TARGET_PATTERN = re.compile("^[A-Z]+[A-Z_0-9]*(?:::[a-zA-Z0-9_]+)?$")
"""Pattern for targets that may possibly refer to a macro or macro parameter.

Any targets matching this pattern that are not defined as C++ symbols will be
looked up in the C domain.

For efficiency, this is restricted to names that consist of only uppercase
letters and digits, to avoid a duplicate C domain query for all symbols that
will be resolved by `sphinx_immaterial.external_cpp_references`.

Since macro parameters are named as "<MACRO_NAME>::<PARAMETER_NAME>", this
pattern allows "::" even though it would normally only match C++ symbols.
"""

POSSIBLE_MACRO_PARAMETER_TARGET_PATTERN = re.compile("^[a-zA-Z0-9_]+$")
"""Pattern for targets that may refer to a macro parameter within the scope of a
C macro definition.
"""


def _monkey_patch_cpp_resolve_c_xrefs():
    """Patch C and C++ domain resolve_xref implementation.

    This adds support for:

    - Resolving C macros from C++ domain xrefs.  This allows a role like
      `cpp:expr` to match both C++ symbols and C macro and macro parameters.
      https://github.com/sphinx-doc/sphinx/issues/10262

    - Normal resolution of missing symbols starting with `std::`.  Normally, the
      C++ domain silences warnings about these symbols in a way that blocks
      `missing-reference` handlers from receiving them.
    """
    orig_resolve_xref_inner = sphinx.domains.cpp.CPPDomain._resolve_xref_inner

    def _resolve_xref_inner(
        self: sphinx.domains.cpp.CPPDomain,
        env: sphinx.environment.BuildEnvironment,
        fromdocname: str,
        builder: sphinx.builders.Builder,
        typ: str,
        target: str,
        node: sphinx.addnodes.pending_xref,
        contnode: docutils.nodes.Element,
    ) -> Tuple[Optional[docutils.nodes.Element], Optional[str]]:

        try:
            refnode, objtype = orig_resolve_xref_inner(
                self, env, fromdocname, builder, typ, target, node, contnode
            )
        except sphinx.errors.NoUri:
            # Only raised for `std::` symbols.  Give `missing-reference` handlers a
            # change to resolve it.
            return None, None

        if refnode is not None:
            return refnode, objtype

        if POSSIBLE_MACRO_TARGET_PATTERN.match(target) or (
            POSSIBLE_MACRO_PARAMETER_TARGET_PATTERN.match(target)
            and node.get("c:parent_key")
        ):
            # Give C domain a chance to resolve it.
            c_domain = cast(sphinx.domains.c.CDomain, env.get_domain("c"))
            return c_domain._resolve_xref_inner(
                env, fromdocname, builder, typ, target, node, contnode
            )

        return None, None

    sphinx.domains.cpp.CPPDomain._resolve_xref_inner = _resolve_xref_inner


SYNOPSIS_ATTR = "_sphinx_immaterial_synopsis"


def set_synopsis(
    symbol: Union[sphinx.domains.cpp.Symbol, sphinx.domains.c.Symbol], synopsis: str
) -> None:
    """Sets the synopsis for a given symbol."""
    setattr(symbol.declaration, SYNOPSIS_ATTR, synopsis)


def _get_precise_template_parameter_object_type(
    object_type: str, symbol: Optional[sphinx.domains.cpp.Symbol]
) -> str:
    if object_type == "templateParam":
        # Determine more precise object type.
        if symbol is not None:
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


def _monkey_patch_add_object_type_and_synopsis(
    domain_class: Union[
        Type[sphinx.domains.cpp.CPPDomain], Type[sphinx.domains.c.CDomain]
    ]
):
    """Patch C/C++ resolve_xref to add object type-dependent CSS classes."""
    orig_resolve_xref_inner = domain_class._resolve_xref_inner

    def _resolve_xref_inner(
        self: domain_class,
        env: sphinx.environment.BuildEnvironment,
        fromdocname: str,
        builder: sphinx.builders.Builder,
        typ: str,
        target: str,
        node: sphinx.addnodes.pending_xref,
        contnode: docutils.nodes.Element,
    ) -> Tuple[Optional[docutils.nodes.Element], Optional[str]]:
        refnode, objtype = orig_resolve_xref_inner(
            self, env, fromdocname, builder, typ, target, node, contnode
        )
        if refnode is None:
            return refnode, objtype

        objtype = _get_precise_template_parameter_object_type(
            objtype, last_resolved_symbol
        )

        if objtype in (
            "templateTypeParam",
            "templateTemplateParam",
            "class",
            "union",
            "type",
            "enum",
            "concept",
        ):
            refnode["classes"].append("desctype")

        if last_resolved_symbol is not None:
            refnode["reftitle"] = apidoc_formatting.format_object_description_tooltip(
                env,
                apidoc_formatting.get_object_description_options(
                    env, self.name, objtype
                ),
                base_title=refnode["reftitle"],
                synopsis=getattr(last_resolved_symbol.declaration, SYNOPSIS_ATTR, None),
            )

        return refnode, objtype

    domain_class._resolve_xref_inner = _resolve_xref_inner


def _monkey_patch_c_macro_parameter_symbols():
    """Adds support for the `macroParam` object type to the C domain."""
    CSymbol = sphinx.domains.c.Symbol

    ASTMacro = sphinx.domains.c.ASTMacro
    ASTMacroParameter = sphinx.domains.c.ASTMacroParameter
    ASTDeclaration = sphinx.domains.c.ASTDeclaration

    orig_add_function_params = CSymbol._add_function_params

    def _add_function_params(self: CSymbol) -> None:
        orig_add_function_params(self)
        if self.declaration is None or not isinstance(
            self.declaration.declaration, ASTMacro
        ):
            return
        args = self.declaration.declaration.args
        if not args:
            return
        for p in args:
            nn = p.arg
            if nn is None:
                continue
            decl = ASTDeclaration("macroParam", None, p)
            assert not nn.rooted
            assert len(nn.names) == 1
            self._add_symbols(nn, decl, self.docname, self.line)

    CSymbol._add_function_params = _add_function_params

    def get_id(
        self: ASTMacroParameter, version: int, objectType: str, symbol: CSymbol
    ) -> str:
        # the anchor will be our parent
        return symbol.parent.declaration.get_id(version, prefixed=False)

    ASTMacroParameter.get_id = get_id

    sphinx.domains.c.CDomain.object_types["macroParam"] = sphinx.domains.ObjType(
        "macro parameter", "identifier", "var", "member", "data"
    )


def _monkey_patch_cpp_expr_role_to_include_c_parent_key():
    """Includes ``c:parent_key`` in pending_xref nodes created by CPPExprRole.

    This allows CPPExprRole to be used from the context of C object descriptions,
    in particular macros.
    """
    CPPExprRole = sphinx.domains.cpp.CPPExprRole

    orig_run = CPPExprRole.run

    def run(
        self: CPPExprRole,
    ) -> Tuple[List[docutils.nodes.Node], List[docutils.nodes.system_message]]:
        nodes, messages = orig_run(self)
        c_parent_key = self.env.ref_context.get("c:parent_key")
        if c_parent_key is not None:
            for node in nodes:
                for refnode in node.traverse(condition=sphinx.addnodes.pending_xref):
                    if refnode.get("refdomain") == "cpp":
                        refnode["c:parent_key"] = c_parent_key
        return nodes, messages

    CPPExprRole.run = run


ANCHOR_ATTR = "sphinx_immaterial_anchor"


def get_symbol_anchor(symbol):
    anchor = getattr(symbol.declaration, ANCHOR_ATTR, None)
    if anchor is None:
        anchor = symbol.declaration.get_newest_id()
    return anchor


OBJECT_PRIORITY_DEFAULT = 1
OBJECT_PRIORITY_UNIMPORTANT = 2


def _monkey_patch_cpp_add_precise_template_parameter_object_types():
    """Adds more precise template{Type,NonType,Template}Param object types."""
    sphinx.domains.cpp.CPPDomain.object_types[
        "templateTypeParam"
    ] = sphinx.domains.ObjType(
        "type template parameter",
        "identifier",
        "class",
        "struct",
        "union",
        "type",
    )
    sphinx.domains.cpp.CPPDomain.object_types[
        "templateNonTypeParam"
    ] = sphinx.domains.ObjType(
        "non-type template parameter", "identifier", "member", "var"
    )
    sphinx.domains.cpp.CPPDomain.object_types[
        "templateTemplateParam"
    ] = sphinx.domains.ObjType(
        "template template parameter", "identifier", "member", "var"
    )

    def get_objects(
        self: sphinx.domains.cpp.CPPDomain,
    ) -> Iterator[Tuple[str, str, str, str, str, int]]:
        global last_resolved_symbol
        rootSymbol = self.data["root_symbol"]
        for symbol in rootSymbol.get_all_symbols():
            if symbol.declaration is None:
                continue
            assert symbol.docname
            fullNestedName = symbol.get_full_nested_name()
            name = str(fullNestedName).lstrip(":")
            dispname = fullNestedName.get_display_string().lstrip(":")
            objectType = _get_precise_template_parameter_object_type(
                symbol.declaration.objectType, symbol
            )
            docname = symbol.docname
            anchor = get_symbol_anchor(symbol)
            # Allow other customizations to access the symbol.
            last_resolved_symbol = symbol
            if objectType in PARAMETER_OBJECT_TYPES:
                priority = OBJECT_PRIORITY_UNIMPORTANT
            else:
                priority = OBJECT_PRIORITY_DEFAULT
            yield (name, dispname, objectType, docname, anchor, priority)

    sphinx.domains.cpp.CPPDomain.get_objects = get_objects


def _strip_namespaces_from_signature(
    node: docutils.nodes.Element, namespaces: List[str]
):
    # Collect nodes to remove first, then remove them in reverse order.
    removals = []
    for child in node.traverse(condition=sphinx.addnodes.desc_sig_name):
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

    for (parent, index) in removals:
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
        _strip_namespaces_from_signature(signode, namespaces)


def _monkey_patch_domain_to_support_include_directives(
    object_class: Type[sphinx.directives.ObjectDescription], language: str
):

    orig_get_signatures = object_class.get_signatures

    def is_include(sig: str) -> bool:
        return sig.startswith("#")

    def get_signatures(self: object_class) -> List[str]:
        return [sig for sig in orig_get_signatures(self) if not is_include(sig)]

    object_class.get_signatures = get_signatures

    orig_run = object_class.run

    def run(self: object_class) -> List[docutils.nodes.Node]:
        nodes = orig_run(self)
        include_directives = [
            sig for sig in orig_get_signatures(self) if is_include(sig)
        ]
        if include_directives:
            obj_desc = nodes[-1]
            include_sig = sphinx.addnodes.desc_signature("", "")
            include_sig["classes"].append("api-include-path")
            for directive in include_directives:
                container = docutils.nodes.container()
                container += docutils.nodes.literal(
                    directive,
                    directive,
                    classes=[language, "code", "highlight"],
                    language=language,
                )
                include_sig.append(container)

            self.set_source_info(include_sig)
            obj_desc.insert(0, include_sig)
        return nodes

    object_class.run = run


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
        for name_node_copy in param_node_copy.traverse(condition=type(name_node)):
            if name_node_copy.get(node_identifier_key):
                return name_node_copy
        raise ValueError("Could not locate name node within parameter")

    for sig_param_node in signode.traverse(condition=sphinx.addnodes.desc_sig_name):
        desc_param_node = sig_param_node.parent
        if not isinstance(desc_param_node, sphinx.addnodes.desc_parameter):
            continue
        while not isinstance(desc_param_node, sphinx.addnodes.desc_parameter):
            desc_param_node = desc_param_node.parent
        new_sig_param_node = add_replacement(sig_param_node, sig_param_node.parent)
        new_sig_param_node["classes"].append("sig-name")

    for desc_sig_name_node in signode.traverse(condition=sphinx.addnodes.desc_sig_name):
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
) -> None:

    domain = obj_content.parent["domain"]

    qualify_parameter_ids = env.config.cpp_qualify_parameter_ids

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
                "Parameter name %r does not match any of the parameters "
                "defined in the signature: %r",
                param_name,
                list(all_params.keys()),
                location=param_node,
            )
            return

        object_type = None
        synopsis = None

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
                object_type = _get_precise_template_parameter_object_type(
                    param_symbol.declaration.objectType, param_symbol
                )
                param_options = apidoc_formatting.get_object_description_options(
                    env, domain, object_type
                )
                generate_synopses = param_options["generate_synopses"]
                if generate_synopses is not None:
                    synopsis = sphinx_utils.summarize_element_text(
                        param_node.parent[-1], generate_synopses
                    )

            if synopsis:
                set_synopsis(param_symbol, synopsis)

            param_id_suffix = f"p-{param_name}"

            # Set symbol id, since by default parameters don't have unique ids,
            # they just use the same id as the parent symbol.  This is
            # neccessary in order for cross links to correctly refer to the
            # parameter description.
            setattr(
                param_symbol.declaration,
                AST_ID_OVERRIDE_ATTR,
                parent_symbol.declaration.get_newest_id() + "-" + param_id_suffix,
            )

            if qualify_parameter_ids:
                # Generate a separate id for each id version.
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
            else:
                id_prefixes = [""]
                setattr(param_symbol.declaration, ANCHOR_ATTR, param_id_suffix)

            if id_prefixes:
                for id_prefix in id_prefixes:
                    param_id = id_prefix + param_id_suffix
                    param_node["ids"].append(param_id)

        if object_type is not None:
            if param_options["include_in_toc"]:
                toc_title = param_name
                if kind:
                    toc_title += f" [{kind}]"
                param_node["toc_title"] = toc_title

        if not qualify_parameter_ids:
            param_node["ids"].append(param_id_suffix)

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
    # sure not to find parameter descriptions within neted object descriptions.
    # For example, if this is a class object description, we don't want to find
    # parameter descriptions within a nested function object description.
    for child in obj_content:
        if not isinstance(child, docutils.nodes.field_list):
            continue
        for field in child:
            field_body = field[-1]
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
    content: docutils.nodes.Element,
    symbols,
) -> None:
    obj_desc = content.parent

    signodes = [
        signode
        for signode in obj_desc.children[:-1]
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
    )


def _monkey_patch_domain_to_cross_link_parameters_and_add_synopses(
    object_class: Type[sphinx.directives.ObjectDescription],
    domain: str,
):

    orig_after_content = object_class.after_content

    orig_transform_content = object_class.transform_content

    def transform_content(self: object_class, contentnode) -> None:
        self.contentnode = contentnode
        orig_transform_content(self, contentnode)

    object_class.transform_content = transform_content

    def after_content(self: object_class) -> None:
        symbols = [self.env.temp_data[f"{domain}:parent_symbol"]]
        while symbols[-1].siblingAbove:
            symbols.append(symbols[-1].siblingAbove)
        symbols.reverse()
        _cross_link_parameters(
            app=self.env.app, domain=domain, content=self.contentnode, symbols=symbols
        )

        options = apidoc_formatting.get_object_description_options(
            self.env, self.domain, self.objtype
        )
        generate_synopses = options["generate_synopses"]

        if generate_synopses is not None:
            synopsis = sphinx_utils.summarize_element_text(
                self.contentnode, generate_synopses
            )
            if synopsis:
                for symbol in symbols:
                    set_synopsis(symbol, synopsis)
        orig_after_content(self)

    object_class.after_content = after_content


AST_ID_OVERRIDE_ATTR = "_sphinx_immaterial_id"


def _monkey_patch_override_ast_id(ast_declaration_class):
    """Allows the Symbol id to be overridden."""
    orig_get_id = ast_declaration_class.get_id

    def get_id(self: ast_declaration_class, version: int, prefixed: bool = True):
        entity_id = getattr(self, AST_ID_OVERRIDE_ATTR, None)
        if entity_id is not None:
            return entity_id
        return orig_get_id(self, version, prefixed)

    ast_declaration_class.get_id = get_id


def _monkey_patch_domain_get_object_synopses(domain_class):
    def get_object_synopses(
        self: domain_class,
    ) -> Iterator[Tuple[Tuple[str, str], str]]:
        for symbol in self.data["root_symbol"].get_all_symbols():
            if symbol.declaration is None:
                continue
            assert symbol.docname
            synopsis = getattr(symbol.declaration, SYNOPSIS_ATTR, None)
            if not synopsis:
                continue
            yield ((symbol.docname, symbol.declaration.get_newest_id()), synopsis)

    domain_class.get_object_synopses = get_object_synopses


def setup(app: sphinx.application.Sphinx):
    _monkey_patch_cpp_parameter_fields(sphinx.domains.cpp.CPPObject.doc_field_types)
    _monkey_patch_cpp_parameter_fields(
        sphinx.domains.cpp.CPPFunctionObject.doc_field_types
    )
    _monkey_patch_cpp_parameter_fields(sphinx.domains.c.CObject.doc_field_types)
    _monkey_patch_cpp_parameter_fields(sphinx.domains.c.CFunctionObject.doc_field_types)
    _monkey_patch_cpp_parameter_fields(sphinx.domains.c.CMacroObject.doc_field_types)

    _monkey_patch_cpp_ast_template_params()
    for ast_type in (
        sphinx.domains.cpp.ASTTemplateParamType,
        sphinx.domains.cpp.ASTTemplateParamTemplateType,
        sphinx.domains.cpp.ASTTemplateParamNonType,
    ):
        _monkey_patch_cpp_ast_wrap_signature_node(
            ast_type=ast_type, wrapper_type=desc_cpp_template_param
        )
    _monkey_patch_cpp_ast_wrap_signature_node(
        ast_type=sphinx.domains.cpp.ASTExplicitSpec, wrapper_type=desc_cpp_explicit
    )
    _monkey_patch_cpp_ast_wrap_signature_node(
        ast_type=sphinx.domains.cpp.ASTRequiresClause,
        wrapper_type=desc_cpp_requires_clause,
    )
    for node in (
        desc_cpp_template_param,
        desc_cpp_template_params,
        desc_cpp_requires_clause,
        desc_cpp_explicit,
    ):
        app.add_node(node)
        sphinx.addnodes.SIG_ELEMENTS.append(node)

    # We monkey patch `resolve_xref` multiple times.  We must call
    # `_monkey_patch_cpp_resolve_c_xrefs` last, to ensure that the other logic
    # only runs once.
    _monkey_patch_resolve_xref_save_symbol(
        sphinx.domains.cpp.Symbol, sphinx.domains.cpp.CPPDomain
    )
    _monkey_patch_resolve_xref_save_symbol(
        sphinx.domains.c.Symbol, sphinx.domains.c.CDomain
    )
    _monkey_patch_add_object_type_and_synopsis(sphinx.domains.c.CDomain)
    _monkey_patch_add_object_type_and_synopsis(sphinx.domains.cpp.CPPDomain)
    _monkey_patch_cpp_resolve_c_xrefs()

    _monkey_patch_c_macro_parameter_symbols()
    _monkey_patch_cpp_expr_role_to_include_c_parent_key()

    _monkey_patch_domain_to_support_include_directives(
        object_class=sphinx.domains.cpp.CPPObject, language="cpp"
    )
    _monkey_patch_domain_to_support_include_directives(
        object_class=sphinx.domains.c.CObject, language="c"
    )

    app.add_config_value(
        "cpp_strip_namespaces_from_signatures",
        default=[],
        rebuild="env",
        types=(List[str],),
    )
    app.add_config_value(
        "cpp_qualify_parameter_ids", default=True, rebuild="env", types=(bool,)
    )
    app.connect("object-description-transform", _strip_namespaces_from_signatures)

    _monkey_patch_domain_to_cross_link_parameters_and_add_synopses(
        sphinx.domains.cpp.CPPObject, domain="cpp"
    )
    _monkey_patch_domain_to_cross_link_parameters_and_add_synopses(
        sphinx.domains.c.CObject, domain="c"
    )

    _monkey_patch_override_ast_id(sphinx.domains.c.ASTDeclaration)
    _monkey_patch_override_ast_id(sphinx.domains.cpp.ASTDeclaration)
    _monkey_patch_domain_get_object_synopses(sphinx.domains.c.CDomain)
    _monkey_patch_domain_get_object_synopses(sphinx.domains.cpp.CPPDomain)
    _monkey_patch_cpp_add_precise_template_parameter_object_types()

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
