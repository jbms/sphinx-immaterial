"""Fixes for the Python domain."""

from typing import (
    cast,
    Sequence,
    Tuple,
    List,
    Dict,
    Type,
    Optional,
    Any,
    Iterator,
)

import docutils.nodes
import docutils.parsers.rst.states
import sphinx.addnodes
import sphinx.application
import sphinx.domains.python
import sphinx.ext.napoleon
import sphinx.util.logging
import sphinx.util.nodes

from . import apidoc_formatting
from . import sphinx_utils

logger = sphinx.util.logging.getLogger(__name__)


def _ensure_wrapped_in_desc_type(
    nodes: List[docutils.nodes.Node],
) -> List[docutils.nodes.Node]:
    if len(nodes) != 1 or not isinstance(nodes[0], sphinx.addnodes.desc_type):
        nodes = [sphinx.addnodes.desc_type("", "", *nodes)]
    return nodes


def _monkey_patch_python_doc_fields():
    PyTypedField = sphinx.domains.python.PyTypedField

    def make_field(
        self: PyTypedField,
        types: Dict[str, List[docutils.nodes.Node]],
        domain: str,
        items: Sequence[Tuple[str, str]],
        env: Optional[sphinx.environment.BuildEnvironment] = None,
        inliner: Optional[docutils.parsers.rst.states.Inliner] = None,
        location: Optional[docutils.nodes.Node] = None,
    ) -> docutils.nodes.field:
        bodynode = docutils.nodes.definition_list()
        bodynode["classes"].append("api-field")
        bodynode["classes"].append("highlight")

        def handle_item(fieldarg: str, content: Any) -> docutils.nodes.Node:
            node = docutils.nodes.definition_list_item()
            term_node = docutils.nodes.term()
            term_node["paramname"] = fieldarg
            term_node += sphinx.addnodes.desc_name(fieldarg, fieldarg)
            fieldtype = types.pop(fieldarg, None)
            if fieldtype:
                term_node += sphinx.addnodes.desc_sig_punctuation("", " : ")
                fieldtype_node = sphinx.addnodes.desc_type()
                if len(fieldtype) == 1 and isinstance(
                    fieldtype[0], docutils.nodes.Text
                ):
                    typename = fieldtype[0].astext()
                    term_node["paramtype"] = typename
                    fieldtype_node.extend(
                        _ensure_wrapped_in_desc_type(
                            self.make_xrefs(
                                self.typerolename,
                                domain,
                                typename,
                                docutils.nodes.Text,
                                env=env,
                                inliner=inliner,
                                location=location,
                            )
                        )
                    )
                else:
                    fieldtype_node += fieldtype
                term_node += fieldtype_node
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

    PyTypedField.make_field = make_field


def _monkey_patch_python_parse_annotation():
    """Ensures that type annotations in signatures are wrapped in `desc_type`.

    This allows them to be distinguished from parameter names in CSS rules.
    """
    orig_parse_annotation = sphinx.domains.python._parse_annotation

    def parse_annotation(
        annotation: str, env: Optional[sphinx.environment.BuildEnvironment] = None
    ) -> List[docutils.nodes.Node]:
        return _ensure_wrapped_in_desc_type(orig_parse_annotation(annotation, env))

    sphinx.domains.python._parse_annotation = parse_annotation


def _monkey_patch_python_parse_arglist():
    """Ensures default values in signatures are styled as code."""

    orig_parse_arglist = sphinx.domains.python._parse_arglist

    def parse_arglist(
        arglist: str, env: Optional[sphinx.environment.BuildEnvironment] = None
    ) -> sphinx.addnodes.desc_parameterlist:
        result = orig_parse_arglist(arglist, env)
        for node in result.traverse(condition=docutils.nodes.inline):
            if "default_value" not in node["classes"]:
                continue
            node.replace_self(
                docutils.nodes.literal(
                    text=node.astext(),
                    classes=["code", "python", "default_value"],
                    language="python",
                )
            )
        return result

    sphinx.domains.python._parse_arglist = parse_arglist


