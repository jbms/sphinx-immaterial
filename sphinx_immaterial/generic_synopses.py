"""Adds synopsis support to the std domain."""

from typing import cast, Optional, List, Iterator, Tuple

import docutils.nodes
import sphinx.application

from . import apidoc_formatting
from . import sphinx_utils


def _monkey_patch_generic_object_to_support_synopses():

    StandardDomain = sphinx.domains.std.StandardDomain

    object_class = sphinx.domains.std.GenericObject

    orig_after_content = object_class.after_content

    orig_transform_content = object_class.transform_content

    def transform_content(self: object_class, contentnode) -> None:
        self.contentnode = contentnode
        orig_transform_content(self, contentnode)

    object_class.transform_content = transform_content

    def after_content(self: object_class) -> None:
        orig_after_content(self)
        noindex = "noindex" in self.options
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
        std = cast(StandardDomain, self.env.get_domain("std"))
        for name in self.names:
            std.data["synopses"][self.objtype, name] = synopsis

    object_class.after_content = after_content

    orig_merge_domaindata = StandardDomain.merge_domaindata

    def merge_domaindata(self, docnames: List[str], otherdata: dict) -> None:
        orig_merge_domaindata(self, docnames, otherdata)
        self.data["synopses"].update(otherdata["synopses"])

    StandardDomain.merge_domaindata = merge_domaindata

    def make_refnode(
        std: StandardDomain,
        builder: sphinx.builders.Builder,
        fromdocname: str,
        docname: str,
        labelid: str,
        contnode: docutils.nodes.Element,
        objtype: str,
        target: str,
    ):
        return sphinx.util.nodes.make_refnode(
            builder,
            fromdocname,
            docname,
            labelid,
            contnode,
            title=apidoc_formatting.format_object_description_tooltip(
                env=builder.env,
                options=apidoc_formatting.get_object_description_options(
                    std.env, "std", objtype
                ),
                base_title=target,
                synopsis=std.data["synopses"].get((objtype, target)),
            ),
        )

    def _resolve_obj_xref(
        self: StandardDomain,
        env: sphinx.environment.BuildEnvironment,
        fromdocname: str,
        builder: sphinx.builders.Builder,
        typ: str,
        target: str,
        node: sphinx.addnodes.pending_xref,
        contnode: docutils.nodes.Element,
    ) -> Optional[docutils.nodes.Element]:
        objtypes = self.objtypes_for_role(typ) or []
        objtype = None
        for objtype in objtypes:
            result = self.objects.get((objtype, target))
            if result is not None:
                docname, labelid = result
                break
        else:
            return None

        return make_refnode(
            self, builder, fromdocname, docname, labelid, contnode, objtype, target
        )

    StandardDomain._resolve_obj_xref = _resolve_obj_xref

    def resolve_any_xref(
        self: StandardDomain,
        env: sphinx.environment.BuildEnvironment,
        fromdocname: str,
        builder: sphinx.builders.Builder,
        target: str,
        node: sphinx.addnodes.pending_xref,
        contnode: docutils.nodes.Element,
    ) -> List[Tuple[str, docutils.nodes.Element]]:
        results: List[Tuple[str, docutils.nodes.Element]] = []
        ltarget = target.lower()  # :ref: lowercases its target automatically
        for role in ("ref", "option"):  # do not try "keyword"
            res = self.resolve_xref(
                env,
                fromdocname,
                builder,
                role,
                ltarget if role == "ref" else target,
                node,
                contnode,
            )
            if res:
                results.append(("std:" + role, res))
        # all others
        for objtype in self.object_types:
            key = (objtype, target)
            if objtype == "term":
                key = (objtype, ltarget)
            if key in self.objects:
                docname, labelid = self.objects[key]
                results.append(
                    (
                        "std:" + self.role_for_objtype(objtype),
                        make_refnode(
                            self,
                            builder,
                            fromdocname,
                            docname,
                            labelid,
                            contnode,
                            objtype,
                            target,
                        ),
                    )
                )
        return results

    StandardDomain.resolve_any_xref = resolve_any_xref

    def get_object_synopses(
        self: StandardDomain,
    ) -> Iterator[Tuple[Tuple[str, str], str]]:
        synopses = self.data["synopses"]
        for (objtype, name), (docname, labelid) in self.objects.items():
            synopsis = synopses.get((objtype, name))
            if not synopsis:
                continue
            yield ((docname, labelid), synopsis)

    StandardDomain.get_object_synopses = get_object_synopses


def setup(app: sphinx.application.Sphinx):
    sphinx.domains.std.StandardDomain.initial_data[
        "synopses"
    ] = {}  # (type, name) -> synopsis
    _monkey_patch_generic_object_to_support_synopses()

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
