import sphinx.addnodes


def test_nonodeid(immaterial_make_app):
    app = immaterial_make_app(
        files={
            "index.rst": """
.. py:class:: Bar

.. py:class:: Foo
   :nonodeid:
"""
        },
    )

    app.build()

    assert not app._warning.getvalue()

    doc = app.env.get_and_resolve_doctree("index", app.builder)

    nodes = list(doc.findall(condition=sphinx.addnodes.desc_signature))

    assert len(nodes) == 2

    assert nodes[0]["ids"] == ["Bar"]
    assert nodes[1]["ids"] == []


def test_invalid_signature(immaterial_make_app):
    app = immaterial_make_app(
        files={
            "index.rst": """
.. py:function:: bar(
"""
        },
    )

    app.build()

    assert not app._warning.getvalue()

    doc = app.env.get_and_resolve_doctree("index", app.builder)

    nodes = list(doc.findall(condition=sphinx.addnodes.desc_signature))

    assert len(nodes) == 1

    assert nodes[0]["ids"] == []
