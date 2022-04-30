"""Optional type annotation transformations."""

import functools
import sys
from typing import (
    Dict,
    Union,
    Optional,
    Tuple,
)

import sphinx.application
import sphinx.domains.python
import sphinx.environment
from sphinx.pycode.ast import ast
import sphinx.util.logging

logger = sphinx.util.logging.getLogger(__name__)

PEP585_ALIASES = {
    "typing.Tuple": "tuple",
    "typing.List": "list",
    "typing.Dict": "dict",
    "typing.DefaultDict": "collections.defaultdict",
    "typing.OrderedDict": "collections.OrderedDict",
    "typing.Counter": "collections.Counter",
    "typing.Set": "set",
    "typing.Callable": "collections.abc.Callable",
    "typing.Deque": "collections.deque",
    "typing.FrozenSet": "frozenset",
    "typing.Type": "type",
    "typing.AbstractSet": "collections.abc.Set",
    "typing.ByteString": "collections.abc.ByteString",
    "typing.Collection": "collections.abc.Collection",
    "typing.Container": "collections.abc.Container",
    "typing.ItemsView": "collections.abc.ItemsView",
    "typing.KeysView": "collections.abc.KeysView",
    "typing.Mapping": "collections.abc.Mapping",
    "typing.MappingView": "collections.abc.MappingView",
    "typing.MutableMapping": "collections.abc.MutableMapping",
    "typing.MutableSequence": "collections.abc.MutableSequence",
    "typing.MutableSet": "collections.abc.MutableSet",
    "typing.Sequence": "collections.abc.Sequence",
    "typing.ValuesView": "collections.abc.ValuesView",
    "typing.Iterable": "collections.abc.Iterable",
    "typing.Iterator": "collections.abc.Iterator",
    "typing.Generator": "collections.abc.Generator",
    "typing.Hashable": "collections.abc.Hashable",
    "typing.Reversible": "collections.abc.Reversible",
    "typing.Sized": "collections.abc.Sized",
    "typing.Coroutine": "collections.abc.Coroutine",
    "typing.AsyncGenerator": "collections.abc.AsyncGenerator",
    "typing.AsyncIterable": "collections.abc.AsyncIterable",
    "typing.AsyncIterator": "collections.abc.AsyncIterator",
    "typing.Awaitable": "collections.abc.Awaitable",
    "typing.ContextManager": "contextlib.AbstractContextManager",
    "typing.AsyncContextManager": "contextlib.AbstractAsyncContextManager",
    "typing.Pattern": "re.Pattern",
    "typing.re.Pattern": "re.Pattern",
    "typing.Match": "re.Match",
    "typing.re.Match": "re.Match",
}

TYPING_NAMES = [
    "Any",
    "Tuple",
    "Optional",
    "Union",
    "Literal",
    "Callable",
    "List",
    "Dict",
    "Set",
    "FrozenSet",
    "Sequence",
    "Type",
]


def _get_ast_dotted_name(node: Union[ast.Name, ast.Attribute]) -> Optional[str]:
    if isinstance(node, ast.Name):
        return node.id
    parent = _get_ast_dotted_name(node.value)
    if parent is None:
        return None
    return f"{parent}.{node.attr}"


def _dotted_name_to_ast(name: str, ctx: ast.expr_context) -> ast.AST:
    parts = name.split(".")
    tree = ast.Name(parts[0], ctx)
    for part in parts[1:]:
        tree = ast.Attribute(tree, part, ctx)
    return tree


if sys.version_info < (3, 8):
    _CONSTANT_AST_NODE_TYPES = (
        ast.Constant,
        ast.Num,
        ast.Str,
        ast.Bytes,
        ast.Ellipsis,
        ast.NameConstant,
    )
else:
    _CONSTANT_AST_NODE_TYPES = (ast.Constant,)


def _retain_explicit_literal(node: ast.AST) -> bool:
    """Checks if the concise literal syntax cannot be used.

    Since constants cannot be types, there is no ambiguity.
    """
    return not isinstance(node, _CONSTANT_AST_NODE_TYPES)


