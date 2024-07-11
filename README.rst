Sphinx-Immaterial Theme
=======================

|MIT License| |PyPI Package| |CI status| |codecov-badge|

This theme is an adaptation of the popular `mkdocs-material
<https://github.com/squidfunk/mkdocs-material/>`__ theme for the `Sphinx
<https://www.sphinx-doc.org/>`__ documentation tool.

This theme is regularly maintained to stay up to date with the upstream
`mkdocs-material <https://squidfunk.github.io/mkdocs-material/>`__ repository.
The HTML templates, JavaScript, and styles from the `mkdocs-material
<https://squidfunk.github.io/mkdocs-material/>`__ theme are incoroprated directly
with mostly minor modifications.

This theme is a fork of the `sphinx-material
<https://github.com/bashtage/sphinx-material>`__ theme, which proved the concept
of a Sphinx theme based on an earlier version of the `mkdocs-material
<https://squidfunk.github.io/mkdocs-material/>`__ theme, but has now
significantly diverged from the upstream `mkdocs-material
<https://squidfunk.github.io/mkdocs-material/>`__ repository.

See `this theme's own documentation
<https://jbms.github.io/sphinx-immaterial/>`__ for a demonstration.

WARNING: This theme is still in beta.  While it is already very usable, breaking
changes will still be made prior to the 1.0 release.

Installation
------------

Install via pip:

.. code-block:: bash

    $ pip install sphinx-immaterial

or if you have the code checked out locally:

.. code-block:: bash

    $ pip install -e .

Configuration
-------------

In your `conf.py` add `sphinx_immaterial` as an extension:

.. code-block:: python

    extensions = [
        ...,
        "sphinx_immaterial"
    ]

and add the following:

.. code-block:: python

    html_theme = 'sphinx_immaterial'

to set the theme.

Customizing the layout
----------------------

You can customize the theme by overriding Jinja template blocks. For example,
'layout.html' contains several blocks that can be overridden or extended.

Place a 'layout.html' file in your project's '/_templates' directory.

.. code-block:: bash

    mkdir source/_templates
    touch source/_templates/layout.html

Then, configure your 'conf.py':

.. code-block:: python

    templates_path = ['_templates']

Finally, edit your override file 'source/_templates/layout.html':

::

    {# Import the theme's layout. #}
    {% extends '!layout.html' %}

    {%- block extrahead %}
    {# Add custom things to the head HTML tag #}
    {# Call the parent block #}
    {{ super() }}
    {%- endblock %}

Differences from mkdocs-material
--------------------------------

This theme closely follows the upstream `mkdocs-material
<https://github.com/squidfunk/mkdocs-material/>`__ repository, but there are a
few differences, primarily due to differences between Sphinx and MkDocs:

- This theme adds styles for Sphinx object descriptions, commonly used for API
  documentation (e.g. class and function documentation).  This is a core element
  of Sphinx for which there is no corresponding feature in MkDocs.

- mkdocs-material uses `lunr.js <https://lunrjs.com/>`__ for searching, and has
  custom UI components for displaying search results in a drop-down menu as you
  type the search query.  This theme uses a separate search implementation based
  on the custom index format used by Sphinx, which fully integrates with the
  search UI provided by mkdocs-material.

.. |MIT License| image:: https://img.shields.io/badge/License-MIT-blue.svg
   :target: https://opensource.org/licenses/MIT-Clause

.. |PyPI Package| image:: https://img.shields.io/pypi/v/sphinx-immaterial
   :target: https://pypi.org/project/sphinx-immaterial

.. |CI status| image:: https://github.com/jbms/sphinx-immaterial/actions/workflows/build.yml/badge.svg
   :target: https://github.com/jbms/sphinx-immaterial/actions/workflows/build.yml

.. |codecov-badge| image:: https://codecov.io/gh/jbms/sphinx-immaterial/graph/badge.svg?token=IGK0B3WN42
   :alt: codecov
   :target: https://codecov.io/gh/jbms/sphinx-immaterial
