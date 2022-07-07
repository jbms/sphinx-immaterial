import sphinx.application

from . import ast_fixes  # type: ignore[unused-import]
from . import cpp_resolve_c_xrefs  # type: ignore[unused-import]
from . import include_directives_in_signatures  # type: ignore[unused-import]
from . import last_resolved_symbol  # type: ignore[unused-import]
from . import macro_parameters  # type: ignore[unused-import]
from . import parameter_objects  # type: ignore[unused-import]
from . import signodes  # type: ignore[unused-import]
from . import strip_namespaces_from_signatures  # type: ignore[unused-import]
from . import symbol_ids  # type: ignore[unused-import]
from . import synopses  # type: ignore[unused-import]


def setup(app: sphinx.application.Sphinx):
    app.setup_extension(signodes.__name__)
    app.setup_extension(strip_namespaces_from_signatures.__name__)
    app.setup_extension(cpp_resolve_c_xrefs.__name__)

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
