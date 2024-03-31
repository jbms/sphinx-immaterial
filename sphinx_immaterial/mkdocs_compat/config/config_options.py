"""Defines mkdocs-compatible field descriptor types."""

import typing


def Choice(*args):
    return (typing.Literal[args], None)


def Type(t, default=None):
    return (t, default)


def Optional(x):
    t, default = x
    return typing.Optional[t], default


def Deprecated(message: str):
    return (str, None)


def ListOfItems(x):
    t, default = x
    return (typing.List[t], [])  # type: ignore[valid-type]
