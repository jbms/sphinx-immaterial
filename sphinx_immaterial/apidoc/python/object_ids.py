import json
from typing import Tuple, cast, List

import docutils.nodes
import sphinx.ext.autodoc
import sphinx.addnodes
import sphinx.domains.python
from sphinx.domains.python import PyObject
from sphinx.domains.python import PythonDomain
import sphinx.util.logging

logger = sphinx.util.logging.getLogger(__name__)


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

    sphinx.ext.autodoc.Documenter.add_directive_header = add_directive_header  # type: ignore[assignment]

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

    sphinx.domains.python.PyObject.handle_signature = handle_signature  # type: ignore[assignment]

    orig_after_content = PyObject.after_content

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

        for signode in cast(List[docutils.nodes.Element], signodes):
            # If the Python signature could not be parsed by Sphinx, `module`
            # and `fullname` won't be set. Such signatures should be gracefully
            # ignored.
            modname = signode.get("module", False)
            if modname is False:
                continue
            fullname = signode.get("fullname", False)
            if fullname is False:
                continue
            symbol = (modname + "." if modname else "") + fullname
            if nonodeid and signode["ids"]:
                orig_node_id = signode["ids"][0]
                signode["ids"] = []
                strip_object_entry_node_id(orig_node_id, symbol)
                if canonical_name:
                    strip_object_entry_node_id(orig_node_id, canonical_name)

                if noindexentry:
                    entries = cast(docutils.nodes.Element, self.indexnode)["entries"]
                    new_entries = []
                    for entry in entries:
                        new_entry = list(entry)
                        if new_entry[2] == orig_node_id:
                            new_entry[2] = ""
                        new_entries.append(tuple(new_entry))
                    cast(docutils.nodes.Element, self.indexnode)["entries"] = (
                        new_entries
                    )

    PyObject.after_content = after_content  # type: ignore[assignment]


_monkey_patch_python_domain_to_support_object_ids()
