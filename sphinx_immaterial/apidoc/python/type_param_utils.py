"""Utilities related to Python type parameter lists."""

import sys
import re
import typing

import sphinx
from sphinx.util.inspect import safe_getattr
import sphinx.util.typing


TYPE_VAR_ANNOTATION_PREFIX = "__SPHINX_IMMATERIAL_TYPE_VAR__"
"""Prefix used by monkey-patched `stringify_annotation` to indicate a TypeVar.

This prefix is checked in a monkey-patched `type_to_xref` where it is converted
into a parameter reference.
"""


if sys.version_info >= (3, 10):
    TypeParam = typing.Union[typing.TypeVar, typing.ParamSpec]
elif sys.version_info >= (3, 11):
    TypeParam = typing.Union[typing.TypeVar, typing.TypeVarTuple, typing.ParamSpec]
else:
    TypeParam = typing.TypeVar


def get_class_type_params(cls: type) -> tuple[TypeParam, ...]:
    """Returns the ordered list of type parameters of a class."""

    type_params = safe_getattr(cls, "__type_params__", ())
    if type_params:
        return type_params

    origin = typing.get_origin(cls)
    if origin is None:
        origin = cls
    if isinstance(origin, type) and not issubclass(origin, typing.Generic):  # type: ignore[arg-type]
        return ()

    args = typing.get_args(cls)
    if args:
        return tuple(arg for arg in args if isinstance(arg, TypeParam))  # type: ignore[misc,arg-type]

    bases = safe_getattr(cls, "__orig_bases__", ())
    if not bases:
        bases = safe_getattr(cls, "__bases__", ())
    if not bases:
        return ()

    # First check for `typing.Generic`, since that takes precedence.
    for base in bases:
        if typing.get_origin(base) is typing.Generic:
            return typing.get_args(base)

    params: dict[TypeParam, bool] = {}
    for base in bases:
        cur_params = get_class_type_params(base)
        for param in cur_params:
            params.setdefault(param, True)
    return tuple(params)


def stringify_type_params(type_params: typing.Iterable[TypeParam]) -> str:
    """Convert a type parameter list to its string representation.

    The string representation is suitable for embedding in a Python domain
    signature.
    """
    if not type_params:
        return ""
    parts = ["["]
    for i, param in enumerate(type_params):
        if i != 0:
            parts.append(",")
        if isinstance(param, typing.TypeVar):
            parts.append(param.__name__)
            parts.append("")

            if bound := param.__bound__:
                parts.append(" : ")
                parts.append(sphinx.util.typing.stringify_annotation(bound))
            if constraints := param.__constraints__:
                parts.append(" : (")
                for j, constraint in enumerate(constraints):
                    if j != 0:
                        parts.append(", ")
                    parts.append(sphinx.util.typing.stringify_annotation(constraint))
                parts.append(")")
    parts.append("]")
    return "".join(parts)


TypeParamSubstitutions = dict[str, str]


def substitute_type_params(
    stringified_annotation: str, substitutions: typing.Optional[TypeParamSubstitutions]
) -> str:
    if not substitutions:
        return stringified_annotation
    return _ENCODED_TYPE_PARAM_PATTERN.sub(
        lambda m: substitutions.get(m[2], m[0]),
        stringified_annotation,
    )


def _get_base_class_type_param_substitutions_impl(
    cls: type,
    substitutions: TypeParamSubstitutions,
    base_classes: dict[type, TypeParamSubstitutions],
):
    bases = safe_getattr(cls, "__orig_bases__", ())
    for base in bases:
        base_origin = typing.get_origin(base) or base
        if isinstance(base_origin, type) and not issubclass(
            base_origin,
            typing.Generic,  # type: ignore[arg-type]
        ):
            continue
        if base_origin is typing.Generic:
            continue
        params = get_class_type_params(base_origin)
        args = typing.get_args(base)

        base_substitutions: TypeParamSubstitutions = {}

        for param, arg in zip(params, args):
            s_arg = substitute_type_params(
                sphinx.util.typing.stringify_annotation(arg), substitutions
            )
            base_substitutions[param.__name__] = s_arg

        base_classes.setdefault(base_origin, base_substitutions)

        _get_base_class_type_param_substitutions_impl(
            base_origin, base_substitutions, base_classes
        )


def get_base_class_type_param_substitutions(
    cls: type,
) -> dict[type, TypeParamSubstitutions]:
    base_classes: dict[type, TypeParamSubstitutions] = {}
    _get_base_class_type_param_substitutions_impl(cls, {}, base_classes)
    return base_classes


