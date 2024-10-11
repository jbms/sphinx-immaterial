from typing import Optional, List, Tuple, cast, Iterator
import docutils.nodes

import sphinx.addnodes
import sphinx.builders
from sphinx.domains.python import PythonDomain
from sphinx.domains.python import PyObject
import sphinx.environment

from .. import object_description_options
from ... import sphinx_utils


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
        refnode["reftitle"] = (
            object_description_options.format_object_description_tooltip(
                env,
                object_description_options.get_object_description_options(
                    env, self.name, obj.objtype
                ),
                base_title=name,
                synopsis=self.data["synopses"].get(name),
            )
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
        for _, refnode in results:
            _add_synopsis(self, env, refnode)
        return results

    PythonDomain.resolve_any_xref = resolve_any_xref  # type: ignore[assignment]


def _monkey_patch_python_domain_to_support_synopses():
    orig_after_content = PyObject.after_content

    orig_transform_content = PyObject.transform_content

    def transform_content(self: PyObject, contentnode) -> None:
        setattr(self, "contentnode", contentnode)
        orig_transform_content(self, contentnode)  # type: ignore[arg-type]

    PyObject.transform_content = transform_content  # type: ignore[assignment]

    def after_content(self: PyObject) -> None:
        orig_after_content(self)
        noindex = "noindex" in self.options
        if noindex:
            return

        obj_desc = cast(
            sphinx.addnodes.desc_content, getattr(self, "contentnode")
        ).parent
        signodes = obj_desc.children[:-1]

        py = cast(PythonDomain, self.env.get_domain("py"))

        symbols = []
        for signode in cast(List[docutils.nodes.Element], signodes):
            modname = signode.get("module", False)
            if modname is False:
                continue
            fullname = signode.get("fullname", False)
            if fullname is False:
                continue
            symbol = (modname + "." if modname else "") + fullname
            symbols.append(symbol)

        if not symbols:
            return

        options = object_description_options.get_object_description_options(
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

    PyObject.after_content = after_content  # type: ignore[assignment]

    orig_merge_domaindata = PythonDomain.merge_domaindata

    def merge_domaindata(self, docnames, otherdata: dict) -> None:
        orig_merge_domaindata(self, docnames, otherdata)
        self.data["synopses"].update(otherdata["synopses"])

    PythonDomain.merge_domaindata = merge_domaindata  # type: ignore[assignment]

    def get_object_synopses(
        self: PythonDomain,
    ) -> Iterator[Tuple[Tuple[str, str], str]]:
        synopses = self.data["synopses"]
        for refname, synopsis in synopses.items():
            obj = self.objects.get(refname)
            if not obj:
                continue
            yield ((obj.docname, obj.node_id), synopsis)

    PythonDomain.get_object_synopses = get_object_synopses  # type: ignore[attr-defined]


_monkey_patch_python_domain_to_add_object_synopses_to_references()
_monkey_patch_python_domain_to_support_synopses()

sphinx.domains.python.PythonDomain.initial_data["synopses"] = {}  # name -> synopsis
