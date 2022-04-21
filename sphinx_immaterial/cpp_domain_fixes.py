"""Fixes for the C and C++ domains."""

import re
from typing import (
    cast,
    Tuple,
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
                term_node["toc_title"] = f"{param_name} [{kind}]"
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


def _monkey_patch_add_object_type_css_classes(
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

        if objtype in ("class", "union", "type", "enum", "templateParam", "concept"):
            refnode["classes"].append("desctype")

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

    _monkey_patch_cpp_resolve_c_xrefs()

    _monkey_patch_c_macro_parameter_symbols()
    _monkey_patch_cpp_expr_role_to_include_c_parent_key()
    _monkey_patch_add_object_type_css_classes(sphinx.domains.c.CDomain)
    _monkey_patch_add_object_type_css_classes(sphinx.domains.cpp.CPPDomain)

    _monkey_patch_domain_to_support_include_directives(
        object_class=sphinx.domains.cpp.CPPObject, language="cpp"
    )
    _monkey_patch_domain_to_support_include_directives(
        object_class=sphinx.domains.c.CObject, language="c"
    )

    app.add_config_value(
        "cpp_strip_namespaces_from_signatures", default=[], rebuild="env"
    )
    app.connect("object-description-transform", _strip_namespaces_from_signatures)

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
