import sphinx.application

from . import annotation_style
from . import object_ids
from . import synopses
from . import parameter_objects
from . import style_default_values_as_code
from . import subscript_methods
from . import attribute_style
from . import napoleon_admonition_classes
from . import strip_property_prefix
from . import section_titles
from . import autodoc_property_type
from . import type_annotation_transforms
from . import strip_self_and_return_type_annotations


def setup(app: sphinx.application.Sphinx):
    app.setup_extension(parameter_objects.__name__)
    app.setup_extension(strip_property_prefix.__name__)
    app.setup_extension(type_annotation_transforms.__name__)
    app.setup_extension(strip_self_and_return_type_annotations.__name__)

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
