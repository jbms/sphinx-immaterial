"""Patch C and C++ domain resolve_xref implementation.

This adds support for:

- Resolving C macros from C++ domain xrefs.  This allows a role like
  `cpp:expr` to match both C++ symbols and C macro and macro parameters.
  https://github.com/sphinx-doc/sphinx/issues/10262

- Normal resolution of missing symbols starting with `std::`.  Normally, the
  C++ domain silences warnings about these symbols in a way that blocks
  `missing-reference` handlers from receiving them.
"""

import re
from typing import Optional, Tuple, List, cast

import docutils.nodes
import sphinx.addnodes
import sphinx.domains.c
import sphinx.domains.cpp

from sphinx.domains.cpp import CPPExprRole

# We monkey patch `resolve_xref` multiple times.  We must call
# `_monkey_patch_cpp_resolve_c_xrefs` last, to ensure that the other logic only
# runs once.
from . import last_resolved_symbol  # noqa: F401
from . import synopses  # noqa: F401

POSSIBLE_MACRO_TARGET_PATTERN = re.compile("^[A-Z]+[A-Z_0-9]*(?:::[a-zA-Z0-9_]+)?$")
"""Pattern for targets that may possibly refer to a macro or macro parameter.

Any targets matching this pattern that are not defined as C++ symbols will be
looked up in the C domain.

For efficiency, this is restricted to names that consist of only uppercase
letters and digits, to avoid a duplicate C domain query for all symbols that
will be resolved by `sphinx_immaterial.apidoc.cpp.external_cpp_references`.

Since macro parameters are named as "<MACRO_NAME>::<PARAMETER_NAME>", this
pattern allows "::" even though it would normally only match C++ symbols.
"""

POSSIBLE_MACRO_PARAMETER_TARGET_PATTERN = re.compile("[^<>:()]+$")
"""Pattern for targets that may refer to a macro parameter within the scope of a
C macro definition.
"""


def _monkey_patch_cpp_resolve_c_xrefs():
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
            # chance to resolve it.
            return None, None

        if refnode is not None:
            return refnode, objtype

        if typ == "any":
            # Don't forward to C domain for :any: xrefs, since it leads to an
            # error determining the role type in CPPDomain.resolve_any_xref, and
            # the C domain will have an opportunity to resolve this reference
            # anyway.
            return refnode, objtype

        macro_pattern = getattr(env.app, C_MACRO_PATTERN_ATTR, None)

        if (macro_pattern is not None and macro_pattern.fullmatch(target)) or (
            POSSIBLE_MACRO_PARAMETER_TARGET_PATTERN.fullmatch(target)
            and node.get("c:parent_key")
        ):
            # Give C domain a chance to resolve it.
            c_domain = cast(sphinx.domains.c.CDomain, env.get_domain("c"))
            return c_domain._resolve_xref_inner(
                env, fromdocname, builder, typ, target, node, contnode
            )

        return None, None

    sphinx.domains.cpp.CPPDomain._resolve_xref_inner = _resolve_xref_inner  # type: ignore[assignment]


def _monkey_patch_cpp_expr_role_to_include_c_parent_key():
    """Includes ``c:parent_key`` in pending_xref nodes created by CPPExprRole.

    This allows CPPExprRole to be used from the context of C object descriptions,
    in particular macros.
    """

    orig_run = CPPExprRole.run

    def run(
        self: CPPExprRole,
    ) -> Tuple[List[docutils.nodes.Node], List[docutils.nodes.system_message]]:
        nodes, messages = orig_run(self)
        c_parent_key = self.env.ref_context.get("c:parent_key")
        if c_parent_key is not None:
            for node in nodes:
                for refnode in node.findall(condition=sphinx.addnodes.pending_xref):
                    if refnode.get("refdomain") == "cpp":
                        refnode["c:parent_key"] = c_parent_key
        return nodes, messages

    CPPExprRole.run = run  # type: ignore[assignment]


_monkey_patch_cpp_resolve_c_xrefs()
_monkey_patch_cpp_expr_role_to_include_c_parent_key()


C_MACRO_PATTERN_ATTR = "_sphinx_immaterial_cpp_xref_c_macro_pattern"


def _config_inited(
    app: sphinx.application.Sphinx, config: sphinx.config.Config
) -> None:
    c_macro_pattern = config.cpp_xref_resolve_c_macro_pattern
    # Compute a regular expression that matches a macro name, or macro with
    # `::<param>` suffix.
    setattr(
        app,
        C_MACRO_PATTERN_ATTR,
        re.compile("(?:" + c_macro_pattern + ")(?:::[a-zA-Z0-9_]+)?"),
    )


def setup(app: sphinx.application.Sphinx):
    app.add_config_value(
        "cpp_xref_resolve_c_macro_pattern",
        default="[A-Z]+[A-Z_0-9]*",
        types=(str,),
        rebuild="env",
    )
    app.connect("config-inited", _config_inited)

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
