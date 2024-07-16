"""Test specific to https://github.com/jbms/sphinx-immaterial/issues/134"""

from typing import List
import pytest
from sphinx.testing.util import SphinxTestApp
from sphinx_immaterial_pybind11_issue_134 import Example  # type: ignore


@pytest.mark.parametrize(
    "args,expected", [([], False), ([True], True)], ids=["without arg", "with arg"]
)
def test_issue_134_example_pkg(args: List[bool], expected: bool):
    cls = Example(*args)
    assert cls.is_set_by_init is expected


def test_autoclass_members(immaterial_make_app):
    """Issue 134 is related to using ``:members:`` option of
    the ``autoclass`` directive."""
    app: SphinxTestApp = immaterial_make_app(
        files={
            "index.rst": "\n".join(
                [
                    "Some API",
                    "========",
                    ".. autoclass:: sphinx_immaterial_pybind11_issue_134.Example",
                    "    :members: is_set_by_init",
                    "    :special-members: __init__",  # tests overloads in pybind11 (for good measure)
                ]
            )
        },
        extra_conf='extensions.append("sphinx.ext.autodoc")\n',
    )
    app.build()
    assert not app._warning.getvalue()  # type: ignore[attr-defined]
    print(app._status.getvalue())  # type: ignore[attr-defined]
