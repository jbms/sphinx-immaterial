import sphinx.application

from . import ast_fixes  # noqa: F401
from . import cpp_resolve_c_xrefs  # noqa: F401
from . import include_directives_in_signatures  # noqa: F401
from . import last_resolved_symbol  # noqa: F401
from . import macro_parameters  # noqa: F401
from . import parameter_objects  # noqa: F401
from . import signodes  # noqa: F401
from . import strip_namespaces_from_signatures  # noqa: F401
from . import symbol_ids  # noqa: F401
from . import synopses  # noqa: F401


def setup(app: sphinx.application.Sphinx):
    app.setup_extension(signodes.__name__)
    app.setup_extension(strip_namespaces_from_signatures.__name__)
    app.setup_extension(cpp_resolve_c_xrefs.__name__)

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
