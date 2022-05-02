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
<https://squidfunk.github.io/mkdocs-material/>`__ theme are incoroprated directly
with mostly minor modifications.

This theme is a fork of the `sphinx-material
<https://github.com/bashtage/sphinx-material>`__ theme, which proved the concept
of a Sphinx theme based on an earlier version of the `mkdocs-material
<https://squidfunk.github.io/mkdocs-material/>`__ theme, but has now
significantly diverged from the upstream `mkdocs-material
<https://squidfunk.github.io/mkdocs-material/>`__ repository.

Getting Started
---------------

.. admonition:: Prerequisites

    Building the theme from source requires node.js v14 or newer installed.
    Please be aware that readthedocs.org uses a docker image that might have
    an outdated verson of node.js installed. Installing node.js from a Unix package
    manager may not provide version 14 or newer.

    Installing from a distributed wheel (such as from pypi.org) does not require
    node.js installed.

Install from git source

.. code-block:: bash

   pip install git+https://github.com/jbms/sphinx-immaterial.git

Update your ``conf.py`` with the required changes:

.. code-block:: python

    extension = ["sphinx_immaterial"]
    # ...
    html_theme = "sphinx_immaterial"


There are a lot more ways to customize this theme. See :ref:`Customization`
or ``theme.conf`` for more details.

.. details:: Settings used in this documentation
    :class: example

    .. literalinclude:: ./conf.py
        :start-after: # -- HTML theme specific settings
        :end-before: # end html_theme_options


.. toctree::
    :hidden:

    customization
    admonitions
    content_tabs
    mermaid_diagrams
    task_lists
    keys

.. toctree::
    :caption: API documentation customization
    :hidden:

    api
    format_signatures
    python
    cpp
    external_cpp_references
    cppreference
    json

.. toctree::
    :caption: Examples and Uses
    :hidden:

    demo_api
    specimen
    rst_basics
    rst-cheatsheet/rst-cheatsheet
    additional_samples
