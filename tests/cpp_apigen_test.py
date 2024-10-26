"""Tests cpp/apigen."""


def test_unnamed_template_parameter(immaterial_make_app):
    app = immaterial_make_app(
        extra_conf="""
extensions.append("sphinx_immaterial.apidoc.cpp.apigen")
""",
        confoverrides=dict(
            nitpicky=True,
            cpp_apigen_configs=[
                dict(
                    document_prefix="cpp_apigen_generated/",
                    api_parser_config=dict(
                        input_content=r"""
/// Tests if something is an array.
///
/// \ingroup Array
template <typename T, typename = void>
constexpr inline bool IsArray = false;
""",
                        compiler_flags=["-std=c++17", "-x", "c++"],
                        verbose=True,
                    ),
                ),
            ],
        ),
        files={
            "index.rst": """
.. cpp-apigen-group:: Array

"""
        },
    )

    app.build()

    assert not app._warning.getvalue()


def test_macro(immaterial_make_app):
    app = immaterial_make_app(
        extra_conf="""
extensions.append("sphinx_immaterial.apidoc.cpp.apigen")
""",
        confoverrides=dict(
            nitpicky=True,
            cpp_apigen_configs=[
                dict(
                    document_prefix="cpp_apigen_generated/",
                    api_parser_config=dict(
                        input_content=r"""
/// Tests something.
///
/// \ingroup Array
#define IS_ARRAY(x) x + 1
""",
                        compiler_flags=["-std=c++17", "-x", "c++"],
                        verbose=True,
                    ),
                ),
            ],
        ),
        files={
            "index.rst": """
.. cpp-apigen-group:: Array

"""
        },
    )

    app.build()

    assert not app._warning.getvalue()
