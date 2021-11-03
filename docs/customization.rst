:hero: Configuration options to personalize your site.

.. embedded material icons used for inline demonstration
.. role:: inline-icon
.. role:: eye
.. role:: eye-outline
.. role:: lightbulb
.. role:: lightbulb-outline
.. role:: sunny
.. role:: night
.. role:: toggle-off
.. role:: toggle-on
.. role:: fa-git
.. role:: fa-git-alt
.. role:: fa-git-square
.. role:: fa-github
.. role:: fa-github-alt
.. role:: fa-github-square
.. role:: fa-gitlab
.. role:: fa-gitkraken
.. role:: fa-bitbucket

.. |eye| image:: _static/images/blank.png
    :class: inline-icon eye
.. |eye-outline| image:: _static/images/blank.png
    :class: inline-icon eye-outline
.. |lightbulb| image:: _static/images/blank.png
    :class: inline-icon lightbulb
.. |lightbulb-outline| image:: _static/images/blank.png
    :class: inline-icon lightbulb-outline
.. |sunny| image:: _static/images/blank.png
    :class: inline-icon sunny
.. |night| image:: _static/images/blank.png
    :class: inline-icon night
.. |toggle-off| image:: _static/images/blank.png
    :class: inline-icon toggle-off
.. |toggle-on| image:: _static/images/blank.png
    :class: inline-icon toggle-on
.. |fa-git| image:: _static/images/blank.png
    :class: inline-icon fa-git
.. |fa-git-alt| image:: _static/images/blank.png
    :class: inline-icon fa-git-alt
.. |fa-git-square| image:: _static/images/blank.png
    :class: inline-icon fa-git-square
.. |fa-github| image:: _static/images/blank.png
    :class: inline-icon fa-github
.. |fa-github-alt| image:: _static/images/blank.png
    :class: inline-icon fa-github-alt
.. |fa-github-square| image:: _static/images/blank.png
    :class: inline-icon fa-github-square
.. |fa-gitlab| image:: _static/images/blank.png
    :class: inline-icon fa-gitlab
.. |fa-gitkraken| image:: _static/images/blank.png
    :class: inline-icon fa-gitkraken
.. |fa-bitbucket| image:: _static/images/blank.png
    :class: inline-icon fa-bitbucket

.. custom roles used to add a class to individual html elements
.. role:: red
.. role:: pink
.. role:: purple
.. role:: deep-purple
.. role:: indigo
.. role:: blue
.. role:: light-blue
.. role:: cyan
.. role:: teal
.. role:: green
.. role:: light-green
.. role:: lime
.. role:: yellow
.. role:: amber
.. role:: orange
.. role:: deep-orange
.. role:: brown
.. role:: grey
.. role:: blue-grey
.. role:: white
.. role:: black
.. role:: accent-red
.. role:: accent-pink
.. role:: accent-purple
.. role:: accent-deep-purple
.. role:: accent-indigo
.. role:: accent-blue
.. role:: accent-light-blue
.. role:: accent-cyan
.. role:: accent-teal
.. role:: accent-green
.. role:: accent-light-green
.. role:: accent-lime
.. role:: accent-yellow
.. role:: accent-amber
.. role:: accent-orange
.. role:: accent-deep-orange
.. role:: accent-brown
.. role:: accent-grey
.. role:: accent-blue-grey
.. role:: accent-white

=============
Customization
=============

There are two methods to alter the theme.  The first, and simplest, uses the
options exposed through ``html_theme_options`` in ``conf.py``. This site's
options are:

.. code-block:: python

    html_theme_options = {
        'site_url': 'http://bashtage.github.io/sphinx-material/',
        'repo_url': 'https://github.com/bashtage/sphinx-material/',
        'repo_name': 'Material for Sphinx',
        'google_analytics': ['UA-XXXXX','auto'],
        'html_minify': True,
        'globaltoc_depth': 2
    }

.. confval:: hero

    To set the hero's text for an individual page, use the ``:hero:`` directive for the desired page.
    If not specified, then the page will not have a hero section.

Configuration Options
=====================

.. confval:: html_logo

    The logo in the navigation side menu and header (when browser viewport is wide enough) is changed
    by specifying the ``html_logo`` option. This must specify an image in the project's path
    (typically in the *docs/images* folder).

