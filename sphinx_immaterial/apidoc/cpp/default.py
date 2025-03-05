import sphinx.application

from . import (
    ast_fixes,  # noqa: F401
    cpp_resolve_c_xrefs,  # noqa: F401
    include_directives_in_signatures,  # noqa: F401
    last_resolved_symbol,  # noqa: F401
    macro_parameters,  # noqa: F401
    parameter_objects,  # noqa: F401
    signodes,  # noqa: F401
    strip_namespaces_from_signatures,  # noqa: F401
    symbol_ids,  # noqa: F401
    synopses,  # noqa: F401
)


def setup(app: sphinx.application.Sphinx):
    app.setup_extension(signodes.__name__)
    app.setup_extension(strip_namespaces_from_signatures.__name__)
    app.setup_extension(cpp_resolve_c_xrefs.__name__)

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
