import typing

_Config = typing.TypeVar("_Config")


class BasePlugin(typing.Generic[_Config]):
    config: _Config
