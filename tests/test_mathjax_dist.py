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


@pytest.mark.parametrize("parallel", [0, 2], ids=["serial", "parallel"])
@pytest.mark.parametrize(
    "has_equations", [True, False], ids=["with-equations", "no-equations"]
)
def test_has_mathjax_dist(immaterial_make_app, has_equations: bool, parallel: int):
    """tests if mathjax dist is included in build output"""

    # Use enough documents for sphinx to read and write them in subprocesses
    # when building in parallel.
    pages = [f"page{i}" for i in range(6)]
    files = {"index.rst": INDEX_RST + "\n.. toctree::\n\n   " + "\n   ".join(pages)}
    for page in pages:
        files[f"{page}.rst"] = f"{page}\n{'=' * len(page)}\n"
    if has_equations:
        files[f"{pages[-1]}.rst"] += MATH_SYNTAX

    app: SphinxTestApp = immaterial_make_app(
        extra_conf="extensions.append('sphinx.ext.mathjax')",
        files=files,
        parallel=parallel,
    )

    app.build()
    assert not app._warning.getvalue()  # type: ignore[attr-defined]
    out_dir = Path(app.outdir) / "_static" / "mathjax"
    assert out_dir.exists() == has_equations
