from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from typing import Callable

    from sphinx.testing.util import SphinxTestApp

index_rst = """
The Test
========

.. toctree::
    page
"""

page_rst = """
Page
====
"""


@pytest.mark.parametrize("builder", ["json", "pickle"])
def test_serializable_build(
    builder: str, immaterial_make_app: Callable[..., SphinxTestApp]
):
    app: SphinxTestApp = immaterial_make_app(
        files={"index.rst": index_rst, "page.rst": page_rst},
        buildername=builder,
    )

    app.build()
    assert not app._warning.getvalue()  # type: ignore[attr-defined]
