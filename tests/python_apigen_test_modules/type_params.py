from typing import TypeVar

T = TypeVar("T")


def foo(x: T) -> T:
    """Foo function.

    :param x: Something or other.
    """
    return x


def bar(x: T) -> T:
    return x


class C:
    def get(self, x: T, y: T) -> T:
        """Get function.

        :param x: Something or other.
        :param y: Another param.
        :type y: T
        """
        return x


__all__ = ["foo", "bar", "C"]
