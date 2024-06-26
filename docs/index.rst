:hero: A responsive Material Design theme for Sphinx sites.

===================
Material for Sphinx
===================

..
    .. image:: images/screenshot.png
        :alt: Material for Sphinx Screenshots

This theme is an adaptation of the popular `mkdocs-material
<https://github.com/squidfunk/mkdocs-material/>`__ theme for the `Sphinx
<https://www.sphinx-doc.org/>`__ documentation tool.

This theme is regularly maintained to stay up to date with the upstream
`mkdocs-material <https://squidfunk.github.io/mkdocs-material/>`__ repository.
The HTML templates, JavaScript, and styles from the `mkdocs-material
<https://squidfunk.github.io/mkdocs-material/>`__ theme are incorporated directly
with mostly minor modifications.

Independent of the upstream mkdocs-material theme, this theme integrates with
and significantly extends Sphinx's API documentation functionality.

This theme is a fork of the `sphinx-material
<https://github.com/bashtage/sphinx-material>`__ theme, which proved the concept
of a Sphinx theme based on an earlier version of the `mkdocs-material
<https://squidfunk.github.io/mkdocs-material/>`__ theme, but has now
significantly diverged from the upstream `mkdocs-material
<https://squidfunk.github.io/mkdocs-material/>`__ repository.

Getting Started
---------------

Installation
~~~~~~~~~~~~

From the PyPI
^^^^^^^^^^^^^

.. code-block:: bash

   pip install sphinx-immaterial

From git source
^^^^^^^^^^^^^^^

.. code-block:: bash

   pip install git+https://github.com/jbms/sphinx-immaterial.git

.. admonition:: Prerequisites

    Building the theme from source requires node.js v14 or newer installed.
    Please be aware that readthedocs.org uses a docker image that might have
    an outdated version of node.js installed. Installing node.js from a Unix package
    manager may not provide version 14 or newer.

    Installing from a distributed wheel (such as from pypi.org) does not require
    node.js installed.


Sphinx configuration
~~~~~~~~~~~~~~~~~~~~

Update your ``conf.py`` with the required changes:

.. code-block:: python

    extensions = ["sphinx_immaterial"]
    # ...
    html_theme = "sphinx_immaterial"


There are a lot more ways to customize this theme. See :ref:`Customization`
or ``theme.conf`` for more details.

.. example:: Settings used in this documentation
    :collapsible:

    .. literalinclude:: ./conf.py
        :start-after: # -- HTML theme specific settings
        :end-before: # end html_theme_options

.. important::
   :title: Migrating from another theme
   :collapsible:

   Be advised to clean prior builds before the first build with a new theme.


.. toctree::
    :hidden:

    customization
    admonitions
    content_tabs
    task_lists
    keys

.. toctree::
    :caption: Code Blocks
    :hidden:

    code_syntax_highlighting
    code_annotations

.. toctree::
    :caption: API documentation customization
    :hidden:

    apidoc/index
    apidoc/format_signatures
    apidoc/python/index
    apidoc/python/apigen
    apidoc/cpp/index
    apidoc/cpp/external_cpp_references
    apidoc/cpp/cppreference
    apidoc/cpp/apigen
    apidoc/json/domain

.. toctree::
    :hidden:

    inline_icons

.. toctree::
    :caption: Diagrams/graphs
    :hidden:

    graphviz
    mermaid_diagrams

.. toctree::
    :caption: Examples and Uses
    :hidden:

    demo_api
    python_apigen_demo
    cpp_apigen_demo
    specimen
    rst_basics
    rst-cheatsheet/rst-cheatsheet
    additional_samples
    myst_typography

.. toctree::
    :hidden:

    theme_result
