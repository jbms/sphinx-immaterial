import pathlib

import pytest

from sphinx_immaterial.apidoc.python.apigen import _get_api_data

from sphinx.testing.path import path as SphinxPath

pytest_plugins = ("sphinx.testing.fixtures",)


@pytest.fixture
def apigen_make_app(tmp_path: pathlib.Path, make_app):

    conf = """
extensions = [
    "sphinx_immaterial",
    "sphinx_immaterial.apidoc.python.apigen",
]
html_theme = "sphinx_immaterial"
"""

    def make(extra_conf: str = "", **kwargs):
        (tmp_path / "conf.py").write_text(conf + extra_conf, encoding="utf-8")
        (tmp_path / "index.rst").write_text("", encoding="utf-8")
        return make_app(srcdir=SphinxPath(str(tmp_path)), **kwargs)

    yield make


@pytest.mark.parametrize(
    "order_tiebreaker,expected_members",
    [("alphabetical", ["a", "b"]), ("definition_order", ["b", "a"])],
)
def test_alphabetical(apigen_make_app, order_tiebreaker, expected_members):

    app = apigen_make_app(
        confoverrides=dict(
            python_apigen_order_tiebreaker=order_tiebreaker,
            python_apigen_default_groups=[],
            python_apigen_modules={
                "python_apigen_test_modules.alphabetical": "api/",
            },
        ),
    )

    print(app._status.getvalue())
    print(app._warning.getvalue())

    data = _get_api_data(app.env)
    members = [x.name for x in data.top_level_groups["public-members"]]
    assert members == expected_members


def test_classmethod(apigen_make_app):
    testmod = "python_apigen_test_modules.classmethod"
    app = apigen_make_app(
        confoverrides=dict(
            python_apigen_default_groups=[
                ("method:.*", "Methods"),
                ("classmethod:.*", "Class methods"),
                ("staticmethod:.*", "Static methods"),
            ],
            python_apigen_modules={
                testmod: "api/",
            },
        ),
    )

    print(app._status.getvalue())
    print(app._warning.getvalue())

    data = _get_api_data(app.env)

    # FIXME: Currently all methods are assigned to the 'Methods" group because
    # the `classmethod` and `staticmethod` object types aren't actually used by
    # Sphinx.
    #
    # https://github.com/sphinx-doc/sphinx/issues/3743
    assert data.entities[f"{testmod}.Foo.my_method"].group_name == "Methods"
    assert data.entities[f"{testmod}.Foo.my_staticmethod"].group_name == "Methods"
    assert data.entities[f"{testmod}.Foo.my_classmethod"].group_name == "Methods"


def test_issue_147(apigen_make_app):
    testmod = "python_apigen_test_modules.issue147"
    app = apigen_make_app(
        confoverrides=dict(
            python_apigen_modules={
                testmod: "api/",
            },
        ),
    )
    print(app._status.getvalue())
    print(app._warning.getvalue())

    data = _get_api_data(app.env)

    for entity in data.entities.values():
        assert entity.options["module"] == testmod


def test_pybind11_property(apigen_make_app):
    testmod = "sphinx_immaterial_pybind11_issue_134"
    app = apigen_make_app(
        confoverrides=dict(
            python_apigen_modules={
                testmod: "api/",
            },
        ),
    )
    print(app._status.getvalue())
    print(app._warning.getvalue())

    data = _get_api_data(app.env)

    options = data.entities[f"{testmod}.Example.is_set_by_init"].options
    assert options["type"] == "bool"

    options = data.entities[f"{testmod}.Example.no_signature"].options
    assert "type" not in options


def test_pure_python_property(apigen_make_app):
    testmod = "python_apigen_test_modules.property"
    app = apigen_make_app(
        confoverrides=dict(
            python_apigen_modules={
                testmod: "api/",
            },
        ),
    )

    print(app._status.getvalue())
    print(app._warning.getvalue())

    data = _get_api_data(app.env)

    options = data.entities[f"{testmod}.Example.foo"].options
    assert options["type"] == "int"
