"""Fixes limitations of the Sphinx C++ parser."""

import sphinx

if sphinx.version_info >= (8, 2):
    from . import (  # noqa: F401
        fix_cpp_domain_symbol_resolution_through_type_aliases,
    )
else:
    from . import (  # noqa: F401
        fix_cpp_domain_symbol_resolution_through_type_aliases_sphinx81,
    )

if sphinx.version_info < (5, 2):
    from . import (  # noqa: F401
        fix_cpp_domain_requires_clause,  # noqa: F401
        fix_cpp_is_pack,  # noqa: F401
        fix_cpp_symbol_to_normalize_template_args,
    )
