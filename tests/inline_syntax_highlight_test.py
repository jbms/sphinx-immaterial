"""Tests related to theme's syntax highlighting
(default-literal inline and code-block)."""

from sphinx.testing.util import SphinxTestApp
import pytest

rst_prologue = """.. role:: python(code)
   :language: python
   :class: highlight
"""
default_literal_rst = """
The Test
========

Normal literal role: ``1 + 2``

.. default-literal-role:: python

Python literal role: ``1 + 2``

.. default-literal-role::

Normal literal role again: ``1 + 2``

"""

highlight_push_pop = """
The Test
========

.. highlight-push::

.. highlight:: json

The following literal block will be highlighted as JSON::

   {"a": 10, "b": null, "c": 10}

.. highlight-push::

.. highlight:: python

The following block will be highlighted as Python::

   def foo(x: int) -> None: ...

.. highlight-pop::

The following block will be highlighted as JSON::

   [1, 2, true, false]
"""


@pytest.mark.parametrize(
    "doc",
    [
        "\n".join([rst_prologue, default_literal_rst]),
        pytest.param(default_literal_rst, marks=pytest.mark.xfail),
        highlight_push_pop,
    ],
    ids=["default_literal", "default_literal_warning", "highlight_push_pop"],
)
def test_syntax_highlighting(doc: str, immaterial_make_app):
    app: SphinxTestApp = immaterial_make_app(
        extra_conf="extensions.append('sphinx_immaterial.inlinesyntaxhighlight')",
        files={"index.rst": doc},
    )

    app.build()
    assert not app._warning.getvalue()  # type: ignore[attr-defined]
