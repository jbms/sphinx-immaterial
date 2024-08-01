"""Optional type annotation transformations."""

import ast
import functools
import re
from typing import (
    cast,
    Dict,
    Union,
    Optional,
    Tuple,
    Sequence,
    NamedTuple,
    Pattern,
    List,
)

import docutils.nodes
import sphinx
import sphinx.application
import sphinx.domains.python
import sphinx.environment
import sphinx.util.logging

from . import type_param_utils

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
    parent = _get_ast_dotted_name(cast(Union[ast.Name, ast.Attribute], node.value))
    if parent is None:
        return None
    return f"{parent}.{node.attr}"


def _dotted_name_to_ast(
    name: str, ctx: ast.expr_context
) -> Union[ast.Name, ast.Attribute]:
    parts = name.split(".")
    tree: Union[ast.Name, ast.Attribute] = ast.Name(parts[0], ctx)
    for part in parts[1:]:
        tree = ast.Attribute(tree, part, ctx)
    return tree


_CONFIG_ATTR = "_sphinx_immaterial_python_type_transform_config"


class TypeTransformConfig(NamedTuple):
    transform: bool
    transform_names: bool
    aliases: Dict[str, str]
    module_aliases: Dict[str, str]
    module_replacements_pattern: Optional[Pattern[str]]
    concise_literal: bool
    pep604: bool
    strip_modules_from_xrefs_pattern: Optional[Pattern[str]]

    def transform_dotted_name(self, dotted_name: str) -> str:
        aliases = self.aliases
        if aliases:
            new_name = aliases.get(dotted_name)
            if new_name is not None:
                return new_name
        module_replacements_pattern = self.module_replacements_pattern
        if module_replacements_pattern:
            dotted_name = module_replacements_pattern.sub(
                lambda m: self.module_aliases[m.group(0)], dotted_name
            )
        return dotted_name


def _retain_explicit_literal(node: ast.AST) -> bool:
    """Checks if the concise literal syntax cannot be used.

    Since constants cannot be types, there is no ambiguity.
    """
    return not isinstance(node, ast.Constant)


class TypeAnnotationTransformer(ast.NodeTransformer):
    """Transforms the AST of a type annotation to improve readability.

    - Converts Union/Optional/Literal to "|" syntax allowed by PEP 604.  This
      syntax is not actually supported until Python 3.10 but displays better in
      the documentation.
    """

    config: TypeTransformConfig

    def visit_Name(self, node: ast.Name) -> ast.AST:
        if self.config.transform_names:
            dotted_name = node.id
            new_dotted_name = self.config.transform_dotted_name(dotted_name)
            if dotted_name != new_dotted_name:
                return _dotted_name_to_ast(new_dotted_name, node.ctx)
        return self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> ast.AST:
        if self.config.transform_names:
            dotted_name = _get_ast_dotted_name(node)
            if dotted_name is not None:
                new_dotted_name = self.config.transform_dotted_name(dotted_name)
                if new_dotted_name != dotted_name:
                    return _dotted_name_to_ast(new_dotted_name, node.ctx)
        return self.generic_visit(node)

    def visit_UnaryOp(self, node: ast.UnaryOp) -> ast.AST:
        if not isinstance(node.op, ast.Invert) or not isinstance(
            node.operand, ast.Subscript
        ):
            return self.generic_visit(node)
        operand, pep604_transformed = self._transform_subscript_pep604(node.operand)
        if pep604_transformed:
            return operand
        return ast.UnaryOp(node.op, operand)

    def _transform_subscript_pep604(self, node: ast.Subscript) -> Tuple[ast.AST, bool]:
        if not self.config.pep604:
            return self.generic_visit(node), False
        value = self.visit(node.value)
        id_str = _get_ast_dotted_name(value)
        if id_str in ("typing.Optional", "typing.Union", "typing.Literal"):
            slice_expr: ast.AST = node.slice
            elts: Sequence[ast.AST]
            if isinstance(slice_expr, ast.Index):
                slice_expr = slice_expr.value  # type: ignore
            if isinstance(slice_expr, ast.Tuple):
                elts = slice_expr.elts
            else:
                elts = [slice_expr]
            elts = [self.visit(x) for x in elts]
            if id_str == "typing.Optional":
                elts.append(ast.Constant(value=None))
            elif id_str == "typing.Literal":
                elts = [
                    ast.Subscript(value, x, node.ctx)
                    if not self.config.concise_literal or _retain_explicit_literal(x)
                    else x
                    for x in elts
                ]
            result = functools.reduce(
                (lambda left, right: ast.BinOp(left, ast.BitOr(), right)), elts
            )
            return result, True
        return ast.Subscript(value, self.visit(node.slice), node.ctx), False

    def visit_Subscript(self, node: ast.Subscript) -> ast.AST:
        return self._transform_subscript_pep604(node)[0]


def _monkey_patch_python_domain_to_transform_type_annotations():
    if sphinx.version_info >= (7, 3):
        orig_parse_annotation = sphinx.domains.python._annotations._parse_annotation  # type: ignore[attr-defined]
    else:
        orig_parse_annotation = sphinx.domains.python._parse_annotation

    def _parse_annotation(annotation: str, env: sphinx.environment.BuildEnvironment):
        transformer_config = getattr(env.app, _CONFIG_ATTR, None)
        if transformer_config is None or not transformer_config.transform:
            return orig_parse_annotation(annotation, env)

        try:
            tree = ast.parse(annotation, type_comments=True)
        except SyntaxError:
            return orig_parse_annotation(annotation, env)

        transformer = TypeAnnotationTransformer()
        transformer.config = cast(TypeTransformConfig, transformer_config)
        tree = ast.fix_missing_locations(transformer.visit(tree))
        annotation = ast.unparse(tree)
        return orig_parse_annotation(annotation, env)

    if sphinx.version_info >= (7, 3):
        sphinx.domains.python._annotations._parse_annotation = _parse_annotation  # type: ignore[assignment,attr-defined]
        sphinx.domains.python._object._parse_annotation = _parse_annotation  # type: ignore[assignment,attr-defined]
    sphinx.domains.python._parse_annotation = _parse_annotation  # type: ignore[assignment]


