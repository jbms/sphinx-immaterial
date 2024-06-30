from typing import Optional, cast, List, Dict, Sequence, Tuple, Any, Iterator

import docutils.nodes
from sphinx.domains.python import PyTypedField
from sphinx.domains.python import PythonDomain
from sphinx.domains.python import PyObject
import sphinx.util.logging

from . import annotation_style
from .. import object_description_options
from ... import sphinx_utils


logger = sphinx.util.logging.getLogger(__name__)


def _monkey_patch_python_doc_fields():
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
                        annotation_style.ensure_wrapped_in_desc_type(
                            self.make_xrefs(
                                cast(str, self.typerolename),
                                domain,
                                typename,
                                docutils.nodes.Text,
                                env=cast(sphinx.environment.BuildEnvironment, env),
                                inliner=cast(
                                    docutils.parsers.rst.states.Inliner, inliner
                                ),
                                location=cast(docutils.nodes.Node, location),
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
        fieldname = docutils.nodes.field_name("", cast(str, self.label))
        fieldbody = docutils.nodes.field_body("", bodynode)
        return docutils.nodes.field("", fieldname, fieldbody)

    PyTypedField.make_field = make_field  # type: ignore[assignment]


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


def _monkey_patch_python_domain_to_store_func_in_ref_context():
    orig_before_content = PyObject.before_content

    def before_content(self: PyObject) -> None:
        orig_before_content(self)

        if not isinstance(
            self, (sphinx.domains.python.PyFunction, sphinx.domains.python.PyMethod)
        ):
            return
        setattr(
            self, "_prev_ref_context_py_func", self.env.ref_context.get("py:func", None)
        )
        if self.names:
            fullname = self.names[-1][0]
        else:
            fullname = None

        if fullname:
            classname = self.env.ref_context.get("py:class")
            if classname and fullname.startswith(classname + "."):
                fullname = fullname[len(classname) + 1 :]
            self.env.ref_context["py:func"] = fullname
        else:
            self.env.ref_context.pop("py:func", None)

    PyObject.before_content = before_content  # type: ignore[assignment]

    orig_after_content = PyObject.after_content

    def after_content(self: PyObject) -> None:
        orig_after_content(self)
        if not isinstance(
            self, (sphinx.domains.python.PyFunction, sphinx.domains.python.PyMethod)
        ):
            return

        prev_py_func = getattr(self, "_prev_ref_context_py_func", None)
        if prev_py_func is None:
            self.env.ref_context.pop("py:func", None)
        else:
            self.env.ref_context["py:func"] = prev_py_func

    PyObject.after_content = after_content  # type: ignore[assignment]


def _monkey_patch_python_domain_to_resolve_params():
    """Adds support to the Python domain for resolving parameter references."""

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
                target = "%s.%s" % (func_name, target)
        result = orig_resolve_xref(
            self, env, fromdocname, builder, typ, target, node, contnode
        )
        if (
            typ == "param"
            and result is None
            and node.get("implicit_sig_param_ref", False)
        ):
            # Suppress missing reference warnings for automatically-added
            # references to parameter descriptions.
            raise sphinx.errors.NoUri
        return result

    PythonDomain.resolve_xref = resolve_xref  # type: ignore[assignment]

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

    PythonDomain.resolve_any_xref = resolve_any_xref  # type: ignore[assignment]


OBJECT_PRIORITY_DEFAULT = 1
OBJECT_PRIORITY_IMPORTANT = 0
OBJECT_PRIORITY_UNIMPORTANT = 2
OBJECT_PRIORITY_EXCLUDE_FROM_SEARCH = -1


def _monkey_patch_python_domain_to_deprioritize_params_in_search():
    """Ensures parameters have OBJECT_PRIORITY_UNIMPORTANT."""
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

    PythonDomain.get_objects = get_objects  # type: ignore[assignment]


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
        for name_node_copy in param_node_copy.findall(condition=type(name_node)):
            if name_node_copy.get(node_identifier_key):
                return name_node_copy
        raise ValueError("Could not locate name node within parameter")

    for desc_param_node in signode.findall(condition=sphinx.addnodes.desc_parameter):
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
            reftype="param",
            reftarget=f"{symbol}.{name}",
            refwarn=False,
        )
        refnode["implicit_sig_param_ref"] = True
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
    qualify_parameter_ids = "nonodeid" not in directive.options

    param_options = object_description_options.get_object_description_options(
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
        unique_symbols: Dict[Tuple[str, str], int] = {}
        for i, sig_param_nodes in enumerate(sig_param_nodes_for_signature):
            desc_param_node = sig_param_nodes.get(param_name)
            if desc_param_node is None:
                continue
            desc_param_node = cast(docutils.nodes.Element, desc_param_node)
            decl_text = desc_param_node.astext().strip()
            unique_decls.setdefault(decl_text, (i, desc_param_node))
            unique_symbols.setdefault((decl_text, symbols[i]), i)
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
            synopsis: Optional[str]
            generate_synopses = param_options["generate_synopses"]
            if generate_synopses is not None:
                synopsis = sphinx_utils.summarize_element_text(
                    cast(docutils.nodes.definition, param_node.parent[-1]),
                    generate_synopses,
                )
            else:
                synopsis = None

            unqualified_param_id = f"p-{param_name}"

            param_symbols = set()

            # Set ids of the parameter node.
            for symbol_i in unique_symbols.values():
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


def _cross_link_parameters(
    directive: sphinx.domains.python.PyObject,
    app: sphinx.application.Sphinx,
    signodes: List[sphinx.addnodes.desc_signature],
    content: sphinx.addnodes.desc_content,
    symbols: List[str],
    noindex: bool,
) -> None:
    env = app.env
    assert isinstance(env, sphinx.environment.BuildEnvironment)

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
            _add_parameter_links_to_signature(env, signode, symbol)
        )

    # Find all parameter descriptions in the object description body, and mark
    # them as the target for cross links to that parameter.  Also substitute in
    # the parameter declaration for the bare parameter name, as described above.
    _add_parameter_documentation_ids(
        directive=directive,
        env=env,
        obj_content=content,
        sig_param_nodes_for_signature=sig_param_nodes_for_signature,
        symbols=symbols,
        noindex=noindex,
    )


def _monkey_patch_python_domain_to_cross_link_parameters():
    orig_after_content = PyObject.after_content

    def after_content(self: PyObject) -> None:
        orig_after_content(self)
        obj_desc = cast(
            sphinx.addnodes.desc_content, getattr(self, "contentnode")
        ).parent
        signodes = obj_desc.children[:-1]

        py = cast(PythonDomain, self.env.get_domain("py"))

        noindex = "noindex" in self.options

        symbols = []
        for signode in cast(List[docutils.nodes.Element], signodes):
            modname = signode["module"]
            fullname = signode["fullname"]
            symbol = (modname + "." if modname else "") + fullname
            symbols.append(symbol)

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
            signodes=cast(List[sphinx.addnodes.desc_signature], signodes),
            content=getattr(self, "contentnode"),
            symbols=function_symbols,
            noindex=noindex,
        )

    PyObject.after_content = after_content  # type: ignore[assignment]


_monkey_patch_python_domain_to_cross_link_parameters()
_monkey_patch_python_doc_fields()
_monkey_patch_python_domain_to_store_func_in_ref_context()
_monkey_patch_python_domain_to_resolve_params()
_monkey_patch_python_domain_to_deprioritize_params_in_search()

sphinx.domains.python.PythonDomain.object_types["parameter"] = sphinx.domains.ObjType(
    "parameter", "param"
)


def setup(app: sphinx.application.Sphinx):
    app.add_role_to_domain("py", "param", PyParamXRefRole())
    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
