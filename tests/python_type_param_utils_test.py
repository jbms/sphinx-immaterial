import typing

import pytest
import sphinx
from sphinx_immaterial.apidoc.python import type_param_utils

if sphinx.version_info < (7, 1):
    pytest.skip(
        f"Type parameters not supported by Sphinx {sphinx.version_info}",
        allow_module_level=True,
    )


T = typing.TypeVar("T")
U = typing.TypeVar("U")


class Foo(typing.Generic[T, U]):
    pass


class Bar1(Foo):
    pass


class Bar2(Foo, typing.Generic[U, T]):
    pass


class Bar3(Foo[int, T]):
    pass


def test_get_class_type_params():
    assert type_param_utils.get_class_type_params(int) == ()
    assert type_param_utils.get_class_type_params(Foo) == (T, U)
    assert type_param_utils.get_class_type_params(Bar1) == (T, U)
    assert type_param_utils.get_class_type_params(Bar2) == (U, T)
    assert type_param_utils.get_class_type_params(Bar3) == (T,)


def test_get_base_class_type_param_substitutions():
    class Bar4(Bar3[tuple[U, int]]):
        pass

    assert type_param_utils.get_base_class_type_param_substitutions(Bar4) == {
        Foo: {"T": "int", "U": "tuple[__SPHINX_IMMATERIAL_TYPE_VAR__V_U, int]"},
        Bar3: {"T": "tuple[__SPHINX_IMMATERIAL_TYPE_VAR__V_U, int]"},
    }
