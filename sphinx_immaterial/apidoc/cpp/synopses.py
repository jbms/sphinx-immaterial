"""Adds support for synopses to C/C++ domains."""

from typing import Union, Type, Optional, Tuple, Iterator

import docutils.nodes
import sphinx.domains.c
import sphinx.domains.cpp
from sphinx.domains.c import CDomain
from sphinx.domains.cpp import CPPDomain

from . import last_resolved_symbol
from . import parameter_objects
from . import symbol_ids
from .. import object_description_options

SYNOPSIS_ATTR = "_sphinx_immaterial_synopsis"


def set_synopsis(
    symbol: Union[sphinx.domains.cpp.Symbol, sphinx.domains.c.Symbol], synopsis: str
) -> None:
    """Sets the synopsis for a given symbol."""
    setattr(symbol.declaration, SYNOPSIS_ATTR, synopsis)


def _monkey_patch_add_object_type_and_synopsis(
    domain_class: Union[
        Type[sphinx.domains.cpp.CPPDomain], Type[sphinx.domains.c.CDomain]
    ],
):
    """Patch C/C++ resolve_xref to add object type-dependent CSS classes."""
    orig_resolve_xref_inner = domain_class._resolve_xref_inner

    def _resolve_xref_inner(
        self: Union[CDomain, CPPDomain],
        env: sphinx.environment.BuildEnvironment,
        fromdocname: str,
        builder: sphinx.builders.Builder,
        typ: str,
        target: str,
        node: sphinx.addnodes.pending_xref,
        contnode: docutils.nodes.Element,
    ) -> Tuple[Optional[docutils.nodes.Element], Optional[str]]:
        refnode, objtype = orig_resolve_xref_inner(
            self,  # type: ignore[arg-type]
            env,
            fromdocname,
            builder,
            typ,
            target,
            node,
            contnode,  # type: ignore
        )
        if refnode is None:
            return refnode, objtype

        assert objtype is not None

        last_symbol = last_resolved_symbol.get_symbol()

        objtype = parameter_objects.get_precise_template_parameter_object_type(
            objtype, last_symbol
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

        if last_symbol is not None:
            refnode["reftitle"] = (
                object_description_options.format_object_description_tooltip(
                    env,
                    object_description_options.get_object_description_options(
                        env, self.name, objtype
                    ),
                    base_title=refnode["reftitle"],
                    synopsis=getattr(last_symbol.declaration, SYNOPSIS_ATTR, None),
                )
            )

        return refnode, objtype

    domain_class._resolve_xref_inner = _resolve_xref_inner  # type: ignore


def _monkey_patch_domain_get_object_synopses(
    domain_class: Union[Type[CDomain], Type[CPPDomain]],
):
    def get_object_synopses(
        self: Union[CDomain, CPPDomain],
    ) -> Iterator[Tuple[Tuple[str, str], str]]:
        for symbol in self.data["root_symbol"].get_all_symbols():
            if symbol.declaration is None:
                continue
            assert symbol.docname
            synopsis = getattr(symbol.declaration, SYNOPSIS_ATTR, None)
            if not synopsis:
                continue
            anchor = symbol_ids.get_symbol_anchor(symbol)
            yield ((symbol.docname, anchor), synopsis)

    domain_class.get_object_synopses = get_object_synopses  # type: ignore


_monkey_patch_add_object_type_and_synopsis(sphinx.domains.c.CDomain)
_monkey_patch_add_object_type_and_synopsis(sphinx.domains.cpp.CPPDomain)

_monkey_patch_domain_get_object_synopses(sphinx.domains.c.CDomain)
_monkey_patch_domain_get_object_synopses(sphinx.domains.cpp.CPPDomain)
