import typing


MyAlias: typing.TypeAlias = int | float
"""PEP 613 type alias that can be int or float.

Group:
  alias-group
"""


T = typing.TypeVar("T")
U = typing.TypeVar("U")

MyGenericAlias: typing.TypeAlias = list[T] | tuple[T, ...]
"""My generic alias that can be a list or tuple with the given element type.

Group:
  alias-group
"""


class Foo:
    """Foo class."""

    MyMemberAlias: typing.TypeAlias = int | float
    """PEP 613 alias within a class."""

    MyGenericMemberAlias: typing.TypeAlias = list[T] | tuple[U, ...]
    """PEP 613 alias within a class."""