def _builder_inited(app: sphinx.application.Sphinx):
    config = app.config

    aliases: Dict[str, str] = {}
    module_aliases: Dict[str, str] = {}

    if config.python_transform_type_annotations_pep585:
        aliases.update(PEP585_ALIASES)

    if config.python_resolve_unqualified_typing:
        for name in TYPING_NAMES:
            full_name = f"typing.{name}"
            aliases[name] = aliases.get(full_name, full_name)

    if config.python_transform_typing_extensions:
        module_aliases["typing_extensions."] = "typing."

    for source_name, target_name in config.python_type_aliases.items():
        if source_name.endswith("."):
            if target_name and not target_name.endswith("."):
                logger.error(
                    "Invalid python_type_aliases entry %r -> %r: "
                    "source names ending in '.' must map to either "
                    "the empty string or a target name ending in '.'",
                    source_name,
                    target_name,
                )
                continue
            module_aliases[source_name] = target_name
        else:
            aliases[source_name] = target_name

    module_replacements_pattern: Optional[Pattern[str]] = None

    if module_aliases:
        module_replacements_pattern = re.compile(
            "|".join(f"(?:^{re.escape(name)})" for name in module_aliases)
        )

    if (
        config.python_transform_type_annotations_concise_literal
        and not config.python_transform_type_annotations_pep604
    ):
        logger.error(
            "python_transform_type_annotations_concise_literal=True "
            "requires python_transform_type_annotations_pep604=True"
        )

    strip_modules_from_xrefs_pattern: Optional[Pattern[str]] = None

    if config.python_module_names_to_strip_from_xrefs:
        strip_modules_from_xrefs_pattern = re.compile(
            "|".join(
                f"(?:^{re.escape(x)}\\.)"
                for x in config.python_module_names_to_strip_from_xrefs
            )
        )

    setattr(
        app,
        _CONFIG_ATTR,
        TypeTransformConfig(
            transform=bool(
                aliases
                or config.python_transform_type_annotations_pep604
                or module_aliases
            ),
            transform_names=bool(aliases or module_aliases),
            aliases=aliases,
            module_aliases=module_aliases,
            module_replacements_pattern=module_replacements_pattern,
            concise_literal=config.python_transform_type_annotations_concise_literal,
            pep604=config.python_transform_type_annotations_pep604,
            strip_modules_from_xrefs_pattern=strip_modules_from_xrefs_pattern,
        ),
    )


def _monkey_patch_python_domain_to_transform_xref_titles():
    if sphinx.version_info >= (7, 3):
        orig_type_to_xref = sphinx.domains.python._annotations.type_to_xref
    else:
        orig_type_to_xref = sphinx.domains.python.type_to_xref

    def type_to_xref(
        target: str,
        env: sphinx.environment.BuildEnvironment,
        *args,
        suppress_prefix: bool = False,
    ) -> sphinx.addnodes.pending_xref:
        if (type_param := type_param_utils.decode_type_param(target)) is not None:
            refnode = sphinx.addnodes.pending_xref(
                "",
                docutils.nodes.Text(type_param.__name__),
                refdomain="py",
                reftype="param",
                reftarget=type_param.__name__,
                refspecific=True,
                refexplicit=True,
                refwarn=True,
            )
            refnode["py:func"] = env.ref_context.get("py:func")
            refnode["py:class"] = env.ref_context.get("py:class")
            refnode["py:module"] = env.ref_context.get("py:module")
            return refnode

        if sphinx.version_info < (7, 2):
            # suppress_prefix may not have been used like a kwarg before v7.2.0 as
            # there was only 3 params for type_to_xref() prior to v7.2.0
            if args:
                suppress_prefix = args[0]
            node = orig_type_to_xref(target, env, suppress_prefix=suppress_prefix)
        else:
            node = orig_type_to_xref(  # type: ignore[misc]
                target, env, *args, suppress_prefix=suppress_prefix
            )
        if (
            not suppress_prefix
            and len(node.children) == 1
            and node.children[0].astext() == target
        ):
            transformer_config = getattr(env.app, _CONFIG_ATTR, None)
            if transformer_config is not None:
                strip_modules_from_xrefs_pattern = (
                    transformer_config.strip_modules_from_xrefs_pattern
                )
                if strip_modules_from_xrefs_pattern is not None:
                    new_target = strip_modules_from_xrefs_pattern.sub("", target)
                    if new_target != target:
                        del node.children[:]
                        node.append(docutils.nodes.Text(new_target))
        return node

    if sphinx.version_info >= (7, 3):
        sphinx.domains.python._annotations.type_to_xref = type_to_xref  # type: ignore[assignment]
    sphinx.domains.python.type_to_xref = type_to_xref  # type: ignore[assignment]


_monkey_patch_python_domain_to_transform_type_annotations()
_monkey_patch_python_domain_to_transform_xref_titles()


def setup(app: sphinx.application.Sphinx):
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
        "python_transform_typing_extensions",
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

    app.add_config_value(
        "python_module_names_to_strip_from_xrefs",
        default=[],
        types=(List[str],),
        rebuild="env",
    )

    app.connect("builder-inited", _builder_inited)

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
