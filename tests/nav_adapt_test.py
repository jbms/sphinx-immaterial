import json

import pytest
import yaml
import sphinx.application

import sphinx_immaterial.nav_adapt


def _default_json_encode(obj):
    return obj.__dict__


def get_nav_info(app: sphinx.application.Sphinx, pagename: str) -> str:
    (
        global_toc,
        local_toc,
        integrated_local_toc,
    ) = sphinx_immaterial.nav_adapt._get_mkdocs_tocs(
        app, pagename, duplicate_local_toc=False, toc_integrate=False
    )
    obj = {
        "global_toc": global_toc,
        "local_toc": local_toc,
        "integrated_local_toc": integrated_local_toc,
    }
    return yaml.safe_dump(json.loads(json.dumps(obj, default=_default_json_encode)))


@pytest.mark.parametrize("includeonly", [True, False], ids=lambda x: f"includeonly_{x}")
@pytest.mark.parametrize("collapse", [True, False], ids=lambda x: f"collapse_{x}")
def test_nav(immaterial_make_app, snapshot, collapse, includeonly):
    # Note: `includeonly` tests selectively including sections (due to objects)
    # but does not test selectively including `toctree` directives themselves,
    # as that is not supported by Sphinx:
    # https://github.com/sphinx-doc/sphinx/issues/9819

    app = immaterial_make_app(
        confoverrides=dict(html_theme_options=dict(globaltoc_collapse=collapse)),
        tags=["xyz"] if includeonly else [],
        files={
            "index.rst": """
Overall title
=============

Getting started
---------------

.. only:: xyz

   .. py:class:: Foo

Another section
---------------

.. toctree::
   :hidden:

   a

.. toctree::
   :hidden:
   :caption: TOC caption

   c
""",
            "a.rst": """
A page
======

Section 1
---------

.. toctree::
   :hidden:

   b

Section 2
---------

.. only:: xyz

   .. py:class:: Bar

""",
            "b.rst": """
B page
======
""",
            "c.rst": """
C page
======
""",
        },
    )
    app.build()

    assert not app._warning.getvalue()
    for pagename in ["index", "a", "b", "c"]:
        snapshot.assert_match(get_nav_info(app, pagename), f"{pagename}.yml")


@pytest.mark.parametrize("include", [True, False])
def test_include_rubrics_in_toc(immaterial_make_app, snapshot, include):
    app = immaterial_make_app(
        extra_conf=f"""
object_description_options=[('py:class', dict(include_rubrics_in_toc={include}))]
""",
        files={
            "index.rst": """
Overall title
=============

.. py:class:: Foo

   Some text.

   .. rubric:: Examples

""",
        },
    )
    app.build()

    assert not app._warning.getvalue()
    print(app._status.getvalue())

    for pagename in ["index"]:
        snapshot.assert_match(get_nav_info(app, pagename), f"{pagename}.yml")
