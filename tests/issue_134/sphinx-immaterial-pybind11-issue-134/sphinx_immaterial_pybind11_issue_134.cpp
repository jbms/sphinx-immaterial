#include <pybind11/pybind11.h>

struct Example {
  const bool is_set_by_init;
  Example() : is_set_by_init(false) {}
  Example(const bool value) : is_set_by_init(value) {}
};

namespace py = pybind11;

PYBIND11_MODULE(sphinx_immaterial_pybind11_issue_134, m) {
  py::class_<Example> cls(m, "Example");

  {
    py::options options;
    options.disable_function_signatures();

    cls.def(py::init<>(), R"docstr(
                __init__()
                __init__(value: bool)

                The default constructor takes no args.
            )docstr")
        .def(py::init<const bool>(), R"docstr(
                The overloaded constructor takes 1 ``bool`` arg.
            )docstr",
             py::arg("value"));

    cls.def_property_readonly("no_signature",
                              [](const Example& self) -> int { return 42; });
  }

  cls.def(
      "foo", [](Example& self, int x) { return 1; }, R"docstr(
Int overload.

Overload:
  int
)docstr");

  cls.def(
      "foo", [](Example& self, bool x) { return 1; }, R"docstr(
Bool overload.

Overload:
  bool
)docstr");

  cls.attr("bar") = cls.attr("foo");

  cls.def_readonly("is_set_by_init", &Example::is_set_by_init, R"docstr(
            This read-only ``bool`` attribute is set by the constructor.
        )docstr");
}
