"""Tests that references to C objects can be resolved via cpp domain xrefs."""


def test_cpp_xref_resolves_to_c_obj(immaterial_make_app):
    app = immaterial_make_app(
        files={
            "index.rst": """
.. c:macro:: FOO

   Some macro.

:cpp:expr:`FOO`

:any:`FOO`
"""
        },
    )

    app.build()

    assert not app._warning.getvalue()
