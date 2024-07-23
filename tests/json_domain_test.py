from pathlib import Path
import re

import docutils.utils
import pytest
import sphinx.addnodes


@pytest.mark.parametrize(
    "doc,schema",
    [
        (
            "\n".join(
                [
                    ".. json:schema:: Pet",
                    ".. json:schema:: Dog",
                    ".. json:schema:: Cat",
                ]
            ),
            "docs/apidoc/json/inheritance_schema.yml",
        ),
        (
            "\n".join(
                [
                    ".. json:schema:: IndexTransform",
                    ".. json:schema:: OutputIndexMap",
                    ".. json:schema:: IndexInterval",
                ]
            ),
            "docs/apidoc/json/index_transform_schema.yml",
        ),
    ],
    ids=["inheritance", "IndexTransform"],
)
def test_doc_examples(doc: str, schema: str, tmp_path: Path, immaterial_make_app):
    schema_path = Path(__file__).parent.parent / schema
    app = immaterial_make_app(
        extra_conf='''
extensions.append("sphinx_immaterial.apidoc.json.domain")
json_schemas = ["schema.yml"]
json_schema_validate = True
rst_prolog = """
.. role:: json(code)
    :language: json
    :class: highlight
"""
''',
        files={
            "index.rst": doc,
            "schema.yml": schema_path.read_text(encoding="utf-8"),
        },
    )
    app.build()
    assert not app._warning.getvalue()


def test_xref_source_info(immaterial_make_app):
    app = immaterial_make_app(
        extra_conf="\n".join(
            [
                'extensions.append("sphinx_immaterial.apidoc.json.domain")',
                'json_schemas = ["schema.yml"]',
            ]
        ),
        files={
            "index.rst": """
.. json:schema:: MySchema
""",
            "schema.yml": """$schema: http://json-schema.org/draft-07/schema#
$id: MySchema
type: object
properties:
  age:
    type: number
    title: Age of the pet in years.
    description: |
      This is :ref:`some-reference`.
    minimum: 0
""",
        },
    )
    app.builder.read()
    doc = app.env.get_doctree("index")
    xrefs = list(doc.findall(condition=sphinx.addnodes.pending_xref))
    assert len(xrefs) == 1
    source, line = docutils.utils.get_source_line(xrefs[0])
    assert source.endswith("schema.yml")
    assert line == 9


def test_missing_ref(immaterial_make_app):
    app = immaterial_make_app(
        extra_conf="\n".join(
            [
                'extensions.append("sphinx_immaterial.apidoc.json.domain")',
                'json_schemas = ["schema.yml"]',
            ]
        ),
        files={
            "index.rst": """
.. json:schema:: MySchema
""",
            "schema.yml": """$schema: http://json-schema.org/draft-07/schema#
$id: MySchema
allOf:
- $ref: OtherSchema
- type: object
  properties:
    path:
      type: string
""",
        },
    )
    app.build()
    assert re.search(
        r"schema\.yml:4: ERROR: Reference to undefined JSON schema: 'OtherSchema'",
        app._warning.getvalue(),
    )


def test_minitems_without_maxitems(immaterial_make_app):
    app = immaterial_make_app(
        extra_conf="\n".join(
            [
                'extensions.append("sphinx_immaterial.apidoc.json.domain")',
                'json_schemas = ["schema.yml"]',
            ]
        ),
        files={
            "index.rst": """
.. json:schema:: MySchema
""",
            "schema.yml": """$schema: http://json-schema.org/draft-07/schema#
$id: MySchema
type: array
maxItems: 5
""",
        },
    )
    app.build()
    assert not app._warning.getvalue()
