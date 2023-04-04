import re
from typing import cast

import pytest
from sphinx_immaterial.apidoc.cpp import api_parser


def test_basic():
    config = api_parser.Config(
        input_path="a.cpp",
        input_content=b"""

/// This is the doc.
int foo(bool x, int y);

""",
    )

    output = api_parser.generate_output(config)
    entities = list(output["entities"].values())
    assert len(entities) == 1


def test_enable_if_transform():
    input_path = "a.cpp"

    input_content = rb"""
namespace std {
template <bool Condition, typename T = void>
using enable_if_t = T;
template <typename T, typename U>
constexpr inline bool is_convertible_v = false;
}

/// This is the doc.
template <typename U, typename T, typename = std::enable_if_t<std::is_convertible_v<U(*)[], T(*)[]>>>
int foo(T x);

"""

    config = api_parser.Config(
        input_path=input_path,
        allow_paths=[re.compile(re.escape(input_path))],
        disallow_namespaces=[re.compile("^std$")],
        compiler_flags=["-std=c++17"],
        input_content=input_content,
    )

    output = api_parser.generate_output(config)

    entities = list(output["entities"].values())
    assert len(entities) == 1
    requires = entities[0].get("requires")
    assert requires


class TestCommentStrip:
    config = api_parser.Config(
        input_path="a.cpp",
    )

    def assert_output(self, expected: str):
        output = api_parser.generate_output(self.config)
        doc_strings = [
            cast(api_parser.JsonDocComment, v["doc"])["text"]
            for v in output.get("entities", {}).values()
            if v.get("doc")
        ]
        assert expected in doc_strings

    @pytest.mark.parametrize(
        argnames="doc_str,expected",
        argvalues=[
            (b"//! This is a docstring.\nint var = 0;", "This is a docstring."),
            (b"/// This is a docstring.\nint var = 0;", "This is a docstring."),
            (b"/** This is a docstring. */\nint var = 0;", "This is a docstring."),
            (
                b"/*! This is a docstring. */\nint var = 0;",
                "This is a docstring.",
            ),
            (
                b"int var = 0; ///< This is a docstring.",
                "This is a docstring.",
            ),
            (
                b"/**\n * This is a docstring.\n */\nint var = 0;",
                "\nThis is a docstring.",
            ),
            (
                b"/*!\n * This is a docstring.\n */\nint var = 0;",
                "\nThis is a docstring.",
            ),
            (
                b"// Skip this.\n/// This is a docstring.\n// Skip this.\nint var = 0;",
                "This is a docstring.",
            ),
            (
                b"/* Skip\n * this.*/\n/**This is a docstring.*/\n"
                b"/*Skip this.*/\nint var = 0;",
                "This is a docstring.",
            ),
        ],
        ids=[
            "///",
            "//!",
            "/**",
            "/*!",
            "///<",
            "/** \n * \n */",
            "/*! \n * \n */",
            "// \n /// \n //",
            "/* \n * \n */\n /** */\n /* */",
        ],
    )
    def test_comment_styles(self, doc_str: bytes, expected: str):
        self.config.input_content = doc_str
        self.assert_output(expected)


def test_function_fields():
    config = api_parser.Config(
        input_path="a.cpp",
        input_content=rb"""
/// @brief A dummy function for tests.
///
/// \details A more detailed paragraph.
///
/// @param arg1 An arg passed by value.
/// \param[in] arg2 An unaltered arg passed by reference.
/// @param[in, out] arg3 An arg passed by reference that gets altered.
/// @retval NULL If unsuccessful.
/// @returns A flag indicating success.
/// \tparam T A template parameter.
template<typename T>
int function(T arg1, T &arg2, T &arg3);
""",
    )

    output = api_parser.generate_output(config)
    entities = output.get("entities", {})
    doc_str = ""
    for entity in entities.values():
        doc = entity.get("doc")
        if doc is not None:
            doc_str = doc["text"]
            break
    else:
        raise AttributeError("no doc string found.")
    expected = "\n".join(
        [
            "A dummy function for tests.",
            "",
            "A more detailed paragraph.",
            "",
            ":param arg1: An arg passed by value.",
            ":param arg2[in]: An unaltered arg passed by reference.",
            ":param arg3[in, out]: An arg passed by reference that gets altered.",
            ":retval NULL: If unsuccessful.",
            ":returns: A flag indicating success.",
            ":tparam T: A template parameter.",
        ]
    )
    assert expected == doc_str
