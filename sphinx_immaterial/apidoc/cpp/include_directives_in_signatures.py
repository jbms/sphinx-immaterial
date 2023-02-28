"""Adds support for #include directives in C/C++ signatures."""

from typing import Type, List

import docutils.nodes
import sphinx.directives
import sphinx.domains.c
import sphinx.domains.cpp


def _monkey_patch_domain_to_support_include_directives(
    object_class: Type[sphinx.directives.ObjectDescription], language: str
):
    orig_get_signatures = object_class.get_signatures

    def is_include(sig: str) -> bool:
        return sig.startswith("#")

    def get_signatures(self: sphinx.directives.ObjectDescription) -> List[str]:
        return [sig for sig in orig_get_signatures(self) if not is_include(sig)]

    object_class.get_signatures = get_signatures  # type: ignore

    orig_run = object_class.run

    def run(self: sphinx.directives.ObjectDescription) -> List[docutils.nodes.Node]:
        nodes = orig_run(self)
        include_directives = [
            sig for sig in orig_get_signatures(self) if is_include(sig)
        ]
        if include_directives:
            obj_desc = nodes[-1]
            assert isinstance(obj_desc, sphinx.addnodes.desc)
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

    object_class.run = run  # type: ignore


_monkey_patch_domain_to_support_include_directives(
    object_class=sphinx.domains.cpp.CPPObject, language="cpp"
)
_monkey_patch_domain_to_support_include_directives(
    object_class=sphinx.domains.c.CObject, language="c"
)
