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
/** First line. */
/* non-doc block comment */
/**/
/*! Fourth line. */
void foo();
""",
            "First line.\n\n\nFourth line.",
            id="block-doc-nondoc-empty-doc",
        ),
        pytest.param(
            b"/// Doc line.\n/**/ void foo();",
            "Doc line.",
            id="macro-empty-comment-before-decl",
        ),
        pytest.param(
            b"/** Doc line. */ /**/ void foo();",
            "Doc line.",
            id="block-doc-and-inline-empty-comment",
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


def test_type_replacements():
    config = api_parser.Config(
        input_path="a.cpp",
        input_content=rb"""
struct source_location {};

namespace foo {
struct SourceLocation {};
}

/// Default method
foo::SourceLocation Default();

/// Logging method
void LogSourceLocation(foo::SourceLocation loc = Default());

/// Class
class ClassWithSourceLocation {
 public:
  /// Constructor.
  ClassWithSourceLocation(foo::SourceLocation loc = Default())
    : loc_(loc) {}

  foo::SourceLocation loc_;
};
""",
        type_replacements={
            "foo::SourceLocation": "source_location",
        },
    )

    output = api_parser.generate_output(config)
    assert not output.get("errors")
    print(output)

    assert len(output.get("entities", {}).values()) == 4
    for x in output["entities"].values():
        d = x.get("declaration")
        if d:
            assert cast(str, d).find("source_location") != -1


def test_using_declaration():
    config = api_parser.Config(
        input_path="a.cpp",
        input_content=rb"""
template <typename U>
struct Wrapper {};

/// Base class.
///
/// \ingroup X
class Base {
 public:
  /// Constructs Base.
  explicit Base(int x);
  Base(int x, int y);
  /// Value type alias.
  using ValueType = int;
  /// Waits for completion.
  void Wait() const;
  void Wait(int timeout) const;
  /// Resets the state.
  void reset();
};

/// Templated base class.
///
/// \ingroup X
template <typename T>
class TemplatedBase {
 public:
  /// Checks readiness.
  bool Ready() const;
};

/// Derived class.
///
/// \ingroup X
template <typename T>
class Derived : public Base, public TemplatedBase<Wrapper<T>> {
 public:
  /// Inherits Base constructors.
  using Base::Base;
  /// Exposes ValueType.
  using Base::ValueType;
  /// Waits for completion.
  using Base::Wait;
  using Base::reset;
  /// Checks readiness via nested template argument.
  using TemplatedBase<Wrapper<T>>::Ready;
};

namespace detail_ns {
void FreeHelper(int x);
void FreeHelper(int x, int y);
}

namespace pub_ns {
/// Re-exported overloaded free function.
///
/// \ingroup X
using detail_ns::FreeHelper;
}
""",
    )
    output = api_parser.generate_output(config)
    assert not output.get("errors")
    assert not output.get("warnings")
    page_names = sorted(
        entity["page_name"]
        for entity in output["entities"].values()
        if "page_name" in entity
    )
    assert page_names == [
        "Base",
        "Base.Base",
        "Base.ValueType",
        "Base.Wait",
        "Base.reset",
        "Derived",
        "Derived.Derived",
        "Derived.Ready",
        "Derived.ValueType",
        "Derived.Wait",
        "TemplatedBase",
        "TemplatedBase.Ready",
        "pub_ns.FreeHelper",
    ]
    by_page = {
        entity["page_name"]: entity
        for entity in output["entities"].values()
        if "page_name" in entity
    }

    derived_ctor = by_page["Derived.Derived"]
    assert derived_ctor["kind"] == "constructor"
    assert derived_ctor["name"] == "Derived"
    assert " ".join(derived_ctor["declaration"].split()) == "explicit __x0(int x)"
    ctor_siblings = derived_ctor.get("siblings", [])
    assert len(ctor_siblings) == 1
    ctor_sibling = output["entities"][ctor_siblings[0]]
    assert ctor_sibling["kind"] == "constructor"
    assert ctor_sibling["name"] == "Derived"
    assert " ".join(ctor_sibling["declaration"].split()) == "__x0(int x, int y)"

    derived_alias = by_page["Derived.ValueType"]
    assert derived_alias["kind"] == "alias"
    assert derived_alias["underlying_type"] == "int"

    derived_wait = by_page["Derived.Wait"]
    assert derived_wait["kind"] == "method"
    assert derived_wait["declaration"] == "void __x0() const"
    siblings = derived_wait.get("siblings", [])
    assert len(siblings) == 1
    sibling = output["entities"][siblings[0]]
    assert sibling["kind"] == "method"
    assert sibling["declaration"] == "void __x0(int timeout) const"

    free_helper = by_page["pub_ns.FreeHelper"]
    assert free_helper["kind"] == "function"
    assert free_helper.get("scope") == "pub_ns::"
    assert free_helper["declaration"] == "void __x0(int x)"
    free_siblings = free_helper.get("siblings", [])
    assert len(free_siblings) == 1
    free_sibling = output["entities"][free_siblings[0]]
    assert free_sibling["kind"] == "function"
    assert free_sibling.get("scope") == "pub_ns::"
    assert free_sibling["declaration"] == "void __x0(int x, int y)"


def test_var_decl_hide_types():
    config = api_parser.Config(
        input_path="a.cpp",
        hide_types=[re.compile(r"\binternal_ns::")],
        input_content=rb"""
