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

.. _customization:

=============
Customization
=============

Metadata for a single page
==========================

Each page can support a set of page-specific options. These are configured using metadata roles.
Each metadata is evaluated as a ``:key: value`` pair.

.. seealso::
    Review the
    `File-wide metadata <https://www.sphinx-doc.org/en/master/usage/restructuredtext/field-lists.html#file-wide-metadata>`_
    section in the sphinx docs.

.. themeconf:: hero

    Unlike, newer versions of mkdocs-material theme, this theme also supports the use of a textual
    "hero" section.

    To set the hero's text for an individual page, use the ``:hero:`` metadata field for the desired page.
    If not specified, then the page will not have a hero section.

    .. code-block:: rst
        :caption: This is how the hero for this page is declared.

        :hero: Configuration options to personalize your site.

.. themeconf:: hide-navigation

    If specified, hides the global navigation sidebar shown on the left side of the page.
    By default, the navigation menu is shown if the browser viewport is sufficiently wide.

    .. code-block:: rst
        :caption: Hide the navigation menu like so:

        :hide-navigation:

.. themeconf:: hide-toc

    If specified, hides the local table of contents shown on the right side of the page.
    By default the local table of contents is shown if the page contains sub-sections and the
    browser viewport is sufficiently wide. If the ``toc.integrate`` `feature <features>` is
    enabled, then this option has no effect.

    .. code-block:: rst
        :caption: Hide the Table of Contents like so:

        :hide-toc:

    Instead of using ``:hide-toc:``, this theme can also use the ``:tocdepth:`` metadata to hide the
    page's Table of Contents.

    .. code-block:: rst
        :caption: Set the depth for the Table of Contents to ``0``:

        :tocdepth: 0

Configuration Options
=====================

.. confval:: html_logo

    The logo in the navigation side menu and header (when browser viewport is wide enough) is changed
    by specifying the ``html_logo`` option.

    .. seealso::
        This option is documented with more detail in the Sphinx documentation.
        However, the size constraints for :external+sphinx_docs:confval:`html_logo`
        and `html_favicon` are not as strict for this theme.

