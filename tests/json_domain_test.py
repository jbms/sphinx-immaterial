import re

import docutils.utils
import sphinx.addnodes


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
