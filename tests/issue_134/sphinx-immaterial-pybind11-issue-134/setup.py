# type: ignore
from pybind11.setup_helpers import Pybind11Extension, build_ext
from setuptools import setup

ext_modules = [
    Pybind11Extension(
        "sphinx_immaterial_pybind11_issue_134",
        ["sphinx_immaterial_pybind11_issue_134.cpp"],
    ),
]

setup(
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
)
