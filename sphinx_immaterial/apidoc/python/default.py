import sphinx
import sphinx.application

from . import annotation_style  # noqa: F401
from . import object_ids  # noqa: F401
from . import synopses  # noqa: F401
from . import parameter_objects
from . import style_default_values_as_code  # noqa: F401
from . import subscript_methods  # noqa: F401
from . import attribute_style  # noqa: F401
from . import napoleon_admonition_classes  # noqa: F401
from . import strip_property_prefix
from . import autodoc_property_type  # noqa: F401
from . import type_annotation_transforms
from . import strip_self_and_return_type_annotations

if sphinx.version_info < (5, 3):
    from . import section_titles  # noqa: F401


def setup(app: sphinx.application.Sphinx):
    app.setup_extension(parameter_objects.__name__)
    app.setup_extension(strip_property_prefix.__name__)
    app.setup_extension(type_annotation_transforms.__name__)
    app.setup_extension(strip_self_and_return_type_annotations.__name__)

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
