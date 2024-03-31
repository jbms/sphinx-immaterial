import typing

import pydantic


class _ConfigMeta:
    pass


class _ConfigBase(pydantic.BaseModel):
    @classmethod
    def keys(cls):
        return cls.model_fields

    def __getitem__(self, key):
        return getattr(self, key)


def _config_new(cls, name, bases, dct):
    members = {k: v for k, v in dct.items() if not k.startswith("__")}
    return pydantic.create_model(name, __base__=_ConfigBase, **members)


if typing.TYPE_CHECKING:
    Config = _ConfigBase
else:
    Config = _ConfigMeta()

# Must be set after creating `Config` to avoid using the custom `__new__`
# implementation.`
_ConfigMeta.__new__ = _config_new  # type: ignore[method-assign,assignment]
