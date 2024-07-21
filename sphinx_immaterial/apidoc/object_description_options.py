import functools
import re
from typing import List, Tuple, Pattern, Dict, Any, Optional, NamedTuple, cast

import pydantic
import sphinx.application
import sphinx.environment
import sphinx.util.logging

logger = sphinx.util.logging.getLogger(__name__)

ObjectDescriptionOptions = Dict[str, Any]


def format_object_description_tooltip(
    env: sphinx.environment.BuildEnvironment,
    options: ObjectDescriptionOptions,
    base_title: str,
    synopsis: Optional[str],
) -> str:
    title = base_title

    domain = env.get_domain(options["domain"])

    if options["include_object_type_in_xref_tooltip"]:
        object_type = options["object_type"]
        title += f" ({domain.get_type_name(domain.object_types[object_type])})"

    if synopsis:
        title += f" — {synopsis}"

    return title


DEFAULT_OBJECT_DESCRIPTION_OPTIONS: List[Tuple[str, dict]] = [
    ("std:envvar", {"toc_icon_class": "alias", "toc_icon_text": "$"}),
    ("js:module", {"toc_icon_class": "data", "toc_icon_text": "r"}),
    ("js:function", {"toc_icon_class": "procedure", "toc_icon_text": "M"}),
    ("js:method", {"toc_icon_class": "procedure", "toc_icon_text": "M"}),
    ("js:class", {"toc_icon_class": "data", "toc_icon_text": "C"}),
    ("js:data", {"toc_icon_class": "alias", "toc_icon_text": "V"}),
    ("js:attribute", {"toc_icon_class": "alias", "toc_icon_text": "V"}),
    ("json:schema", {"toc_icon_class": "data", "toc_icon_text": "J"}),
    ("json:subschema", {"toc_icon_class": "sub-data", "toc_icon_text": "j"}),
    ("py:class", {"toc_icon_class": "data", "toc_icon_text": "C"}),
    ("py:function", {"toc_icon_class": "procedure", "toc_icon_text": "F"}),
    ("py:method", {"toc_icon_class": "procedure", "toc_icon_text": "M"}),
    ("py:classmethod", {"toc_icon_class": "procedure", "toc_icon_text": "M"}),
    ("py:staticmethod", {"toc_icon_class": "procedure", "toc_icon_text": "M"}),
    ("py:property", {"toc_icon_class": "alias", "toc_icon_text": "P"}),
    ("py:attribute", {"toc_icon_class": "alias", "toc_icon_text": "A"}),
    ("py:data", {"toc_icon_class": "alias", "toc_icon_text": "V"}),
    (
        "py:parameter",
        {
            "toc_icon_class": "sub-data",
            "toc_icon_text": "p",
            "generate_synopses": "first_sentence",
        },
    ),
    (
        "py:typeParameter",
        {
            "toc_icon_class": "alias",
            "toc_icon_text": "T",
            "generate_synopses": "first_sentence",
        },
    ),
    ("c:member", {"toc_icon_class": "alias", "toc_icon_text": "V"}),
    ("c:var", {"toc_icon_class": "alias", "toc_icon_text": "V"}),
    ("c:function", {"toc_icon_class": "procedure", "toc_icon_text": "F"}),
    ("c:macro", {"toc_icon_class": "alias", "toc_icon_text": "D"}),
    ("c:union", {"toc_icon_class": "data", "toc_icon_text": "U"}),
    ("c:struct", {"toc_icon_class": "data", "toc_icon_text": "S"}),
    ("c:enum", {"toc_icon_class": "data", "toc_icon_text": "E"}),
    ("c:enumerator", {"toc_icon_class": "data", "toc_icon_text": "e"}),
    ("c:type", {"toc_icon_class": "alias", "toc_icon_text": "T"}),
    (
        "c:macroParam",
        {
            "toc_icon_class": "sub-data",
            "toc_icon_text": "p",
            "generate_synopses": "first_sentence",
        },
    ),
    ("cpp:class", {"toc_icon_class": "data", "toc_icon_text": "C"}),
    ("cpp:struct", {"toc_icon_class": "data", "toc_icon_text": "S"}),
    ("cpp:enum", {"toc_icon_class": "data", "toc_icon_text": "E"}),
    ("cpp:enum-class", {"toc_icon_class": "data", "toc_icon_text": "E"}),
    ("cpp:enum-struct", {"toc_icon_class": "data", "toc_icon_text": "E"}),
    ("cpp:enumerator", {"toc_icon_class": "data", "toc_icon_text": "e"}),
    ("cpp:union", {"toc_icon_class": "data", "toc_icon_text": "U"}),
    ("cpp:concept", {"toc_icon_class": "data", "toc_icon_text": "t"}),
    ("cpp:function", {"toc_icon_class": "procedure", "toc_icon_text": "F"}),
    ("cpp:alias", {"toc_icon_class": "procedure", "toc_icon_text": "F"}),
    ("cpp:member", {"toc_icon_class": "alias", "toc_icon_text": "V"}),
    ("cpp:var", {"toc_icon_class": "alias", "toc_icon_text": "V"}),
    ("cpp:type", {"toc_icon_class": "alias", "toc_icon_text": "T"}),
    ("cpp:namespace", {"toc_icon_class": "alias", "toc_icon_text": "N"}),
    (
        "cpp:functionParam",
        {
            "toc_icon_class": "sub-data",
            "toc_icon_text": "p",
            "generate_synopses": "first_sentence",
        },
    ),
    (
        "cpp:templateTypeParam",
        {
            "toc_icon_class": "alias",
            "toc_icon_text": "T",
            "generate_synopses": "first_sentence",
        },
    ),
    (
        "cpp:templateNonTypeParam",
        {
            "toc_icon_class": "data",
            "toc_icon_text": "N",
            "generate_synopses": "first_sentence",
        },
    ),
    (
        "cpp:templateTemplateParam",
        {
            "toc_icon_class": "alias",
            "toc_icon_text": "T",
            "generate_synopses": "first_sentence",
        },
    ),
    ("rst:directive", {"toc_icon_class": "data", "toc_icon_text": "D"}),
    ("rst:directive:option", {"toc_icon_class": "sub-data", "toc_icon_text": "o"}),
    ("rst:role", {"toc_icon_class": "procedure", "toc_icon_text": "R"}),
]