.. confval:: html_theme_options

    .. confval:: site_url

        Specify a site_url used to generate sitemap.xml links. If not specified, then
        no sitemap will be built.

    .. confval:: repo_url

        Set the repo url for the link to appear.

    .. confval:: repo_name

        The name of the repo. If must be set if repo_url is set.

    .. confval:: repo_type

        Must be one of github, gitlab or bitbucket.

    .. confval:: edit_uri

        This is the url segment that is concatenated with repo_url to point readers to the document's
        source file. This is typically in the form of ``'blob/<branch name>/<docs source folder>'``.
        Defaults to a blank string (which disables the edit icon). This is disabled for builds on
        ReadTheDocs as they implement their own mechanism based on the repository's branch or tagged
        commit.

    .. confval:: features

        Some features that have been ported and can be enabled by specifying the features name in a list
        of strings. The following features are supported:

        - `navigation.expand <https://squidfunk.github.io/mkdocs-material/setup/setting-up-navigation/#navigation-expansion>`_
        - `navigation.tabs <https://squidfunk.github.io/mkdocs-material/setup/setting-up-navigation/#navigation-tabs>`_ (only shows for browsers with large viewports)
        - `toc.integrate <https://squidfunk.github.io/mkdocs-material/setup/setting-up-navigation/#navigation-integration>`_
        - `navigation.sections <https://squidfunk.github.io/mkdocs-material/setup/setting-up-navigation/#navigation-sections>`_
        - `navigation.instant <https://squidfunk.github.io/mkdocs-material/setup/setting-up-navigation/#instant-loading>`_
        - `header.autohide <https://squidfunk.github.io/mkdocs-material/setup/setting-up-the-header/#automatic-hiding>`_
        - `navigation.top <https://squidfunk.github.io/mkdocs-material/setup/setting-up-navigation/#back-to-top-button>`_
        - `search.highlight <https://squidfunk.github.io/mkdocs-material/setup/setting-up-site-search/#search-highlighting>`_
        - `search.share <https://squidfunk.github.io/mkdocs-material/setup/setting-up-site-search/#search-sharing>`_

    .. confval:: icon for the repository

        The icon that represents the source code repository can be changed using the ``repo`` field of the
        ``icon`` `dict` (within the ``html_theme_options`` `dict`). Although this icon can be
        `any of the icons bundled with this theme <https://github.com/squidfunk/mkdocs-material/tree/master/material/.icons>`_,
        popular choices are:

        - |fa-git| ``fontawesome/brands/git``
        - |fa-git-alt| ``fontawesome/brands/git-alt``
        - |fa-git-square| ``fontawesome/brands/git-square``
        - |fa-github| ``fontawesome/brands/github``
        - |fa-github-alt| ``fontawesome/brands/github-alt``
        - |fa-github-square| ``fontawesome/brands/github-square``
        - |fa-gitlab| ``fontawesome/brands/gitlab``
        - |fa-gitkraken| ``fontawesome/brands/gitkraken``
        - |fa-bitbucket| ``fontawesome/brands/bitbucket``

    .. confval:: palette

        The theme's color pallet. This theme requires at least 2 schemes specified (ie 1
        scheme for light & 1 scheme for dark). Each scheme needs a specified ``primary`` and
        ``accent`` colors. Additionally, each scheme must have a ``toggle`` `dict` in which
        the ``name`` field specifies the text in the tooltip and the ``icon`` field specifies
        an icon to use to visually indicate which scheme is currently used.

        .. confval:: primary color

            Options are

            :red:`red`, :pink:`pink`, :purple:`purple`, :deep-purple:`deep-purple`, :indigo:`indigo`, :blue:`blue`,
            :light-blue:`light-blue`, :cyan:`cyan`, :teal:`teal`, :green:`green`, :light-green:`light-green`,
            :lime:`lime`, :yellow:`yellow`, :amber:`amber`, :orange:`orange`, :deep-orange:`deep-orange`,
            :brown:`brown`, :grey:`grey`, :blue-grey:`blue-grey`, :black:`black`, and :white:`white`.

        .. confval:: accent color

            Options are

            :accent-red:`red`, :accent-pink:`pink`, :accent-purple:`purple`, :accent-deep-purple:`deep-purple`,
            :accent-indigo:`indigo`, :accent-blue:`blue`, :accent-light-blue:`light-blue`, :accent-cyan:`cyan`,
            :accent-teal:`teal`, :accent-green:`green`, :accent-light-green:`light-green`, :accent-lime:`lime`,
            :accent-yellow:`yellow`, :accent-amber:`amber`, :accent-orange:`orange`, :accent-deep-orange:`deep-orange`.

        .. confval:: Toggle icon

            Options must be `any of the icons bundled with this theme <https://github.com/squidfunk/mkdocs-material/tree/master/material/.icons>`_.
            Popular combinations are

            .. csv-table::

                |toggle-off| ``material/toggle-switch-off-outline``, |toggle-on| ``material/toggle-switch``
                |sunny| ``material/weather-sunny``, |night| ``material/weather-night``
                |eye-outline| ``material/eye-outline``, |eye| ``material/eye``
                |lightbulb-outline| ``material/lightbulb-outline``, |lightbulb| ``material/lightbulb``

    .. confval:: direction

        Specifies the text direction.  Set to ``ltr`` (default) for left-to-right,
        or ``rtl`` for right-to-left.

    .. confval:: google_analytics_account

        Set to enable google analytics.

    .. confval:: globaltoc_depth

        The maximum depth of the global TOC; set it to -1 to allow unlimited depth.

    .. confval:: globaltoc_collapse

        If true, TOC entries that are not ancestors of the current page are collapsed.

    .. confval:: globaltoc_includehidden

        If true, the global TOC tree will also contain hidden entries.

    .. confval:: version_dropdown

        A flag indicating whether the version drop down should be included. You must supply a JSON file
        to use this feature.

    .. confval:: version_dropdown_text

        The text in the version dropdown button

    .. confval:: version_json

        The location of the JSON file that contains the version information. The default assumes there
        is a file versions.json located in the root of the site.

    .. confval:: version_info

        A dictionary used to populate the version dropdown.  If this variable is provided, the static
        dropdown is used and any JavaScript information is ignored.