_ENCODE_TYPE_PARAM: dict[type[TypeParam], typing.Callable[[TypeParam], str]] = {
    typing.TypeVar: lambda annotation: (
        TYPE_VAR_ANNOTATION_PREFIX + "V_" + annotation.__name__
    ),
}
_DECODE_TYPE_PARAM: dict[str, typing.Callable[[str], TypeParam]] = {
    "V": typing.TypeVar,
}

if sys.version_info >= (3, 10):
    _ENCODE_TYPE_PARAM[typing.ParamSpec] = (
        lambda annotation: TYPE_VAR_ANNOTATION_PREFIX + "P_" + annotation.__name__
    )
    _DECODE_TYPE_PARAM["P"] = typing.ParamSpec
if sys.version_info >= (3, 11):
    _ENCODE_TYPE_PARAM[typing.TypeVarTuple] = (  # type: ignore[index]
        lambda annotation: TYPE_VAR_ANNOTATION_PREFIX + "T_" + annotation.__name__
    )
    _DECODE_TYPE_PARAM["T"] = typing.TypeVarTuple  # type: ignore[assignment]


_ENCODED_TYPE_PARAM_PATTERN = re.compile(
    r"\b"
    + TYPE_VAR_ANNOTATION_PREFIX
    + "(["
    + "".join(_DECODE_TYPE_PARAM.keys())
    + r"])_(\w+)\b"
)


def decode_type_param(annotation: str) -> typing.Optional[TypeParam]:
    m = _ENCODED_TYPE_PARAM_PATTERN.fullmatch(annotation)
    if m is None:
        return None
    kind = m[1]
    name = m[2]
    decode = _DECODE_TYPE_PARAM[kind]
    return decode(name)


def encode_type_param(annotation: TypeParam) -> str:
    return _ENCODE_TYPE_PARAM[type(annotation)](annotation)


def get_type_params_from_signature(signature: str) -> dict[str, TypeParam]:
    params = {}
    for m in _ENCODED_TYPE_PARAM_PATTERN.finditer(signature):
        name = m[2]
        if name in params:
            continue
        kind = m[1]
        decode = _DECODE_TYPE_PARAM[kind]
        params[name] = decode(name)
    return params


def _monkey_patch_stringify_annotation_to_support_type_params():
    """In order to properly resolve references to type parameters in signatures,
    they need to be given the `py:param` role with a target of the unqualified
    type name.

    Normally, when `sphinx.ext.autodoc` encounters a TypeVar within a type
    annotation, it formats it as `<module_name>.<type_name>`. As this is
    indistinguishable from any other class name, our monkey-patched
    `type_to_xref` would have no way to know when to create a `py:param`
    reference instead of the usual `py:class` reference.

    As a workaround, monkey-patch `stringify_annotation` to format `TypeVar`
    annotations as `TYPE_VAR_ANNOTATION_PREFIX + type_name`. This special prefix
    is then detected and stripped off by the monkey-patched `type_to_xref`
    defined in type_annotation_transforms.py.
    """
    orig = sphinx.util.typing.stringify_annotation

    def stringify_annotation(
        annotation: typing.Any,
        /,
        mode="fully-qualified-except-typing",
    ) -> str:
        if (encode := _ENCODE_TYPE_PARAM.get(type(annotation))) is not None:
            return encode(annotation)
        return orig(annotation, mode=mode)

    for module in [
        "sphinx.util.typing",
        "sphinx.ext.autodoc",
        "sphinx.ext.autodoc.typehints",
        "sphinx.util.inspect",
        "sphinx.ext.napoleon.docstring",
    ]:
        m = sys.modules.get(module)
        if m is None:
            continue
        if getattr(m, "stringify_annotation", None) is orig:
            setattr(m, "stringify_annotation", stringify_annotation)

    deprecated_objects = getattr(sphinx.util.typing, "_DEPRECATED_OBJECTS", {})
    if "stringify" in deprecated_objects:
        deprecated_objects["stringify"] = (stringify_annotation,) + deprecated_objects[
            "stringify"
        ][1:]


if sphinx.version_info < (7, 1):
    # Type parameters are not supported by Sphinx<7.1. Always just return an
    # empty type parameter list.

    def get_class_type_params(cls: type) -> tuple[TypeParam, ...]:
        return ()

    def get_type_params_from_signature(signature: str) -> dict[str, TypeParam]:
        return {}

else:
    _monkey_patch_stringify_annotation_to_support_type_params()