namespace internal_ns {
struct Tag {};
struct Niebloid {
  template <typename T>
  auto operator()(T&& v) const {
    return 0;
  }
};
struct CallbackNiebloid {
  void operator()(void (*cb)() const) const & {}
};
struct PtrNiebloid {
  int* operator()() const { return nullptr; }
};
}

/// Tag constant.
///
/// \ingroup X
constexpr auto kTag = internal_ns::Tag{};

/// Formats values.
///
/// \ingroup X
constexpr auto Format = internal_ns::Niebloid{};

/// Invokes a const function pointer.
///
/// \ingroup X
constexpr auto Invoke = internal_ns::CallbackNiebloid{};

/// Returns a pointer.
///
/// \ingroup X
constexpr auto GetPtr = internal_ns::PtrNiebloid{};

/// Lambda callable.
///
/// \ingroup X
constexpr auto Identity = [](int x) { return x; };

/// Container with hidden-type members.
///
/// \ingroup X
struct Holder {
  /// Formats inside Holder.
  static constexpr auto MemberFormat = internal_ns::Niebloid{};
  /// Non-static callable field.
  internal_ns::Niebloid callable_field;
  /// Non-callable hidden-type field.
  internal_ns::Tag tag_field;
};
""",
    )
    output = api_parser.generate_output(config)
    assert not output.get("errors")
    assert not output.get("warnings")
    by_name = {entity["name"]: entity for entity in output["entities"].values()}
    assert by_name["kTag"]["kind"] == "var"
    assert by_name["kTag"]["declaration"] == "constexpr auto __x0"
    assert by_name["kTag"]["initializer"] is None
    assert by_name["Format"]["kind"] == "function"
    assert by_name["Format"]["declaration"] == "constexpr auto __x0(T &&v)"
    assert by_name["Format"]["template_parameters"] == [
        {"declaration": "typename T", "name": "T", "kind": "type", "pack": False}
    ]
    assert by_name["Invoke"]["kind"] == "function"
    assert by_name["Invoke"]["declaration"] == "constexpr void __x0(void (*cb)() const)"
    assert by_name["GetPtr"]["kind"] == "function"
    assert by_name["GetPtr"]["declaration"] == "constexpr int *__x0()"
    assert by_name["Identity"]["kind"] == "var"
    assert by_name["Identity"]["declaration"] == "constexpr auto __x0"
    assert by_name["Identity"]["initializer"] is None
    assert by_name["MemberFormat"]["kind"] == "method"
    assert by_name["MemberFormat"]["declaration"] == "static constexpr auto __x0(T &&v)"
    assert by_name["callable_field"]["kind"] == "method"
    assert by_name["callable_field"]["declaration"] == "auto __x0(T &&v)"
    assert by_name["tag_field"]["kind"] == "var"
    assert by_name["tag_field"]["declaration"].strip() == "auto __x0"
    assert "Methods" in by_name["Holder"]["related_members"]
    assert "Data members" in by_name["Holder"]["related_members"]
    assert "Friend functions" not in by_name["Holder"]["related_members"]


def test_undocumented_parent_warning():
    config = api_parser.Config(
        input_path="a.cpp",
        input_content=rb"""
class UndocumentedParent {
 public:
  /// Documented member inside undocumented class.
  void Foo();

 private:
  /// Private helper inside undocumented class (should not warn).
  void PrivateHelper();
};

/// Documented outer class.
///
/// \ingroup X
class DocumentedOuter {
 private:
  struct PrivateNested {
    /// Comment inside private nested helper struct (should not warn).
    int count = 0;
  };
};
""",
    )
    output = api_parser.generate_output(config)
    assert not output.get("errors")
    warnings = output.get("warnings", [])
    assert len(warnings) == 1
    assert (
        "Undocumented parent UndocumentedParent for documented member Foo()"
        in warnings[0]["message"]
    )
