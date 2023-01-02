"""Fixes limitations of the Sphinx C++ parser."""

import sphinx

from . import fix_cpp_domain_symbol_resolution_through_type_aliases  # type: ignore[unused-import]

if sphinx.version_info < (5, 2):
    from . import fix_cpp_domain_requires_clause  # type: ignore[unused-import]
    from . import fix_cpp_is_pack  # type: ignore[unused-import]
    from . import fix_cpp_symbol_to_normalize_template_args  # type: ignore[unused-import]
