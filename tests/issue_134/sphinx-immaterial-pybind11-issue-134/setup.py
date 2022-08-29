#! python
# type: ignore
from setuptools import setup
from pybind11.setup_helpers import Pybind11Extension, build_ext

ext_modules = [
    Pybind11Extension(
        "sphinx_immaterial_pybind11_issue_134",
        ["sphinx_immaterial_pybind11_issue_134.cpp"],
    ),
]

setup(
    name="sphinx-immaterial-pybind11-issue-134",
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
)
