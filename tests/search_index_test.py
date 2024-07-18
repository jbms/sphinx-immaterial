import os
import pathlib

import sphinx.search


def test_object_anchor(immaterial_make_app):
    app = immaterial_make_app(
        files={
            "index.rst": """
Overall title
=============

.. py:class:: Foo
""",
        },
    )
    app.build()

    assert not app._warning.getvalue()
    search_index_js = pathlib.Path(
        os.path.join(app.outdir, "searchindex.js")
    ).read_text("utf-8")
    search_index = sphinx.search.js_index.loads(search_index_js)

    assert search_index["objects"] == {"": [[0, 0, 1, 0, "Foo", ""]]}