Customizing the layout
======================

You can customize the theme by overriding Jinja template blocks. For example,
"layout.html" contains several blocks that can be overridden or extended.

Place a "layout.html" file in your project's "/_templates" directory (typically located in the
"docs" directory).

.. code-block:: bash

    mkdir source/_templates
    touch source/_templates/layout.html

Then, configure your 'conf.py':

.. code-block:: python

    templates_path = ['_templates']

Finally, edit your override file ``source/_templates/layout.html``:

.. code-block:: jinja

    {# Import the theme's layout. #}
    {% extends '!layout.html' %}

    {%- block extrahead %}
    {# Add custom things to the head HTML tag #}
    {# Call the parent block #}
    {{ super() }}
    {%- endblock %}

New Blocks
***********

The theme has a small number of new blocks to simplify some types of
customization:

``footerrel``
    Previous and next in the footer.
``font``
    The default font inline CSS and the class to the google API. Use this
    block when changing the font.
``fonticon``
    Block that contains the icon font. Use this to add additional icon fonts
    (e.g., `FontAwesome <https://fontawesome.com/>`_). You should probably call ``{{ super() }}`` at
    the end of the block to include the default icon font as well.

Version Dropdown
================

A version dropdown is available that lets you store multiple versions in a single site.
The standard structure of the site, relative to the base is usually::

    /
    /devel
    /v1.0.0
    /v1.1.0
    /v1.1.1
    /v1.2.0


To use the version dropdown, you must set ``version_dropdown`` to ``True`` in
the sites configuration.

There are two approaches, one which stores the version information in a JavaScript file
and one which uses a dictionary in the configuration.

Using a Javascript File
*************************

The data used is read via javascript from a file. The basic structure of the file is a dictionary
of the form [label, path].

.. code-block::javascript

    {
        "release": "",
        "development": "devel",
        "v1.0.0": "v1.0.0",
        "v1.1.0": "v1.1.0",
        "v1.1.1": "v1.1.0",
        "v1.2.0": "v1.2.0",
    }

This dictionary tells the dropdown that the release version is in the root of the site, the
other versions are archived under their version number, and the development version is
located in /devel.

.. note::

    The advantage of this approach is that you can separate version information
    from the rendered documentation.  This makes is easy to change the version
    dropdown in _older_ versions of the documentation to reflect additional versions
    that are released later. Changing the Javascript file changes the version dropdown
    content in all versions.  This approach is used in
    `statsmodels <https://www.statsmodels.org/>`_.

Using ``conf.py``
-----------------

.. warning::

    This method has precedence over the JavaScript approach. If ``version_info`` is
    not empty in a site's ``html_theme_options``, then the static approach is used.

The alternative uses a dictionary where the key is the title and the value is the target.
The dictionary is part of the size configuration's ``html_theme_options``.

.. code-block::python

    "version_info": {
        "release": "",  # empty is the master doc
        "development": "devel/",
        "v1.0.0": "v1.0.0/",
        "v1.1.0": "v1.1.0/",
        "v1.1.1": "v1.1.0/",
        "v1.2.0": "v1.2.0/",
        "Read The Docs": "https://rtd.readthedocs.io/",
    }

The dictionary structure is nearly identical.  Here you can use relative paths
like in the JavaScript version. You can also use absolute paths.

.. note::

    This approach is easier if you only want to have a fixed set of documentation,
    e.g., stable and devel.
