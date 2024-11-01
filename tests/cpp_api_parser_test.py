import re
from typing import cast

import pytest
from sphinx_immaterial.apidoc.cpp import api_parser


def test_basic():
    config = api_parser.Config(
        input_path="a.cpp",
        input_content=rb"""

/// This is the doc.
int foo(bool x, int y);

""",
    )

    output = api_parser.generate_output(config)
    assert not output.get("errors")
    entities = list(output["entities"].values())
    assert len(entities) == 1


def test_nondoc_comment():
    config = api_parser.Config(
        input_path="a.cpp",
        input_content=rb"""
struct string_view {};
struct string{};

/// Specifies a dimension of an index space by index or by label.
class DimensionIdentifier {
 public:
  /// Constructs from a label.
  DimensionIdentifier(string_view label) {
    //assert(label.data() != nullptr);
  }

  // Constructs from a label.
  //
  // Stores a reference to the `std::string` data, does not copy it.
  DimensionIdentifier(const string& label) {}
};
""",
    )

    output = api_parser.generate_output(config)
    assert not output.get("errors")
    print(output)
    entities = list(output["entities"].values())
    assert len(entities) == 2


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
///
/// \ingroup X
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
    assert not output.get("errors")
    assert not output.get("warnings")
    entities = list(output["entities"].values())
    assert len(entities) == 1
    requires = entities[0].get("requires")
    assert requires


@pytest.mark.parametrize(
    "doc_str,expected",
    [
        pytest.param(
            b"//! This is a docstring.\nint var = 0;",
            "This is a docstring.",
            id="slash-slash-bang",
        ),
        pytest.param(
            b"/// This is a docstring.\nint var = 0;",
            "This is a docstring.",
            id="slash-slash-slash",
        ),
        pytest.param(
            b"/** This is a docstring. */\nint var = 0;",
            "This is a docstring.",
            id="slash-star-star",
        ),
        pytest.param(
            b"/*! This is a docstring. */\nint var = 0;",
            "This is a docstring.",
            id="slash-star-bang",
        ),
        pytest.param(
            b"int var = 0; ///< This is a docstring.",
            "This is a docstring.",
            id="slash-slash-slash-lessthan",
        ),
        pytest.param(
            b"int var = 0; /**< This is a docstring. */",
            "This is a docstring.",
            id="slash-star-star-lessthan",
        ),
        pytest.param(
            b"int var = 0; /*!< This is a docstring. */",
            "This is a docstring.",
            id="slash-star-bang-lessthan",
        ),
        pytest.param(
            b"/**\n * This is a docstring.\n */\nint var = 0;",
            "\nThis is a docstring.",
            id="slash-star-star-newline-star",
        ),
        pytest.param(
            b"/*!\n * This is a docstring.\n */\nint var = 0;",
            "\nThis is a docstring.",
            id="slash-star-bang-newline-star",
        ),
        pytest.param(
            b"// Skip this.\n/// This is a docstring.\n// Skip this.\nint var = 0;",
            "This is a docstring.",
            id="slash-slash-skip-non-doc",
        ),
        pytest.param(
            b"/* Skip\n * this.*/\n/**This is a docstring.*/\n"
            b"/*Skip this.*/\nint var = 0;",
            "This is a docstring.",
            id="slash-star-skip-non-doc",
        ),
        pytest.param(
            b"""
/// First line.
// non-doc line
//- non-doc line again
/*! Fourth line. */
void foo();
""",
            "First line.\n\n\nFourth line.",
            id="doc-nondoc-doc",
        ),
        pytest.param(
            b"""
int foo; ///< First line.
         ///< Second line.
         /**< Third line. */
""",
            "First line.\nSecond line.\nThird line.",
            id="postfix-multiple",
        ),
    ],
)
def test_comment_styles(doc_str: bytes, expected: str):
    config = api_parser.Config(
        input_path="a.cpp",
        input_content=doc_str,
    )
    output = api_parser.generate_output(config)
    assert not output.get("errors")
    doc_strings = [
        cast(api_parser.JsonDocComment, v["doc"])["text"]
        for v in output.get("entities", {}).values()
        if v.get("doc")
    ]
    assert expected in doc_strings


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
    assert not output.get("errors")
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


def test_unnamed_template_parameter():
    config = api_parser.Config(
        input_path="a.cpp",
        compiler_flags=["-std=c++17", "-x", "c++"],
        input_content=rb"""
/// Tests something.
///
/// \ingroup Array
template <typename = void>
constexpr inline bool IsArray = false;
""",
    )

    output = api_parser.generate_output(config)
    assert not output.get("errors")
    assert not output.get("warnings")
    entities = output.get("entities", {})
    assert len(entities) == 1
    entity = list(entities.values())[0]
    tparams = entity["template_parameters"]
    assert tparams is not None
    assert tparams[0]["name"] == ""


def test_variable_template_specialization():
    config = api_parser.Config(
        input_path="a.cpp",
        compiler_flags=["-std=c++17", "-x", "c++"],
        input_content=rb"""
/// Check if it has A.
///
/// \ingroup Array
template <typename T>
constexpr inline bool HasA = false;

/// Specializes HasA for int.
/// \ingroup Array
/// \id int
template <>
constexpr inline bool HasA<int> = true;
""",
    )

    output = api_parser.generate_output(config)
    assert not output.get("errors")
    assert not output.get("warnings")
    entities = output.get("entities", {})
    assert len(entities) == 2
    assert sorted([entity["page_name"] for entity in entities.values()]) == [
        "HasA",
        "HasA-int",
    ]