class TypeAnnotationTransformer(ast.NodeTransformer):
    """Transforms the AST of a type annotation to improve readability.

    - Converts Union/Optional/Literal to "|" syntax allowed by PEP 604.  This
      syntax is not actually supported until Python 3.10 but displays better in
      the documentation.
    """

    aliases: Dict[str, str]
    concise_literal: bool
    pep604: bool

    def visit_Name(self, node: ast.Name) -> ast.AST:
        aliases = self.aliases
        if aliases:
            dotted_name = node.id
            new_name = aliases.get(dotted_name)
            if new_name is not None:
                return _dotted_name_to_ast(new_name, node.ctx)
        return self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> ast.AST:
        aliases = self.aliases
        if aliases:
            dotted_name = _get_ast_dotted_name(node)
            if dotted_name is not None:
                new_name = aliases.get(dotted_name)
                if new_name is not None:
                    return _dotted_name_to_ast(new_name, node.ctx)
        return self.generic_visit(node)

    def visit_UnaryOp(self, node: ast.Invert) -> ast.AST:
        if not isinstance(node.op, ast.Invert) or not isinstance(
            node.operand, ast.Subscript
        ):
            return self.generic_visit(node)
        operand, pep604_transformed = self._transform_subscript_pep604(node.operand)
        if pep604_transformed:
            return operand
        return ast.UnaryOp(node.op, operand)

    def _transform_subscript_pep604(self, node: ast.Subscript) -> Tuple[ast.AST, bool]:
        if not self.pep604:
            return self.generic_visit(self), False
        value = self.visit(node.value)
        id_str = _get_ast_dotted_name(value)
        if id_str in ("typing.Optional", "typing.Union", "typing.Literal"):
            elts = node.slice
            if isinstance(node.slice, ast.Index):
                elts = elts.value
            if isinstance(elts, ast.Tuple):
                elts = elts.elts
            else:
                elts = [node.slice]
            elts = [self.visit(x) for x in elts]
            if id_str == "typing.Optional":
                elts.append(ast.Constant(value=None))
            elif id_str == "typing.Literal":
                elts = [
                    ast.Subscript(value, x, node.ctx)
                    if not self.concise_literal or _retain_explicit_literal(x)
                    else x
                    for x in elts
                ]
            result = functools.reduce(
                (lambda left, right: ast.BinOp(left, ast.BitOr(), right)), elts
            )
            return result, True
        return ast.Subscript(value, self.visit(node.slice), node.ctx), False

    def visit_Subscript(self, node: ast.Subscript) -> ast.AST:
        value = self.visit(node.value)
        id_str = _get_ast_dotted_name(value)
        if id_str is None:
            return ast.Subscript(value, self.visit(node.slice), node.ctx)
        if id_str in ("typing.Optional", "typing.Union", "typing.Literal"):
            elts = node.slice
            if isinstance(node.slice, ast.Index):
                elts = elts.value
            if isinstance(elts, ast.Tuple):
                elts = elts.elts
            else:
                elts = [node.slice]
            elts = [self.visit(x) for x in elts]
            if id_str == "typing.Optional":
                elts.append(ast.Constant(value=None))
            elif id_str == "typing.Literal":
                elts = [
                    ast.Subscript(value, x, node.ctx)
                    if not self.concise_literal or _retain_explicit_literal(x)
                    else x
                    for x in elts
                ]
            result = functools.reduce(
                (lambda left, right: ast.BinOp(left, ast.BitOr(), right)), elts
            )
            return result
        return ast.Subscript(value, self.visit(node.slice), node.ctx)


def _monkey_patch_python_domain_to_transform_type_annotations():

    orig_parse_annotation = sphinx.domains.python._parse_annotation

    def _parse_annotation(annotation: str, env: sphinx.environment.BuildEnvironment):
        if not env._sphinx_immaterial_python_type_transform:
            return orig_parse_annotation(annotation, env)
        try:
            orig_ast_parse = sphinx.domains.python.ast_parse

            def ast_parse(annotation: str) -> ast.AST:
                tree = orig_ast_parse(annotation)
                config = env.config
                transformer = TypeAnnotationTransformer()
                transformer.aliases = env._sphinx_immaterial_python_type_aliases
                transformer.pep604 = config.python_transform_type_annotations_pep604
                transformer.concise_literal = (
                    config.python_transform_type_annotations_concise_literal
                )
                return ast.fix_missing_locations(transformer.visit(tree))

            sphinx.domains.python.ast_parse = ast_parse
            return orig_parse_annotation(annotation, env)
        finally:
            sphinx.domains.python.ast_parse = orig_ast_parse

    sphinx.domains.python._parse_annotation = _parse_annotation


def _builder_inited(app: sphinx.application.Sphinx):
    config = app.config

    aliases = {}
    if config.python_transform_type_annotations_pep585:
        aliases.update(PEP585_ALIASES)

    if config.python_resolve_unqualified_typing:
        for name in TYPING_NAMES:
            full_name = f"typing.{name}"
            aliases[name] = aliases.get(full_name, full_name)

    aliases.update(config.python_type_aliases)

    if (
        config.python_transform_type_annotations_concise_literal
        and not config.python_transform_type_annotations_pep604
    ):
        logger.error(
            "python_transform_type_annotations_concise_literal=True "
            "requires python_transform_type_annotations_pep604=True"
        )

    app.env._sphinx_immaterial_python_type_aliases = aliases

    app.env._sphinx_immaterial_python_type_transform = (
        aliases or config.python_transform_type_annotations_pep604
    )


def setup(app: sphinx.application.Sphinx):
    _monkey_patch_python_domain_to_transform_type_annotations()

    app.add_config_value(
        "python_type_aliases",
        default={},
        types=(Dict[str, str],),
        rebuild="env",
    )

    app.add_config_value(
        "python_resolve_unqualified_typing",
        default=True,
        types=(bool,),
        rebuild="env",
    )

    app.add_config_value(
        "python_transform_type_annotations_pep585",
        default=True,
        types=(bool,),
        rebuild="env",
    )

    app.add_config_value(
        "python_transform_type_annotations_pep604",
        default=True,
        types=(bool,),
        rebuild="env",
    )

    app.add_config_value(
        "python_transform_type_annotations_concise_literal",
        default=True,
        types=(bool,),
        rebuild="env",
    )

    app.connect("builder-inited", _builder_inited)

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