def _monkey_patch_python_get_signature_prefix(
    directive_cls: Type[sphinx.domains.python.PyObject],
) -> None:
    orig_get_signature_prefix = directive_cls.get_signature_prefix

    def get_signature_prefix(self, sig: str) -> str:
        prefix = orig_get_signature_prefix(self, sig)
        if sphinx.version_info >= (4, 3):
            return prefix
        parts = prefix.strip().split(" ")
        if "property" in parts:
            parts.remove("property")
        if parts:
            return " ".join(parts) + " "
        return ""

    directive_cls.get_signature_prefix = get_signature_prefix


def _monkey_patch_pyattribute_handle_signature(
    directive_cls: Type[sphinx.domains.python.PyObject],
):
    """Modifies PyAttribute or PyVariable to improve styling of signature."""

    def handle_signature(
        self, sig: str, signode: sphinx.addnodes.desc_signature
    ) -> Tuple[str, str]:
        result = super(directive_cls, self).handle_signature(sig, signode)
        typ = self.options.get("type")
        if typ:
            signode += sphinx.addnodes.desc_sig_punctuation("", " : ")
            signode += sphinx.domains.python._parse_annotation(typ, self.env)

        value = self.options.get("value")
        if value:
            signode += sphinx.addnodes.desc_sig_punctuation("", " = ")
            signode += docutils.nodes.literal(
                text=value, classes=["code", "python"], language="python"
            )
        return result

    directive_cls.handle_signature = handle_signature


def _monkey_patch_parameterlist_to_support_subscript():
    desc_parameterlist = sphinx.addnodes.desc_parameterlist

    def astext(self: desc_parameterlist) -> str:
        open_paren, close_paren = self.get("parens", ("(", ")"))
        return f"{open_paren}{super(desc_parameterlist, self).astext()}{close_paren}"

    desc_parameterlist.astext = astext


def _monkey_patch_napoleon_admonition_classes():
    GoogleDocstring = sphinx.ext.napoleon.docstring.GoogleDocstring

    def _add_admonition_class(method_name: str, class_name: str) -> None:
        orig_method = getattr(GoogleDocstring, method_name)

        def wrapper(self: GoogleDocstring, section: str) -> List[str]:
            result = orig_method(self, section)
            result.insert(1, f"   :class: {class_name}")
            return result

        setattr(GoogleDocstring, method_name, wrapper)

    _add_admonition_class("_parse_examples_section", "example")


class PyParamXRefRole(sphinx.domains.python.PyXRefRole):
    def process_link(
        self,
        env: sphinx.environment.BuildEnvironment,
        refnode: docutils.nodes.Element,
        has_explicit_title: bool,
        title: str,
        target: str,
    ) -> Tuple[str, str]:
        refnode["py:func"] = env.ref_context.get("py:func")
        return super().process_link(env, refnode, has_explicit_title, title, target)


def _monkey_patch_python_domain_to_resolve_params():
    """Adds support to the Python domain for resolving parameter references."""

    PythonDomain = sphinx.domains.python.PythonDomain  # pylint: disable=invalid-name
    orig_resolve_xref = PythonDomain.resolve_xref

    def resolve_xref(
        self: PythonDomain,
        env: sphinx.environment.BuildEnvironment,
        fromdocname: str,
        builder: sphinx.builders.Builder,
        typ: str,
        target: str,
        node: sphinx.addnodes.pending_xref,
        contnode: docutils.nodes.Element,
    ) -> Optional[docutils.nodes.Element]:
        if typ == "param":
            func_name = node.get("py:func")
            if func_name and "." not in target:
                return orig_resolve_xref(
                    self,
                    env,
                    fromdocname,
                    builder,
                    typ,
                    "%s.%s" % (func_name, target),
                    node,
                    contnode,
                )

        return orig_resolve_xref(
            self, env, fromdocname, builder, typ, target, node, contnode
        )

    PythonDomain.resolve_xref = resolve_xref

    orig_resolve_any_xref = PythonDomain.resolve_any_xref

    def resolve_any_xref(
        self: PythonDomain,
        env: sphinx.environment.BuildEnvironment,
        fromdocname: str,
        builder: sphinx.builders.Builder,
        target: str,
        node: sphinx.addnodes.pending_xref,
        contnode: docutils.nodes.Element,
    ) -> List[Tuple[str, docutils.nodes.Element]]:
        results = orig_resolve_any_xref(
            self, env, fromdocname, builder, target, node, contnode
        )
        # Don't resolve parameters as any refs, as they introduce too many
        # ambiguities.
        return [r for r in results if r[0] != "py:param"]

    PythonDomain.resolve_any_xref = resolve_any_xref


