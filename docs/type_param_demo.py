import collections.abc
from typing import (
    TypeVar,
    Generic,
    overload,
    Iterable,
    Optional,
    KeysView,
    ValuesView,
    ItemsView,
    Iterator,
    Union,
)

K = TypeVar("K")
V = TypeVar("V")
T = TypeVar("T")
U = TypeVar("U")


class Map(Generic[K, V]):
    """Maps keys of type :py:param:`.K` to values of type :py:param:`.V`.

    Type parameters:
      K:
        Key type.
      V:
        Mapped value type.

    Group:
      type-param
    """

    @overload
    def __init__(self): ...

    @overload
    def __init__(self, items: collections.abc.Mapping[K, V]): ...

    @overload
    def __init__(self, items: Iterable[tuple[K, V]]): ...

    def __init__(self, items):
        """Construct from the specified items."""
        ...

    def clear(self):
        """Clear the map."""
        ...

    def keys(self) -> KeysView[K]:
        """Return a dynamic view of the keys."""
        ...

    def items(self) -> ItemsView[K, V]:
        """Return a dynamic view of the items."""
        ...

    def values(self) -> ValuesView[V]:
        """Return a dynamic view of the values."""
        ...

    @overload
    def get(self, key: K) -> Optional[V]: ...

    @overload
    def get(self, key: K, default: V) -> V: ...

    @overload
    def get(self, key: K, default: T) -> Union[V, T]: ...

    def get(self, key: K, default=None):
        """Return the mapped value, or the specified default.

        :param key: Key to retrieve.
        :param default: Default value to return if key is not present.
        """
        ...

    def __len__(self) -> int:
        """Return the number of items in the map."""
        ...

    def __contains__(self, key: K) -> bool:
        """Check if the map contains :py:param:`.key`."""
        ...

    def __getitem__(self, key: K) -> V:
        """Return the value associated with :py:param:`.key`.

        Raises:
          KeyError: if :py:param:`.key` is not present.
        """
        ...

    def __setitem__(self, key: K, value: V):
        """Set the value associated with the specified key."""
        ...

    def __delitem__(self, key: K):
        """Remove the value associated with the specified key.

        Raises:
          KeyError: if :py:param:`.key` is not present.
        """
        ...

    def __iter__(self) -> Iterator[K]:
        """Iterate over the keys."""
        ...


class Derived(Map[int, U], Generic[U]):
    """Map from integer keys to arbitrary values.

    Type parameters:
      U: Mapped value type.

    Group:
      type-param
    """

    pass


__all__ = ["Map", "Derived"]
