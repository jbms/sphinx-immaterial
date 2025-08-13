"""Tests related to theme's theme_result extension."""

from pathlib import Path

import pytest
from sphinx.testing.util import SphinxTestApp

INDEX_RST = """
The Test
========

Some text.
"""

MATH_SYNTAX = """
Since Pythagoras, we know that :math:`a^2 + b^2 = c^2`.

.. math::

   (a + b)^2 = a^2 + 2ab + b^2

   (a - b)^2 = a^2 - 2ab + b^2
"""


@pytest.mark.parametrize(
    "has_equations", [True, False], ids=["with-equations", "no-equations"]
)
def test_has_mathjax_dist(immaterial_make_app, has_equations: bool):
    """tests if mathjax dist is included in build output"""

    index_rst = INDEX_RST
    if has_equations:
        index_rst += MATH_SYNTAX

    app: SphinxTestApp = immaterial_make_app(
        extra_conf="extensions.append('sphinx.ext.mathjax')",
        files={"index.rst": index_rst},
    )

    app.build()
    assert not app._warning.getvalue()  # type: ignore[attr-defined]
    out_dir = Path(app.outdir) / "_static" / "mathjax"
    assert out_dir.exists() == has_equations
