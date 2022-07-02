import re

from sphinx_immaterial.apidoc.cpp import api_parser


def test_basic():

    config = api_parser.Config(
        input_path="a.cpp",
        input_content=b"""

/// This is the doc.
int foo(bool x, int y);

""")

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
        input_content=input_content)

    output = api_parser.generate_output(config)

    entities = list(output["entities"].values())
    assert len(entities) == 1
    requires = entities[0].get("requires")
    assert requires
