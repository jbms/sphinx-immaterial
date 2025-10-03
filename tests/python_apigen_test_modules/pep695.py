type MyAliasType = int | float
"""PEP 695 type alias that can be int or float.

Group:
  alias-group
"""


type MyGenericAliasType[T] = list[T] | tuple[T, ...]
"""PEP 695 type alias that can be a list or tuple with the given element type.

Group:
  alias-group
"""


class Bar[T]:
    """Class with PEP 695 type params."""


class Foo:
    """Foo class."""

    type MyMemberAlias = int | float
    """PEP 613 alias within a class."""

    type MyGenericMemberAlias[T, U] = list[T] | tuple[U, ...]
    """PEP 613 alias within a class."""