def get_object_description_option_registry(app: sphinx.application.Sphinx):
    key = "sphinx_immaterial_object_description_option_registry"
    registry = getattr(app, key, None)
    if registry is None:
        registry = {}
        setattr(app, key, registry)
    return registry


class RegisteredObjectDescriptionOption(NamedTuple):
    type_constraint: Any
    default: Any


def add_object_description_option(
    app: sphinx.application.Sphinx, name: str, default: Any, type_constraint: Any = Any
) -> None:
    registry = get_object_description_option_registry(app)
    if name in registry:
        logger.error(f"Object description option {name!r} already registered")
    default = pydantic.TypeAdapter(type_constraint).validate_python(default)
    registry[name] = RegisteredObjectDescriptionOption(
        default=default, type_constraint=type_constraint
    )


def get_object_description_options(
    env: Optional[sphinx.environment.BuildEnvironment],
    domain: Optional[str],
    object_type: Optional[str],
) -> ObjectDescriptionOptions:
    return env.app._sphinx_immaterial_get_object_description_options(  # type: ignore
        domain, object_type
    )


def _builder_inited(app: sphinx.application.Sphinx) -> None:
    registry = get_object_description_option_registry(app)
    options_map: Dict[str, List[Tuple[int, Dict[str, Any]]]] = {}
    options_patterns: List[Tuple[Pattern, int, Dict[str, Any]]] = []

    default_options = {}
    for name, registered_option in registry.items():
        default_options[name] = registered_option.default

    # Validate options
    for i, (pattern, options) in enumerate(
        cast(
            List[Tuple[Pattern, Dict[str, Any]]],
            pydantic.TypeAdapter(List[Tuple[Pattern, Dict[str, Any]]]).validate_python(
                DEFAULT_OBJECT_DESCRIPTION_OPTIONS
                + app.config.object_description_options,
            ),
        )
    ):
        for name, value in options.items():
            registered_option = registry.get(name)
            if registered_option is None:
                logger.error(
                    "Undefined object description option %r specified for pattern %r",
                    name,
                    pattern.pattern,
                )
                continue
            try:
                options[name] = pydantic.TypeAdapter(
                    registered_option.type_constraint
                ).validate_python(value)
            except Exception as e:
                logger.error(
                    "Invalid value %r for object description option"
                    " %r specified for pattern %r: %s",
                    value,
                    name,
                    pattern.pattern,
                    e,
                )
        if pattern.pattern == re.escape(pattern.pattern):
            # Pattern just matches a single string.
            options_map.setdefault(pattern.pattern, []).append((i, options))
        else:
            options_patterns.append((pattern, i, options))

    @functools.lru_cache(maxsize=None)
    def get_options(domain: str, object_type: str) -> Dict[str, Any]:
        key = f"{domain}:{object_type}"
        matches = options_map.get(key)
        if matches is None:
            matches = []
        else:
            matches = list(matches)
        for pattern, i, options in options_patterns:
            if pattern.fullmatch(key):
                matches.append((i, options))
        matches.sort(key=lambda x: x[0])
        full_options = default_options.copy()
        for _, m in matches:
            full_options.update(m)
        full_options.update(domain=domain, object_type=object_type)
        return full_options

    app._sphinx_immaterial_get_object_description_options = get_options  # type: ignore


def setup(app: sphinx.application.Sphinx):
    app.add_config_value(
        "object_description_options",
        default=[],
        rebuild="env",
        types=(List[Tuple[Pattern, Dict[str, Any]]],),
    )

    add_object_description_option(
        app, "include_object_type_in_xref_tooltip", type_constraint=bool, default=True
    )

    app.connect("builder-inited", _builder_inited)

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
