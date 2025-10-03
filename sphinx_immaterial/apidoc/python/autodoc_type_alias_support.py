"""Adds TypeAlias and TypeAliasType support to autodoc."""

import ast
import sys
import typing
from typing import Any, TypeAlias, ClassVar

import sphinx

if sphinx.version_info < (7, 4):
    raise ValueError("Sphinx >= 7.4 required for type alias support")

import sphinx.application
from sphinx.ext.autodoc import (
    Documenter,
    DataDocumenter,
    AttributeDocumenter,
    ModuleDocumenter,
)
import sphinx.util.typing
import sphinx.util.inspect
import sphinx.domains.python
from sphinx.pycode.parser import VariableCommentPicker
import typing_extensions

if sys.version_info >= (3, 12):
    TYPE_ALIAS_TYPES = (typing.TypeAliasType, typing_extensions.TypeAliasType)
    TYPE_ALIAS_AST_NODES = (ast.TypeAlias,)
else:
    TYPE_ALIAS_TYPES = typing_extensions.TypeAliasType
    TYPE_ALIAS_AST_NODES = ()


class TypeAliasDocumenter(DataDocumenter):
    priority = max(DataDocumenter.priority, AttributeDocumenter.priority) + 1
    objtype = "type"
    option_spec: ClassVar[sphinx.util.typing.OptionSpec] = dict(Documenter.option_spec)
    option_spec["no-value"] = DataDocumenter.option_spec["no-value"]

    @classmethod
    def can_document_member(
        cls: type[Documenter], member: Any, membername: str, isattr: bool, parent: Any
    ) -> bool:
        if isinstance(member, TYPE_ALIAS_TYPES):
            return True

        if not isattr:
            return False

        type_hints = sphinx.util.typing.get_type_hints(
            parent.object, include_extras=True
        )
        return type_hints.get(membername) is TypeAlias

    def add_directive_header(self, sig: str) -> None:
        Documenter.add_directive_header(self, sig)
        sourcename = self.get_sourcename()
        try:
            if self.options.no_value or self.should_suppress_value_header():
                pass
            else:
                value = self.object
                if isinstance(value, TYPE_ALIAS_TYPES):
                    value = value.__value__
                objrepr = sphinx.util.typing.stringify_annotation(value)
                self.add_line("   :canonical: " + objrepr, sourcename)
        except ValueError:
            pass


def _monkey_patch_sphinx_analyzer_to_support_type_aliases():
    orig_visit = VariableCommentPicker.visit

    def visit(self, node: ast.AST) -> None:
        if isinstance(node, TYPE_ALIAS_AST_NODES):
            new_node = ast.Assign(targets=[node.name], value=node.value)
            ast.copy_location(new_node, node)
            ast.fix_missing_locations(new_node)
            node = new_node
        orig_visit(self, node)

    VariableCommentPicker.visit = visit


def _monkey_patch_sphinx_pr_13926():
    # https://github.com/sphinx-doc/sphinx/pull/13926

    PyTypeAlias = sphinx.domains.python.PyTypeAlias

    orig_add_target_and_index = PyTypeAlias.add_target_and_index

    def add_target_and_index(self, name_cls, sig, signode) -> None:
        saved_canonical = self.options.get("canonical", False)
        try:
            self.options.pop("canonical", None)
            orig_add_target_and_index(self, name_cls, sig, signode)
        finally:
            if saved_canonical is not False:
                self.options["canonical"] = saved_canonical

    PyTypeAlias.add_target_and_index = add_target_and_index


_monkey_patch_sphinx_analyzer_to_support_type_aliases()
_monkey_patch_sphinx_pr_13926()


def setup(app: sphinx.application.Sphinx):
    app.add_autodocumenter(TypeAliasDocumenter)
    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
