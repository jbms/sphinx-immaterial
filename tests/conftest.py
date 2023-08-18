import pathlib
from typing import Dict

import pytest
import sphinx

if sphinx.version_info < (7, 2):
    from sphinx.testing.path import path as SphinxPath
else:
    from pathlib import Path as SphinxPath  # type: ignore[assignment]


pytest_plugins = ("sphinx.testing.fixtures",)


@pytest.fixture
def immaterial_make_app(tmp_path: pathlib.Path, make_app):
    conf = """
extensions = [
    "sphinx_immaterial",
]
html_theme = "sphinx_immaterial"
"""

    def make(files: Dict[str, str], extra_conf: str = "", **kwargs):
        (tmp_path / "conf.py").write_text(conf + extra_conf, encoding="utf-8")
        for filename, content in files.items():
            (tmp_path / filename).write_text(content, encoding="utf-8")
        app = make_app(srcdir=SphinxPath(str(tmp_path)), **kwargs)
        app.pdb = True
        return app

    yield make
