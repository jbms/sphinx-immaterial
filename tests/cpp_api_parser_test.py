import re

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
        allow_paths=[re.escape(input_path)],
        disallow_namespaces=[re.compile("^std$")],
        compiler_flags=["-std=c++17"],
        input_content=input_content,
    )

    output = api_parser.generate_output(config)

    entities = list(output["entities"].values())
    assert len(entities) == 1
    requires = entities[0].get("requires")
    assert requires


def test_comment_strip():
    # this test can also be used for trailing doc strings (though it isn't supported yet)
    config = api_parser.Config(
        input_path="a.cpp",
        input_content="""
//! This is a docstring.
int var = 0;

/// This is a docstring.
int arr[1];

// Do not show this.
bool internal = true;  ///< This is a docstring.

/** This is a docstring. */
bool is_used = false;

/*! This is a docstring. */
bool is_useful = false;
""",
    )

    output = api_parser.generate_output(config)
    doc_strings = [
        v["doc"]["text"] for v in output.get("entities", {}).values()
    ]
    assert "Do not show this." not in doc_strings
    # count changes to 5 when supporting trailing doc strings
    assert doc_strings.count("This is a docstring.") >= 4

def test_function_fields():
    config = api_parser.Config(
        input_path="a.cpp",
        input_content="""
/// @brief A dummy function for tests.
///
/// \\details A more detailed paragraph.
///
/// @param arg1 An arg passed by value.
/// \\param[in] arg2 An unaltered arg passed by reference.
/// @param[in, out] arg3 An arg passed by reference that gets altered.
/// @retval int A negative number indicating a specific error, otherwise 0.
/// @returns A flag indicating success.
/// \\tparam T A template parameter.
template<typename T>
int function(T arg1, T &arg2, T &arg3);
"""
    )

    output = api_parser.generate_output(config)
    entities = output.get("entities", {})
    doc_str = ""
    for entity in entities.values():  # type: dict
        if entity.get("doc"):
            doc_str = entity["doc"]["text"]
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
            ":retval int: A negative number indicating a specific error, otherwise 0.",
            ":returns: A flag indicating success.",
            ":tparam T: A template parameter.",
        ]
    )
    assert expected == doc_str