def _monkey_patch_python_domain_to_add_object_synopses_to_references():
    PythonDomain = sphinx.domains.python.PythonDomain  # pylint: disable=invalid-name

    def _add_synopsis(
        self: PythonDomain,
        env: sphinx.environment.BuildEnvironment,
        refnode: docutils.nodes.Element,
    ) -> None:
        name = refnode.get("reftitle")
        obj = self.objects.get(name)
        if obj is None:
            return
        refnode["reftitle"] = apidoc_formatting.format_object_description_tooltip(
            env,
            apidoc_formatting.get_object_description_options(
                env, self.name, obj.objtype
            ),
            base_title=name,
            synopsis=self.data["synopses"].get(name),
        )

    orig_resolve_xref = PythonDomain.resolve_xref

    def resolve_xref(
        self: PythonDomain,
        env: sphinx.environment.BuildEnvironment,
        fromdocname: str,
        builder: sphinx.builders.Builder,
        typ: str,
        target: str,
        node: sphinx.addnodes.pending_xref,
        contnode: docutils.nodes.Element,
    ) -> Optional[docutils.nodes.Element]:
        refnode = orig_resolve_xref(
            self, env, fromdocname, builder, typ, target, node, contnode
        )
        if refnode is not None:
            _add_synopsis(self, env, refnode)
        return refnode

    PythonDomain.resolve_xref = resolve_xref

    orig_resolve_any_xref = PythonDomain.resolve_any_xref

    def resolve_any_xref(
        self: PythonDomain,
        env: sphinx.environment.BuildEnvironment,
        fromdocname: str,
        builder: sphinx.builders.Builder,
        target: str,
        node: sphinx.addnodes.pending_xref,
        contnode: docutils.nodes.Element,
    ) -> List[Tuple[str, docutils.nodes.Element]]:
        results = orig_resolve_any_xref(
            self, env, fromdocname, builder, target, node, contnode
        )
        for _, refnode in results:
            _add_synopsis(self, env, refnode)
        return results

    PythonDomain.resolve_any_xref = resolve_any_xref


OBJECT_PRIORITY_DEFAULT = 1
OBJECT_PRIORITY_IMPORTANT = 0
OBJECT_PRIORITY_UNIMPORTANT = 2
OBJECT_PRIORITY_EXCLUDE_FROM_SEARCH = -1


def _monkey_patch_python_domain_to_deprioritize_params_in_search():
    """Ensures parameters have OBJECT_PRIORITY_UNIMPORTANT."""
    PythonDomain = sphinx.domains.python.PythonDomain  # pylint: disable=invalid-name
    orig_get_objects = PythonDomain.get_objects

    def get_objects(
        self: PythonDomain,
    ) -> Iterator[Tuple[str, str, str, str, str, int]]:
        for obj in orig_get_objects(self):
            if obj[2] != "parameter":
                yield obj
            else:
                yield (
                    obj[0],
                    obj[1],
                    obj[2],
                    obj[3],
                    obj[4],
                    OBJECT_PRIORITY_UNIMPORTANT,
                )

    PythonDomain.get_objects = get_objects


