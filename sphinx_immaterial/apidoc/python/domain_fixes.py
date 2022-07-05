"""Fixes for the Python domain."""

import json
import re
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
    Union,
)

import docutils.nodes
import docutils.parsers.rst.states
import sphinx
import sphinx.addnodes
import sphinx.application
import sphinx.builders
import sphinx.domains
import sphinx.domains.python
import sphinx.environment
import sphinx.errors
import sphinx.ext.napoleon
import sphinx.util.logging
import sphinx.util.nodes

from .. import apidoc_formatting
from ... import sphinx_utils
from . import autodoc_property_type

PythonDomain = sphinx.domains.python.PythonDomain
PyTypedField = sphinx.domains.python.PyTypedField
PyObject = sphinx.domains.python.PyObject


logger = sphinx.util.logging.getLogger(__name__)


def _ensure_wrapped_in_desc_type(
    nodes: List[docutils.nodes.Node],
) -> List[docutils.nodes.Node]:
    if len(nodes) != 1 or not isinstance(nodes[0], sphinx.addnodes.desc_type):
        nodes = [sphinx.addnodes.desc_type("", "", *nodes)]
    return nodes


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
                        _ensure_wrapped_in_desc_type(
                            self.make_xrefs(
                                cast(str, self.typerolename),
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
        fieldname = docutils.nodes.field_name("", cast(str, self.label))
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

    def get_signature_prefix(self, sig: str) -> Union[str, List[docutils.nodes.Node]]:
        prefix = orig_get_signature_prefix(self, sig)
        if not self.env.config.python_strip_property_prefix:
            return prefix
        if sphinx.version_info >= (4, 3):
            prefix = cast(List[docutils.nodes.Node], prefix)
            assert isinstance(prefix, list)
            for prop_idx, node in enumerate(prefix):
                if node == "property":
                    assert isinstance(
                        prefix[prop_idx + 1], sphinx.addnodes.desc_sig_space
                    )
                    prefix = list(prefix)
                    del prefix[prop_idx : prop_idx + 2]
                    break
            return prefix
        prefix = cast(str, prefix)  # type: ignore
        assert isinstance(prefix, str)
        parts = prefix.strip().split(" ")
        if "property" in parts:
            parts.remove("property")
        if parts:
            return " ".join(parts) + " "
        return ""

    directive_cls.get_signature_prefix = get_signature_prefix  # type: ignore


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

    directive_cls.handle_signature = handle_signature  # type: ignore


desc_parameterlist = sphinx.addnodes.desc_parameterlist


def _monkey_patch_parameterlist_to_support_subscript():
    def astext(self: desc_parameterlist) -> str:
        open_paren, close_paren = self.get("parens", ("(", ")"))
        return f"{open_paren}{super(desc_parameterlist, self).astext()}{close_paren}"

    desc_parameterlist.astext = astext  # type: ignore


GoogleDocstring = sphinx.ext.napoleon.docstring.GoogleDocstring


def _monkey_patch_napoleon_admonition_classes():
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

    PyObject.before_content = before_content

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

    PyObject.after_content = after_content


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
            desc_param_node = cast(docutils.nodes.Element, desc_param_node)
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


def _monkey_patch_python_domain_to_support_synopses():

    orig_after_content = PyObject.after_content

    orig_transform_content = PyObject.transform_content

    def transform_content(self: PyObject, contentnode) -> None:
        setattr(self, "contentnode", contentnode)
        orig_transform_content(self, contentnode)

    PyObject.transform_content = transform_content

    def after_content(self: PyObject) -> None:
        orig_after_content(self)
        obj_desc = cast(
            sphinx.addnodes.desc_content, getattr(self, "contentnode")
        ).parent
        signodes = obj_desc.children[:-1]

        py = cast(PythonDomain, self.env.get_domain("py"))

        def strip_object_entry_node_id(existing_node_id: str, object_id: str):
            obj = py.objects.get(object_id)
            if (
                obj is None
                or obj.node_id != existing_node_id
                or obj.docname != self.env.docname
            ):
                return
            py.objects[object_id] = obj._replace(node_id="")

        nonodeid = "nonodeid" in self.options
        canonical_name = self.options.get("canonical")
        noindexentry = "noindexentry" in self.options
        noindex = "noindex" in self.options

        symbols = []
        for signode in cast(List[docutils.nodes.Element], signodes):
            modname = signode["module"]
            fullname = signode["fullname"]
            symbol = (modname + "." if modname else "") + fullname
            symbols.append(symbol)
            if nonodeid and signode["ids"]:
                orig_node_id = signode["ids"][0]
                signode["ids"] = []
                strip_object_entry_node_id(orig_node_id, symbol)
                if canonical_name:
                    strip_object_entry_node_id(orig_node_id, canonical_name)

                if noindexentry:
                    entries = self.indexnode["entries"]
                    new_entries = []
                    for entry in entries:
                        new_entry = list(entry)
                        if new_entry[2] == orig_node_id:
                            new_entry[2] = ""
                        new_entries.append(tuple(new_entry))
                    self.indexnode["entries"] = new_entries

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
        if noindex:
            return
        options = apidoc_formatting.get_object_description_options(
            self.env, self.domain, self.objtype
        )
        generate_synopses = options["generate_synopses"]
        if generate_synopses is None:
            return
        synopsis = sphinx_utils.summarize_element_text(
            getattr(self, "contentnode"), generate_synopses
        )
        if not synopsis:
            return
        for symbol in symbols:
            py.data["synopses"][symbol] = synopsis

    PyObject.after_content = after_content

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


def _maybe_strip_type_annotations(
    app: sphinx.application.Sphinx,
    domain: str,
    objtype: str,
    contentnode: sphinx.addnodes.desc_content,
) -> None:
    if domain != "py":
        return
    obj_desc = contentnode.parent
    assert isinstance(obj_desc, sphinx.addnodes.desc)
    strip_self_type_annotations = app.config.python_strip_self_type_annotations
    strip_return_type_annotations = app.config.python_strip_return_type_annotations
    for signode in obj_desc[:-1]:
        assert isinstance(signode, sphinx.addnodes.desc_signature)
        if strip_self_type_annotations:
            for param in signode.traverse(condition=sphinx.addnodes.desc_parameter):
                if param.children[0].astext() == "self":
                    # Remove any annotations on `self`
                    del param.children[1:]
                break
        if strip_return_type_annotations is not None:
            fullname = signode.get("fullname")
            if fullname is None:
                # Python domain failed to parse the signature.  Just ignore it.
                continue
            modname = signode["module"]
            if modname:
                fullname = modname + "." + fullname
            if strip_return_type_annotations.fullmatch(fullname):
                # Remove return type.
                for node in signode.traverse(condition=sphinx.addnodes.desc_returns):
                    node.parent.remove(node)


def _monkey_patch_python_domain_to_support_object_ids():
    for object_class in sphinx.domains.python.PythonDomain.directives.values():
        object_class.option_spec["object-ids"] = json.loads
        object_class.option_spec["nonodeid"] = docutils.parsers.rst.directives.flag

    passthrough_options = ("object-ids", "nonodeid")

    orig_add_directive_header = sphinx.ext.autodoc.Documenter.add_directive_header

    def add_directive_header(self: sphinx.ext.autodoc.Documenter, sig: str) -> None:
        orig_add_directive_header(self, sig)
        for option_name in passthrough_options:
            if option_name not in self.options:
                continue
            value = self.options[option_name]
            self.add_line(f"   :{option_name}: {value}", self.get_sourcename())

    sphinx.ext.autodoc.Documenter.add_directive_header = add_directive_header

    orig_handle_signature = sphinx.domains.python.PyObject.handle_signature

    def handle_signature(
        self: sphinx.domains.python.PyObject,
        sig: str,
        signode: sphinx.addnodes.desc_signature,
    ) -> Tuple[str, str]:
        fullname, prefix = orig_handle_signature(self, sig, signode)
        object_ids = self.options.get("object-ids")
        if object_ids is not None:
            signature_index = getattr(self, "_signature_index", 0)
            setattr(self, "_signature_index", signature_index + 1)
            modname = signode["module"]
            if modname:
                modname += "."
            else:
                modname = ""
            if signature_index >= len(object_ids):
                logger.warning(
                    "Not enough object-ids %r specified for %r",
                    object_ids,
                    modname + signode["fullname"],
                    location=self.get_source_info(),
                )
            else:
                object_id = object_ids[signature_index]
                if object_id.startswith(modname):
                    fullname = object_id[len(modname) :]
                    signode["fullname"] = fullname
                else:
                    logger.warning(
                        "object-id %r for %r does not start with module name %r",
                        object_id,
                        signode["fullname"],
                        modname,
                        location=self.get_source_info(),
                    )
        return fullname, prefix

    sphinx.domains.python.PyObject.handle_signature = handle_signature


def _monkey_patch_python_domain_to_support_titles():
    """Enables support for titles in all Python directive types.

    Normally sphinx only supports titles in `automodule`, but the python_apigen
    extension uses titles to group member summaries.
    """

    orig_before_content = PyObject.before_content

    def before_content(self: sphinx.domains.python.PyObject) -> None:
        orig_before_content(self)
        setattr(self, "_saved_content", self.content)
        self.content = docutils.statemachine.StringList()

    orig_transform_content = sphinx.domains.python.PyObject.transform_content

    def transform_content(self: PyObject, contentnode: docutils.nodes.Node) -> None:
        sphinx.util.nodes.nested_parse_with_titles(
            self.state,
            getattr(self, "_saved_content"),
            contentnode,
        )
        orig_transform_content(self, contentnode)

    sphinx.domains.python.PyObject.before_content = before_content
    sphinx.domains.python.PyObject.transform_content = transform_content


def _config_inited(
    app: sphinx.application.Sphinx, config: sphinx.config.Config
) -> None:

    if (
        config.python_strip_self_type_annotations
        or config.python_strip_return_type_annotations
    ):
        if isinstance(config.python_strip_return_type_annotations, str):
            setattr(
                config,
                "python_strip_return_type_annotations",
                re.compile(config.python_strip_return_type_annotations),
            )
        app.connect("object-description-transform", _maybe_strip_type_annotations)


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
    _monkey_patch_python_domain_to_store_func_in_ref_context()
    _monkey_patch_python_domain_to_resolve_params()
    _monkey_patch_python_domain_to_deprioritize_params_in_search()
    _monkey_patch_python_domain_to_add_object_synopses_to_references()
    _monkey_patch_python_domain_to_support_synopses()
    _monkey_patch_python_domain_to_support_object_ids()
    _monkey_patch_python_domain_to_support_titles()
    autodoc_property_type.apply_property_documenter_type_annotation_fix()

    sphinx.domains.python.PythonDomain.initial_data["synopses"] = {}  # name -> synopsis

    app.add_role_to_domain("py", "param", PyParamXRefRole())
    app.add_config_value(
        "python_strip_self_type_annotations", default=True, rebuild="env", types=(bool,)
    )
    app.add_config_value(
        "python_strip_return_type_annotations",
        default=r".*.(__setitem__|__init__)",
        rebuild="env",
        types=(re.Pattern, type(None)),
    )
    app.add_config_value(
        "python_strip_property_prefix", default=False, rebuild="env", types=(bool,)
    )
    app.connect("config-inited", _config_inited)

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