.. confval:: html_theme_options

    This theme is configured using a ``html_theme_options`` `dict` in the *conf.py* file. The
    following subsections can be used can be used as keys whose values configure the theme in
    different ways.

    .. themeconf:: site_url

        Specify a site_url used to generate sitemap.xml links. If not specified, then
        no sitemap will be built.

    .. themeconf:: repo_url

        Set the repo url for the link to appear.

    .. themeconf:: repo_name

        The name of the repo. If must be set if repo_url is set.

    .. themeconf:: repo_type

        Must be one of github, gitlab or bitbucket.

    .. themeconf:: icon["repo"]

        The icon that represents the source code repository can be changed using the ``repo`` field of the
        ``icon`` `dict` (within the `html_theme_options` `dict`). Although this icon can be
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

        .. important::
            This option has no effect if the :themeconf:`repo_url` option is not specified.

        .. literalinclude:: conf.py
            :language: python
            :caption: This is the setting currently used by this documentation.
            :start-at: "icon": {
            :end-before: "site_url":

    .. themeconf:: edit_uri

        This is the url segment that is concatenated with :themeconf:`repo_url` to point readers to the document's
        source file. This is typically in the form of ``"blob/<branch name>/<docs source folder>"``.
        Defaults to a blank string (which disables the edit icon). This is disabled for builds on
        ReadTheDocs as they implement their own mechanism based on the repository's branch or tagged
        commit.

    .. themeconf:: features

        Some features that have been ported from the mkdocs-material theme and can be enabled by specifying the features name in a list
        of strings. The following features are supported:

        - `content.code.annotate <https://squidfunk.github.io/mkdocs-material/reference/code-blocks/#code-annotations>`_
        - `header.autohide <https://squidfunk.github.io/mkdocs-material/setup/setting-up-the-header/#automatic-hiding>`_
        - `navigation.expand <https://squidfunk.github.io/mkdocs-material/setup/setting-up-navigation/#navigation-expansion>`_
        - `navigation.instant <https://squidfunk.github.io/mkdocs-material/setup/setting-up-navigation/#instant-loading>`_
        - `navigation.sections <https://squidfunk.github.io/mkdocs-material/setup/setting-up-navigation/#navigation-sections>`_
        - `navigation.tabs <https://squidfunk.github.io/mkdocs-material/setup/setting-up-navigation/#navigation-tabs>`_
          (only shows for browsers with large viewports)

          .. note::
              Due to a difference in general document structure between mkdocs and sphinx, any
              `toctree` entry should start with a page entity (that contains a section header).
              Sphinx does allow `toctree` entries to be a list of only hyperlinks, but a
              navigation tab created from such an entry will only lead to the first hyperlink in
              the `toctree`.

              See `issue #33 <https://github.com/jbms/sphinx-immaterial/issues/33>`_ for a
              problematic demonstration.
        - `navigation.tabs.sticky <https://squidfunk.github.io/mkdocs-material/setup/setting-up-navigation/#sticky-navigation-tabs>`_
        - `navigation.top <https://squidfunk.github.io/mkdocs-material/setup/setting-up-navigation/#back-to-top-button>`_
        - `navigation.tracking <https://squidfunk.github.io/mkdocs-material/setup/setting-up-navigation/#anchor-tracking>`_
        - `search.highlight <https://squidfunk.github.io/mkdocs-material/setup/setting-up-site-search/#search-highlighting>`_
        - `search.share <https://squidfunk.github.io/mkdocs-material/setup/setting-up-site-search/#search-sharing>`_
        - `toc.integrate <https://squidfunk.github.io/mkdocs-material/setup/setting-up-navigation/#navigation-integration>`_

        .. hint::
            Sphinx automatically implements the
            `navigation.indexes <https://squidfunk.github.io/mkdocs-material/setup/setting-up-navigation/#section-index-pages>`_
            feature.

    .. themeconf:: palette

        The theme's color pallette **must be** a single `dict` or a `list` of `dict`\ s.
        Each `dict` can optionally specify a ``scheme``, ``primary``, ``accent``, and ``media``
        fields.

        .. themeconf:: scheme

            To use light and dark modes, this theme supports 2 schemes which are specified by a ``scheme`` field.

            1. The ``default`` scheme for light mode

               .. code-block:: python

                   html_theme_options = {
                        "palette": { "scheme": "default" }
                   }

            2. The ``slate`` scheme for dark mode.

               .. code-block:: python

                   html_theme_options = {
                        "palette": { "scheme": "slate" }
                   }


        .. themeconf:: primary

            Primary color options are

            :red:`red`, :pink:`pink`, :purple:`purple`, :deep-purple:`deep-purple`, :indigo:`indigo`, :blue:`blue`,
            :light-blue:`light-blue`, :cyan:`cyan`, :teal:`teal`, :green:`green`, :light-green:`light-green`,
            :lime:`lime`, :yellow:`yellow`, :amber:`amber`, :orange:`orange`, :deep-orange:`deep-orange`,
            :brown:`brown`, :grey:`grey`, :blue-grey:`blue-grey`, :black:`black`, and :white:`white`.

        .. themeconf:: accent

            Accent color options are

            :accent-red:`red`, :accent-pink:`pink`, :accent-purple:`purple`, :accent-deep-purple:`deep-purple`,
            :accent-indigo:`indigo`, :accent-blue:`blue`, :accent-light-blue:`light-blue`, :accent-cyan:`cyan`,
            :accent-teal:`teal`, :accent-green:`green`, :accent-light-green:`light-green`, :accent-lime:`lime`,
            :accent-yellow:`yellow`, :accent-amber:`amber`, :accent-orange:`orange`, :accent-deep-orange:`deep-orange`.

        .. themeconf:: toggle

            If using a `list` of schemes, then each scheme can have a ``toggle`` `dict` in which

            - The ``name`` field specifies the text in the tooltip.
            - The ``icon`` field specifies an icon to use that visually indicates which scheme is
              currently used.
              Options must be `any of the icons bundled with this theme <https://github.com/squidfunk/mkdocs-material/tree/master/material/.icons>`_.
              Popular combinations are

              .. csv-table::

                  |toggle-off| ``material/toggle-switch-off-outline``, |toggle-on| ``material/toggle-switch``
                  |sunny| ``material/weather-sunny``, |night| ``material/weather-night``
                  |eye-outline| ``material/eye-outline``, |eye| ``material/eye``
                  |lightbulb-outline| ``material/lightbulb-outline``, |lightbulb| ``material/lightbulb``

        .. themeconf:: media (palette preference)

            In order to automatically set the color palette based on the user's system preference, a media
            query can be specified with the ``media`` field.

            .. code-block:: python

                html_theme_options = {
                    "palette": [
                        {
                            "media": "(prefers-color-scheme: light)",
                            "scheme": "default",
                            "toggle": {
                                "icon": "material/toggle-switch-off-outline",
                                "name": "Switch to dark mode",
                            }
                        },
                        {
                            "media": "(prefers-color-scheme: dark)",
                            "scheme": "slate",
                            "toggle": {
                                "icon": "material/toggle-switch",
                                "name": "Switch to light mode",
                            }
                        },
                    ]
                }

    .. themeconf:: direction

        Specifies the text direction. Set to ``ltr`` (default) for left-to-right,
        or ``rtl`` for right-to-left.

    .. themeconf:: font

        Use this dictionary to change the fonts used in the theme. For example:

        .. code-block:: python

            html_theme_options = {
                "font": {
                    "text": "Roboto",  # used for all the pages' text
                    "code": "Roboto Mono"  # used for literal code blocks
                },
            }

        You can specify any of the available `Google Fonts <https://fonts.google.com/>`_.

    .. themeconf:: analytics

        Set to enable site analytics.

        .. code-block:: python

            html_theme_options = {
                "analytics": {
                    "provider": "google",
                    "property": "G-XXXXXXXXXX"  # Or "UA-XXXXXXXX-X"
                }
            }

    .. themeconf:: globaltoc_collapse

        If true (the default value), TOC entries that are not ancestors of the current page are collapsed.

        .. warning::
            Setting this option to `False` may lead to large generated page sizes since the entire
            table of contents tree will be duplicated on every page.

    .. themeconf:: toc_title

        A string that specifies the title text that appears above the table of
        contents in the side bar.  If neither this configuration option nor
        :themeconf:`toc_title_is_page_title` is specified, a default
        language-dependent translation of "Table of Contents" is used.  This
        configuration option takes precedence over
        :themeconf:`toc_title_is_page_title`.

    .. themeconf:: toc_title_is_page_title

       If set to ``True`` and :themeconf:`toc_title` is unspecified, the table of
       contents is labeled in the side bar by the title of the page itself.

    .. themeconf:: version_dropdown

        A `bool` flag indicating whether the version drop-down selector should be used. See
        :ref:`version_dropdown` below about using this feature.

    .. themeconf:: version_json

        The name of the JSON file that contains the version information to be used for the
        :ref:`version_dropdown` selector. The default assumes there is a file named *versions.json*
        located in the root directory of the site hosted by a webserver.

    .. themeconf:: version_info

        A list of dictionaries used to populate the :ref:`version_dropdown` selector.

.. _version_dropdown:

Version Dropdown
================

A version dropdown selector is available that lets you store multiple versions in a single site.
The standard structure of the site (relative to the base domain) is usually

.. code-block:: text

    /
    /1.0
    /2.0

Whereas Sphinx must be executed separately for each version of the documentation you are
building.

.. code-block:: text

    git fetch --all --tags
    git checkout 1.0
    sphinx-build docs _build/1.0
    git checkout 2.0
    sphinx-build docs _build/2.0

This means you need to implement a custom mechanism that allows keeping the built
documentation when checking out different branches or tagged commits.

.. important::
    To use the version dropdown selector, you must set :themeconf:`version_dropdown` to `True` in
    the `html_theme_options` dict.

    .. code-block:: python

        html_theme_options = {
            "version_dropdown": True,
        }

Supported Approaches
********************

There are two approaches:

1. The version information is stored in a :themeconf:`version_info` `list` in the conf.py file.

   .. note::
       Notice this is an ordered list. Meaning, approach 1 will take precedence over approach 2.

2. The version information is stored in a JSON file.

   The default name of the JSON file is ``versions.json``, but the JSON file's name could be
   changed by setting :themeconf:`version_json` in the conf.py file's `html_theme_options`.

   .. code-block:: python

       html_theme_options = {
           "version_json": "doc_versions.json",
       }

   .. warning::
       The JSON approach only works if your documentation is served from a webserver; it does not
       work if you use ``file://`` url). When serving the docs from a webserver the
       :themeconf:`version_json` file is resolved relative to the *parent* directory that contains
       the sphinx builder's HTML output. For example, if the builder's output is ``2.0``, you
       should have directory structure like so:

       .. code-block:: text

           /versions.json
           /1.0/index.html
           /2.0/index.html


Version Information Structure
*****************************

Both approaches use a data structure similar to what is used by the
`mkdocs mike plugin <https://github.com/jimporter/mike>`_. Contrary to what the mike plugin's
README says, the ``aliases`` field is not optional, but it can be set to an empty list if not using
aliases. Other required fields include ``version`` and ``title``.

- The ``version`` field can be set to a relative/absolute path or a URL.
- The ``title`` field is a string used to describe the version in the selector's dropdown menu.
- The ``aliases`` field is meant for giving a specific version a surname like "latest" or "stable".
  This way, a URL to the webserver "<webserver-domain>/stable" will be redirected to the corresponding
  ``version``'s path.

  Let's say you have a version of the documentation built on a pre-release in a directory
  called "3.0-rc1".

  .. code-block:: text

      /
      /1.0
      /2.0
      /3.0-rc1

  You can give this pre-released version an alias called "beta" or "latest".

  .. code-block:: json

      [
        {"version": "1.0", "title": "1.0", "aliases": []}
        {"version": "2.0", "title": "2.0", "aliases": ["stable"]}
        {"version": "3.0-rc1", "title": "Release Candidate 1", "aliases": ["beta", "latest"]}
      ]


.. literalinclude:: conf.py
    :language: python
    :caption: This is the version dropdown selector settings used by this theme:
    :start-after: BEGIN: version_dropdown
    :end-before: END: version_dropdown

.. note::
    ``aliases`` do not apply when using an external URL (as in not relative to the same webserver)
    in the ``verion`` field.

.. md-tab-set::
    :name: version_info_example

    .. md-tab-item:: Using ``version_info`` in conf.py

        .. code-block:: python

            html_theme_options = {
                "version_dropdown": True,
                "version_info": [
                    {"version": "2.0", "title": "2.0", "aliases": ["latest"]},
                    {"version": "1.0", "title": "1.0", "aliases": []},
                ],
            }

    .. md-tab-item:: Using a JSON file

        .. hint::
            Remember to set ``"version_dropdown": True`` in the conf.py file's `html_theme_options` `dict`.

        .. code-block:: json

            [
              {"version": "2.0", "title": "2.0", "aliases": ["latest"]},
              {"version": "1.0", "title": "1.0", "aliases": []},
            ]

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
**************
This theme has a new block inherited from the mkdocs-material theme:

``footerrel``
    Previous and next in the footer.
