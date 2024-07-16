"""Wraps various signature elements in designated nodes.

This allows other extensions to identify those elements more easily.
"""

from typing import Type

import docutils.nodes
import sphinx.addnodes
import sphinx.application
import sphinx.domains.cpp
from sphinx.domains.cpp import ASTTemplateParams


class desc_cpp_template_param(sphinx.addnodes.desc_sig_element):
    """Wraps a single template parameter.

    This allows template parameters to be more easily identified when
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
        orig_describe_signature_as_introducer(
            self, fake_parent, mode, env, symbol, lineSpec
        )
        for x in fake_parent.findall(condition=sphinx.addnodes.desc_name):
            # Ensure template parameter names aren't styled as the main entity
            # name.
            x["classes"].append("sig-name-nonprimary")
        parentNode.extend(fake_parent.children)

    ASTTemplateParams.describe_signature_as_introducer = (  # type: ignore[assignment]
        describe_signature_as_introducer
    )


def _monkey_patch_cpp_ast_wrap_signature_node(
    ast_type: Type[sphinx.domains.cpp.ASTBase],
    wrapper_type: Type[docutils.nodes.TextElement],
):
    """Patches an AST node type to wrap its signature with a docutils node."""
    orig_describe_signature = ast_type.describe_signature  # type: ignore

    def describe_signature(
        self: sphinx.domains.cpp.ASTBase,
        signode: docutils.nodes.TextElement,
        *args,
        **kwargs,
    ) -> None:
        wrapper = wrapper_type("", "")
        signode += wrapper
        orig_describe_signature(self, wrapper, *args, **kwargs)

    ast_type.describe_signature = describe_signature  # type: ignore


_monkey_patch_cpp_ast_template_params()


def _monkey_patch_cpp_ast_template_param_nodes():
    for ast_type in (
        sphinx.domains.cpp.ASTTemplateParamType,
        sphinx.domains.cpp.ASTTemplateParamTemplateType,
        sphinx.domains.cpp.ASTTemplateParamNonType,
    ):
        _monkey_patch_cpp_ast_wrap_signature_node(
            ast_type=ast_type, wrapper_type=desc_cpp_template_param
        )


_monkey_patch_cpp_ast_template_param_nodes()
_monkey_patch_cpp_ast_wrap_signature_node(
    ast_type=sphinx.domains.cpp.ASTExplicitSpec, wrapper_type=desc_cpp_explicit
)
_monkey_patch_cpp_ast_wrap_signature_node(
    ast_type=sphinx.domains.cpp.ASTRequiresClause,
    wrapper_type=desc_cpp_requires_clause,
)


def setup(app: sphinx.application.Sphinx):
    for node in (
        desc_cpp_template_param,
        desc_cpp_requires_clause,
        desc_cpp_explicit,
    ):
        app.add_node(node)

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
