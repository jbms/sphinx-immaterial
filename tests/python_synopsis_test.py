import docutils.nodes


def test_python_class_synopsis(immaterial_make_app, snapshot):
    app = immaterial_make_app(
        files={
            "index.rst": """
.. py:class:: Bar

   Synopsis goes here.

   Rest of description goes here.

:py:obj:`Bar`
"""
        },
    )

    app.build()

    assert not app._warning.getvalue()

    doc = app.env.get_and_resolve_doctree("index", app.builder)

    node = list(doc.findall(condition=docutils.nodes.reference))[-1]

    snapshot.assert_match(node["reftitle"], "reftitle.txt")
