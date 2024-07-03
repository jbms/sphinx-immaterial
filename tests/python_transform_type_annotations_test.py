import pathlib

import pytest

import docutils.nodes
import sphinx
import sphinx.application
import sphinx.domains.python

if sphinx.version_info < (7, 2):
    from sphinx.testing.path import path as SphinxPath
else:
    from pathlib import Path as SphinxPath  # type: ignore[assignment]

pytest_plugins = ("sphinx.testing.fixtures",)


@pytest.fixture
def theme_make_app(tmp_path: pathlib.Path, make_app):
    conf = """
extensions = [
    "sphinx_immaterial",
]
html_theme = "sphinx_immaterial"
"""

    def make(extra_conf: str = "", **kwargs):
        (tmp_path / "conf.py").write_text(conf + extra_conf, encoding="utf-8")
        (tmp_path / "index.rst").write_text("", encoding="utf-8")
        return make_app(srcdir=SphinxPath(str(tmp_path)), **kwargs)

    yield make


def get_parsed_annotation_as_text(
    annotation: str, app: sphinx.application.Sphinx
) -> str:
    if sphinx.version_info >= (7, 3):
        assert (
            sphinx.domains.python._annotations._parse_annotation  # type: ignore[attr-defined]
            is sphinx.domains.python._parse_annotation
        )

        assert (
            sphinx.domains.python._object._parse_annotation  # type: ignore[attr-defined]
            is sphinx.domains.python._parse_annotation
        )

        assert (
            sphinx.domains.python._annotations.type_to_xref  # type: ignore[attr-defined]
            is sphinx.domains.python.type_to_xref
        )

    parsed_annotations = sphinx.domains.python._parse_annotation(annotation, app.env)
    parent = docutils.nodes.TextElement("", "")
    parent.extend(parsed_annotations)
    return parent.astext()


def test_transform_type_annotations_pep604(theme_make_app):
    app = theme_make_app(
        confoverrides=dict(),
    )

    for annotation, expected_text in [
        ("Union[int, float]", "int | float"),
        ("Literal[1, 2, None]", "1 | 2 | None"),
    ]:
        assert get_parsed_annotation_as_text(annotation, app) == expected_text


def test_python_module_names_to_strip_from_xrefs(theme_make_app):
    app = theme_make_app(
        confoverrides=dict(
            python_module_names_to_strip_from_xrefs=["tensorstore", "collections.abc"]
        ),
    )

    for annotation, expected_text in [
        ("tensorstore.Dim", "Dim"),
        ("collections.abc.Sequence", "Sequence"),
        ("collections.abc.def.Sequence", "def.Sequence"),
    ]:
        assert get_parsed_annotation_as_text(annotation, app) == expected_text
