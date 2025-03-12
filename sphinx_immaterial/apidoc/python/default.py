import sphinx
import sphinx.application

from . import (
    annotation_style,  # noqa: F401
    attribute_style,  # noqa: F401
    autodoc_property_type,  # noqa: F401
    napoleon_admonition_classes,  # noqa: F401
    object_ids,  # noqa: F401
    parameter_objects,
    strip_property_prefix,
    strip_self_and_return_type_annotations,
    style_default_values_as_code,  # noqa: F401
    subscript_methods,  # noqa: F401
    synopses,  # noqa: F401
    type_annotation_transforms,
)


def setup(app: sphinx.application.Sphinx):
    app.setup_extension(parameter_objects.__name__)
    app.setup_extension(strip_property_prefix.__name__)
    app.setup_extension(type_annotation_transforms.__name__)
    app.setup_extension(strip_self_and_return_type_annotations.__name__)

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
