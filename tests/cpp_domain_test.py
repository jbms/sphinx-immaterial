"""Tests C++ domain functionality added by this theme."""

import json

import docutils.nodes
import pytest

pytest_plugins = ("sphinx.testing.fixtures",)


def snapshot_references(app, snapshot):
    doc = app.env.get_and_resolve_doctree("index", app.builder)

    nodes = list(doc.findall(condition=docutils.nodes.reference))

    node_data = [
        {
            "text": node.astext(),
            **{
                attr: node.get(attr)
                for attr in ["refid", "refurl", "reftitle"]
                if attr in node
            },
        }
        for node in nodes
    ]

    snapshot.assert_match("\n".join(json.dumps(n) for n in node_data), "references.txt")


@pytest.mark.parametrize("node_id", [None, "", "abc"])
def test_parameter_objects(immaterial_make_app, snapshot, node_id: str):
    """Tests that parameter objects take into account the `node-id` option."""

    attrs = []
    if node_id is not None:
        attrs.append(f":node-id: {node_id}")
    attrs_text = "\n".join(attrs)

    app = immaterial_make_app(
        files={
            "index.rst": f"""

.. cpp:function:: void foo(int bar, int baz, int undocumented);
   {attrs_text}

   Test function.

   :param bar: Bar parameter.
   :param baz: Baz parameter.
""",
        },
    )

    app.build()

    snapshot_references(app, snapshot)


def test_template_parameter_objects(immaterial_make_app, snapshot):
    """Tests that xrefs to template parameters include template parameter kind
    in tooltip text."""
    app = immaterial_make_app(
        files={
            "index.rst": """

.. cpp:function:: template <typename T, int N, template<typename> class U>\
                  void foo();

   Test function.

   :tparam T: T parameter.
   :tparam N: N parameter.
""",
        },
    )

    app.build()

    snapshot_references(app, snapshot)


def test_macro_parameter_objects(immaterial_make_app, snapshot):
    """Tests that macro parameters work correctly."""
    app = immaterial_make_app(
        files={
            "index.rst": """

.. c:macro:: FOO(a, b, c)

   Test macro.

   :param a: A parameter.
   :param b: B parameter.
""",
        },
    )

    app.build()

    snapshot_references(app, snapshot)