def _add_parameter_links_to_signature(
    env: sphinx.environment.BuildEnvironment,
    signode: sphinx.addnodes.desc_signature,
    symbol: str,
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

    for desc_param_node in signode.traverse(condition=sphinx.addnodes.desc_parameter):
        for sig_param_node in desc_param_node:
            if not isinstance(sig_param_node, sphinx.addnodes.desc_sig_name):
                continue
            new_sig_param_node = add_replacement(sig_param_node, desc_param_node)
            new_sig_param_node["classes"].append("sig-name")
            break

    for name_node, param_node in replacements:
        name = name_node.astext()
        refnode = sphinx.addnodes.pending_xref(
            "",
            name_node.deepcopy(),
            refdomain="py",
            reftype="parameter",
            reftarget=f"{symbol}.{name}",
            refwarn=False,
        )
        name_node.replace_self(refnode)

    return sig_param_nodes


def _add_parameter_documentation_ids(
    directive: sphinx.domains.python.PyObject,
    env: sphinx.environment.BuildEnvironment,
    obj_content: sphinx.addnodes.desc_content,
    sig_param_nodes_for_signature: List[Dict[str, docutils.nodes.Element]],
    symbols: List[str],
    noindex: bool,
) -> None:

    qualify_parameter_ids = env.config.python_qualify_parameter_ids

    param_options = apidoc_formatting.get_object_description_options(
        env, "py", "parameter"
    )

    py = cast(sphinx.domains.python.PythonDomain, env.get_domain("py"))

    def cross_link_single_parameter(
        param_name: str, param_node: docutils.nodes.term
    ) -> None:
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

        if not noindex:
            generate_synopses = param_options["generate_synopses"]
            if generate_synopses is not None:
                synopsis = sphinx_utils.summarize_element_text(
                    param_node.parent[-1], generate_synopses
                )
            else:
                synopsis = None

            unqualified_param_id = f"p-{param_name}"

            param_symbols = set()

            # Set ids of the parameter node.
            for symbol_i, _ in unique_decls.values():
                symbol = symbols[symbol_i]
                param_symbol = f"{symbol}.{param_name}"
                if param_symbol in param_symbols:
                    continue
                param_symbols.add(param_symbol)

                if synopsis:
                    py.data["synopses"][param_symbol] = synopsis

                if qualify_parameter_ids:
                    node_id = sphinx.util.nodes.make_id(
                        env, directive.state.document, "", param_symbol
                    )
                    param_node["ids"].append(node_id)
                else:
                    node_id = unqualified_param_id

                py.note_object(param_symbol, "parameter", node_id, location=param_node)

            if param_options["include_in_toc"]:
                toc_title = param_name
                param_node["toc_title"] = toc_title

            if not qualify_parameter_ids:
                param_node["ids"].append(unqualified_param_id)

        # If a parameter type was specified explicitly, don't replace it from
        # the signature.
        if not param_node.get("paramtype"):
            # Replace the bare parameter name with the unique parameter
            # declarations.
            del param_node[:]
            new_param_nodes = []

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


def _cross_link_parameters(
    directive: sphinx.domains.python.PyObject,
    app: sphinx.application.Sphinx,
    signodes: List[sphinx.addnodes.desc_signature],
    content: docutils.nodes.Element,
    symbols: List[str],
    noindex: bool,
) -> None:
    # Collect the docutils nodes corresponding to the declarations of the
    # parameters in each signature, and turn the parameter names into
    # cross-links to the parameter description.
    #
    # In the parameter descriptions, these declarations will be copied in to
    # replace the bare parameter name so that the parameter description shows
    # e.g. `x : int = 10` rather than just `x`.
    sig_param_nodes_for_signature = []
    for signode, symbol in zip(signodes, symbols):
        sig_param_nodes_for_signature.append(
            _add_parameter_links_to_signature(app.env, signode, symbol)
        )

    # Find all parameter descriptions in the object description body, and mark
    # them as the target for cross links to that parameter.  Also substitute in
    # the parameter declaration for the bare parameter name, as described above.
    _add_parameter_documentation_ids(
        directive=directive,
        env=app.env,
        obj_content=content,
        sig_param_nodes_for_signature=sig_param_nodes_for_signature,
        symbols=symbols,
        noindex=noindex,
    )


def _monkey_patch_python_domain_to_support_synopses():

    PythonDomain = sphinx.domains.python.PythonDomain

    object_class = sphinx.domains.python.PyObject

    orig_after_content = object_class.after_content

    orig_transform_content = object_class.transform_content

    def transform_content(self: object_class, contentnode) -> None:
        self.contentnode = contentnode
        orig_transform_content(self, contentnode)

    object_class.transform_content = transform_content

    def after_content(self: object_class) -> None:
        orig_after_content(self)
        obj_desc = self.contentnode.parent
        signodes = obj_desc.children[:-1]

        symbols = []
        for signode in signodes:
            modname = signode["module"]
            fullname = signode["fullname"]
            symbols.append((modname + "." if modname else "") + fullname)
        noindex = "noindex" in self.options
        if not symbols:
            return
        if self.objtype in ("class", "exception"):
            # Any parameters are actually constructor parameters.  To avoid
            # symbol name conflicts, assign object names under `__init__`.
            function_symbols = [f"{symbol}.__init__" for symbol in symbols]
        else:
            function_symbols = symbols

        _cross_link_parameters(
            directive=self,
            app=self.env.app,
            signodes=signodes,
            content=self.contentnode,
            symbols=function_symbols,
            noindex=noindex,
        )
        if noindex:
            return
        options = apidoc_formatting.get_object_description_options(
            self.env, self.domain, self.objtype
        )
        generate_synopses = options["generate_synopses"]
        if generate_synopses is None:
            return
        synopsis = sphinx_utils.summarize_element_text(
            self.contentnode, generate_synopses
        )
        if not synopsis:
            return
        py = cast(PythonDomain, self.env.get_domain("py"))
        for symbol in symbols:
            py.data["synopses"][symbol] = synopsis

    object_class.after_content = after_content

    orig_merge_domaindata = PythonDomain.merge_domaindata

    def merge_domaindata(self, docnames: List[str], otherdata: dict) -> None:
        orig_merge_domaindata(self, docnames, otherdata)
        self.data["synopses"].update(otherdata["synopses"])

    PythonDomain.merge_domaindata = merge_domaindata

    def get_object_synopses(
        self: PythonDomain,
    ) -> Iterator[Tuple[Tuple[str, str], str]]:
        synopses = self.data["synopses"]
        for refname, synopsis in synopses.items():
            obj = self.objects.get(refname)
            if not obj:
                continue
            yield ((obj.docname, obj.node_id), synopsis)

    PythonDomain.get_object_synopses = get_object_synopses


sphinx.domains.python.PythonDomain.object_types["parameter"] = sphinx.domains.ObjType(
    "parameter", "param"
)


def setup(app: sphinx.application.Sphinx):
    _monkey_patch_python_doc_fields()
    _monkey_patch_python_parse_annotation()
    _monkey_patch_python_parse_arglist()
    _monkey_patch_python_get_signature_prefix(sphinx.domains.python.PyFunction)
    _monkey_patch_python_get_signature_prefix(sphinx.domains.python.PyMethod)
    _monkey_patch_python_get_signature_prefix(sphinx.domains.python.PyProperty)
    _monkey_patch_pyattribute_handle_signature(sphinx.domains.python.PyAttribute)
    _monkey_patch_pyattribute_handle_signature(sphinx.domains.python.PyVariable)
    _monkey_patch_parameterlist_to_support_subscript()
    _monkey_patch_napoleon_admonition_classes()
    _monkey_patch_python_domain_to_resolve_params()
    _monkey_patch_python_domain_to_deprioritize_params_in_search()
    _monkey_patch_python_domain_to_add_object_synopses_to_references()
    _monkey_patch_python_domain_to_support_synopses()

    sphinx.domains.python.PythonDomain.initial_data["synopses"] = {}  # name -> synopsis

    app.add_role_to_domain("py", "param", PyParamXRefRole())
    app.add_config_value(
        "python_qualify_parameter_ids", default=True, rebuild="env", types=(bool,)
    )

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
