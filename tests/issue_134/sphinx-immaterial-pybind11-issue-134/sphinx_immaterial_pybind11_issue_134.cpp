#include <pybind11/pybind11.h>

struct Example
{
    const bool is_set_by_init;
    Example() : is_set_by_init(false) {}
    Example(const bool value) : is_set_by_init(value) {}
};

namespace py = pybind11;

PYBIND11_MODULE(sphinx_immaterial_pybind11_issue_134, m)
{
    py::class_<Example>(m, "Example")
        .def(py::init<>(), R"docstr(
            The default constructor takes no args.
        )docstr")
        .def(py::init<const bool>(), R"docstr(
            The overloaded constructor takes 1 ``bool`` arg.
        )docstr",
             py::arg("value"))
        .def_readonly("is_set_by_init", &Example::is_set_by_init, R"docstr(
            This read-only ``bool`` attribute is set by the constructor.
        )docstr");
}
