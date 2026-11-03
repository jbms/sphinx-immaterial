"""Tests cpp/apigen."""

import pathlib


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


def test_using_and_hide_types(immaterial_make_app):
    app = immaterial_make_app(
        extra_conf="""
extensions.append("sphinx_immaterial.apidoc.cpp.apigen")
""",
        confoverrides=dict(
            nitpicky=True,
            cpp_apigen_case_insensitive_filesystem=False,
            cpp_apigen_configs=[
                dict(
                    document_prefix="cpp_apigen_generated/",
                    api_parser_config=dict(
                        hide_types=[r"\binternal_ns::"],
                        input_content=r"""
namespace internal_ns {
struct Tag {};
struct Niebloid {
  template <typename T>
  auto operator()(T&& v) const {
    return 0;
  }
};
}

/// Base class.
///
/// \ingroup Api
class Base {
 public:
  /// Constructs Base.
  explicit Base(int x);
  Base(int x, int y);
  /// Waits for completion.
  void Wait() const;
  void Wait(int timeout) const;
};

/// Templated base class.
///
/// \ingroup Api
template <typename T>
class TemplatedBase {
 public:
  /// Checks readiness.
  bool Ready() const;
};

/// Derived class.
///
/// \ingroup Api
template <typename T>
class Derived : public Base, public TemplatedBase<T> {
 public:
  /// Inherits Base constructors.
  using Base::Base;
  /// Waits for completion.
  using Base::Wait;
  /// Checks readiness.
  using TemplatedBase<T>::Ready;
};

/// Tag constant.
///
/// \ingroup Api
/**/ constexpr auto kTag = internal_ns::Tag{};

/// Formats values.
///
/// \ingroup Api
constexpr auto Format = internal_ns::Niebloid{};

/// Holder struct.
///
/// \ingroup Api
struct Holder {
  /// Formats inside Holder.
  static constexpr auto MemberFormat = internal_ns::Niebloid{};
};
""",
                        compiler_flags=["-std=c++17", "-x", "c++"],
                        verbose=True,
                    ),
                ),
            ],
        ),
        files={
            "index.rst": """
.. cpp-apigen-group:: Api

"""
        },
    )

    app.build()

    assert not app._warning.getvalue()
    generated_dir = pathlib.Path(app.outdir) / "cpp_apigen_generated"
    for page in (
        "Derived.Derived.html",
        "Derived.Wait.html",
        "Derived.Ready.html",
        "Format.html",
        "Holder.MemberFormat.html",
        "kTag.html",
    ):
        assert (generated_dir / page).is_file(), f"Missing generated page {page}"
    wait_html = (generated_dir / "Derived.Wait.html").read_text(encoding="utf-8")
    assert "timeout" in wait_html
