:hero: A responsive Material Design theme for Sphinx sites.

===================
Material for Sphinx
===================

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

See the `TensorStore documentation <https://google.github.io/tensorstore/>`__
for a demonstration of this theme.

Getting Started
---------------
Install from git

.. code-block:: bash

   pip install git+https://github.com/jbms/sphinx-immaterial.git

Update your ``conf.py`` with the required changes:

.. code-block:: python

    html_theme = 'sphinx_immaterial'


There are a lot more ways to customize this theme. See :ref:`Customization`
or ``theme.conf`` for more details.

.. code-block:: python

    html_theme = 'sphinx_immaterial'

    # Material theme options (see theme.conf for more information)
    html_theme_options = {

        # Set the name of the project to appear in the navigation.
        'nav_title': 'Project Name',

        # Set you GA account ID to enable tracking
        'google_analytics_account': 'UA-XXXXX',

        # Specify a base_url used to generate sitemap.xml. If not
        # specified, then no sitemap will be built.
        'base_url': 'https://project.github.io/project',

        # Set the color and the accent color
        'color_primary': 'blue',
        'color_accent': 'light-blue',

        # Set the repo location to get a badge with stats
        'repo_url': 'https://github.com/project/project/',
        'repo_name': 'Project',

        # Visible levels of the global TOC; -1 means unlimited
        'globaltoc_depth': 3,
        # If False, expand all TOC entries
        'globaltoc_collapse': False,
        # If True, show hidden TOC entries
        'globaltoc_includehidden': False,
    }

.. toctree::
    :caption: Basic Use
    :maxdepth: 1

    customization
    specimen
    additional_samples


.. toctree::
    :caption: Other Examples and Uses
    :maxdepth: 1

    pymethod
    numpydoc
    rst-cheatsheet/rst-cheatsheet
    basics
