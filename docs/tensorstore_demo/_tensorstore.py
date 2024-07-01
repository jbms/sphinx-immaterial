"""Demo file for Python API documentation generation.

This defines some entities that are aliased into the `tensorstore_demo` module.
"""

import typing


class Foo:
    """
    This is a class defined in the ``tensorstore_demo._tensorstore`` module
    but should appear to be defined in the ``tensorstore_demo`` module.

    Group:
      Some other group
    """

    def bar(self, x: int) -> int:
        """Returns :py:param:`x`.

        :param x: Parameter to :py:obj:`.bar`.
        """
        pass


def bar(x: Foo) -> Foo:
    """Returns :py:param:`x`.

    :param x: Parameter to :py:obj:`.bar`.

    Group:
      Some other group.
    """
    pass


bar_also = bar


class FooSubclass(Foo):
    """This is a subclass of :py:obj:`.Foo`.

    Group:
      Some other group.
    """

    def baz(self, x: str) -> str:
        """Does the baz operation."""
        return x

    @typing.overload
    def overloaded_method(self, x: int) -> int:
        pass

    @typing.overload
    def overloaded_method(self, x: str) -> str:
        pass

    def overloaded_method(self, x):
        """Returns its argument."""
        return x
