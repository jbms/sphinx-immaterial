"""Tests related to theme's kbd_keys extension."""

import pytest
from sphinx.testing.util import SphinxTestApp

index_rst = """
The Test
========

:keys:`ctrl+alt+tab`

:keys:`caps-lock`, :keys:`left-cmd+shift+a`, :keys:`backspace`

:keys:`my-special-key+My Special Key`
"""


@pytest.mark.parametrize("builder", ["html", "latex"])
def test_keys_role(builder: str, immaterial_make_app):
    app: SphinxTestApp = immaterial_make_app(
        extra_conf="\n".join(
            [
                "extensions.append('sphinx_immaterial.kbd_keys')",
                'keys_map = {"my-special-key": "Awesome Key"}',
            ]
        ),
        files={"index.rst": index_rst},
        buildername=builder,
    )

    app.build()
    assert not app._warning.getvalue()  # type: ignore[attr-defined]
