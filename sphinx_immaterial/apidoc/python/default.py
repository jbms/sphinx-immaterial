import sphinx
import sphinx.application

from . import annotation_style  # pylint: disable=unused-import
from . import object_ids  # pylint: disable=unused-import
from . import synopses  # pylint: disable=unused-import
from . import parameter_objects
from . import style_default_values_as_code  # pylint: disable=unused-import
from . import subscript_methods  # pylint: disable=unused-import
from . import attribute_style  # pylint: disable=unused-import
from . import napoleon_admonition_classes  # pylint: disable=unused-import
from . import strip_property_prefix
from . import autodoc_property_type  # pylint: disable=unused-import
from . import type_annotation_transforms
from . import strip_self_and_return_type_annotations

if sphinx.version_info < (5, 3):
    from . import section_titles  # pylint: disable=unused-import


def setup(app: sphinx.application.Sphinx):
    app.setup_extension(parameter_objects.__name__)
    app.setup_extension(strip_property_prefix.__name__)
    app.setup_extension(type_annotation_transforms.__name__)
    app.setup_extension(strip_self_and_return_type_annotations.__name__)

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
