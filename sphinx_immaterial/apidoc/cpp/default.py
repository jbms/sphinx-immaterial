import sphinx.application

from . import ast_fixes  # pylint: disable=unused-import
from . import cpp_resolve_c_xrefs  # pylint: disable=unused-import
from . import include_directives_in_signatures  # pylint: disable=unused-import
from . import last_resolved_symbol  # pylint: disable=unused-import
from . import macro_parameters  # pylint: disable=unused-import
from . import parameter_objects  # pylint: disable=unused-import
from . import signodes  # pylint: disable=unused-import
from . import strip_namespaces_from_signatures  # pylint: disable=unused-import
from . import symbol_ids  # pylint: disable=unused-import
from . import synopses  # pylint: disable=unused-import


def setup(app: sphinx.application.Sphinx):
    app.setup_extension(signodes.__name__)
    app.setup_extension(strip_namespaces_from_signatures.__name__)
    app.setup_extension(cpp_resolve_c_xrefs.__name__)

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
