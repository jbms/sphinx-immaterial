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

.. _any of the icons bundled with this theme: https://github.com/squidfunk/mkdocs-material/tree/master/material/.icons

.. _customization:

=============
Customization
=============

Metadata for a single page
==========================

Each page can support a set of page-specific options. These are configured using metadata roles.
Each metadata is evaluated as a :rst:`:key: value` pair.

.. seealso::
    Review the
    `File-wide metadata <https://www.sphinx-doc.org/en/master/usage/restructuredtext/field-lists.html#file-wide-metadata>`_
    section in the sphinx docs.

.. themeconf:: hero

    Unlike, newer versions of mkdocs-material theme, this theme also supports the use of a textual
    "hero" section.

    To set the hero's text for an individual page, use the :rst:`:hero:` metadata field for the desired page.
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

    Instead of using :rst:`:hide-toc:`, this theme can also use the :rst:`:tocdepth:` metadata to hide the
    page's Table of Contents.

    .. code-block:: rst
        :caption: Set the depth for the Table of Contents to ``0``:

        :tocdepth: 0

.. themeconf:: hide-edit-link

    If specified, hides the "Edit this page" link at the top of the page.  By
    default, an edit link is shown if :themeconf:`edit_uri` is specified.  This
    option overrides that for a given page.

    .. code-block:: rst
        :caption: Hide the "Edit this page" link:

        :hide-edit-link:

    A common use case for this option is to specify it on automatically-generated
    pages, as for those pages there is no source document to edit.

.. themeconf:: hide-footer

    If specified, hides the current page's footer (specifically the part containing the
    "Previous" and "Next" links).

    .. code-block:: rst
        :caption: Hide the "Previous" and "Next" links at the bottom of the page:

        :hide-footer:

.. themeconf:: hide-feedback

    If specified, hides the user :themeconf:`feedback` buttons at the bottom of the current page.

    .. code-block:: rst
        :caption: Hide the feedback buttons at the bottom of the page:

        :hide-feedback:

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

    .. themeconf:: icon

        .. literalinclude:: conf.py
            :language: python
            :caption: This is the setting currently used by this documentation.
            :start-at: "icon": {
            :end-before: "site_url":

        .. themeconf:: repo

            The icon that represents the source code repository can be changed using the
            :themeconf:`icon`\ [:themeconf:`repo`] field in the :confval:`html_theme_options`
            settings. Although this icon can be `any of the icons bundled with this theme`_,
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
        
        .. themeconf:: admonition

            The default icons for admonitions can be changed by setting this field to a `dict` in
            which the keys are CSS classes (see :doc:`admonitions`) and the values are
            `any of the icons bundled with this theme`_.
            
            .. seealso::
                Refer to the :ref:`change_admonition_icon` section for more detail.

        .. themeconf:: edit

            The icon used for the generated "edit this page" button at the top of the document.
            This is only used if :themeconf:`edit_uri` is configured and when not explicitly hidden
            using :themeconf:`hide-edit-link`.

            As usual, `any of the icons bundled with this theme`_ can be used here. While the default is
            ``material/pencil``, this documentation uses ``material/file-edit-outline``

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
        - `content.tabs.link <https://squidfunk.github.io/mkdocs-material/reference/content-tabs/#linked-content-tabs>`_

          .. seealso::
              Please refer to the :ref:`linked_tabs` section for more information.

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
        - `announce.dismiss <https://squidfunk.github.io/mkdocs-material/setup/setting-up-the-header/?h=ann#mark-as-read>`_
          
          .. seealso::
              Refer to the `New blocks`_ section below about how to add an announcement banner.
        - ``toc.follow``

          This is similar to the `toc.follow
          <https://squidfunk.github.io/mkdocs-material/setup/setting-up-navigation/#anchor-following>`__
          feature supported by the mkdocs-material theme, but differs in that
          both the left and right sidebar are scrolled automatically.

          - The local table-of-contents scrolls automatically to keep the
            currently-displayed document section in view.  Note that this
            applies to all three possible locations for the local
            table-of-contents:

            - in the right sidebar, which is the default location if the browser
              viewport is sufficiently wide;
            - in the left sidebar, if the ``toc.integrate`` feature is enabled;
            - in the "layered" navigation menu, if the browser viewport is
              sufficiently narrow.

          - If the ``toc.integrate`` feature is disabled, the left sidebar
            additionally scrolls automatically to keep within view either:

            - the navigation entry for the current document, or
            - if the current document contains sections with child documents,
              the navigation entry for the currently-displayed document section.

            Note that if the ``toc.integrate`` feature is enabled, the left
            sidebar is instead scrolled for the local table-of-contents as
            described above.
        - ``toc.sticky``

          Makes headings in the left and right sidebars "sticky", such that the
          full path to each heading remains visible even as the sidebars are
          scrolled.

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
              Options must be `any of the icons bundled with this theme`_.
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

        The specified fonts will be downloaded automatically (using the cache
        specified by :confval:`sphinx_immaterial_external_resource_cache_dir`)
        and included in the built documentation.

    .. themeconf:: analytics

        To enable site analytics, a ``provider`` and ``property`` fields **must** be specified in this dict.

        .. code-block:: python

            html_theme_options = {
                "analytics": {
                    "provider": "google",
                    "property": "G-XXXXXXXXXX"
                }
            }
        
        .. themeconf:: feedback

            This theme also supports user feedback using site analytics. Along with the required
            ``provider`` and ``property`` fields, the :themeconf:`feedback` `dict` also requires
            the following fields:

            ``title``
                The text used to invite user feedback (placed just above the feedback buttons).
            ``ratings``
                This `list` of `dict` objects specifies the user's options for feedback. Each `dict`
                will represent a button and requires the following fields:

                ``icon``
                    As usual, `any of the icons bundled with this theme`_ can be specified here.
                ``name``
                    The text shown in the tooltip when hovering over a feedback button.
                ``data``
                    The data transmitted to your analytics provider upon submission of user feedback.
                ``note``
                    The text displayed after the user feedback is submitted. You can use a HTML hyperlink
                    element :html:`<a href="a_url">link text</a>` to encourage further user interaction (see
                    example snippet below).

            .. code-block:: python
                :caption: using Google analytics to collect user feedback for each page

                html_theme_options = {
                    "analytics": {
                        "provider": "google",
                        "property": "G-XXXXXXXXXX",
                        "feedback": {
                            "title": "Was this page helpful?",
                            "ratings": [
                                {
                                    "icon": "material/emoticon-happy-outline",
                                    "name": "This page was helpful",
                                    "data": 1,
                                    "note": "Thanks for the feedback!",
                                },
                                {
                                    "icon": "material/emoticon-sad-outline",
                                    "name": "This page could be improved",
                                    "data": 0,
                                    "note": "Thanks for the feedback! Help us improve this page by "
                                    '<a href="https://github.com/jbms/sphinx-immaterial/issues">opening an issue</a>.',
                                },
                            ],
                        },
                    },
                }

            .. seealso::
                User feedback can be hidden for a certain page by using the :themeconf:`hide-feedback`
                metadata tag in the document's source.

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

        .. code-block:: python

            html_theme_options = {
                "toc_title": "Contents",
            }

    .. themeconf:: toc_title_is_page_title

       If set to ``True`` and :themeconf:`toc_title` is unspecified, the table of
       contents is labeled in the side bar by the title of the page itself.

       .. code-block:: python

           html_theme_options = {
               "toc_title_is_page_title": True,
           }

    .. themeconf:: social

        A `list` of `dict`\ s that define iconic links in the site's footer. Each `dict` shall
        have a :python:`"icon"` and a :python:`"link"` field.

        - The :python:`"icon"` field can be specifed as `any of the icons bundled with this theme`_
        - The :python:`"link"` field is simply the hyperlink target added to the icon specified.

        .. literalinclude:: conf.py
            :caption: This theme uses the following configuration:
            :start-after: # BEGIN: social icons
            :end-before: # END: social icons

    .. themeconf:: version_dropdown

        A `bool` flag indicating whether the version drop-down selector should be used. See
        :ref:`version_dropdown` below about using this feature.

    .. themeconf:: version_json

        The name of the JSON file that contains the version information to be used for the
        :ref:`version_dropdown` selector. The default assumes there is a file named *versions.json*
        located in the root directory of the site hosted by a webserver.

    .. themeconf:: version_info

        A list of dictionaries used to populate the :ref:`version_dropdown` selector.

.. confval:: sphinx_immaterial_external_resource_cache_dir

   Specifies the local directory used to cache external resources, such as
   Google Fonts.  If this config option is not specified, defaults to:

   - the value of the :envvar:`SPHINX_IMMATERIAL_EXTERNAL_RESOURCE_CACHE_DIR`
     environment variable, if specified; or
   - a platform-dependent cache directory
     (e.g. :file:`~/.cache/sphinx_immaterial/external_resources` on Linux).

.. envvar:: SPHINX_IMMATERIAL_EXTERNAL_RESOURCE_CACHE_DIR

   Environment variable that specifies a default value for the
   :confval:`sphinx_immaterial_external_resource_cache_dir` configuration
   option.

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

Partial Layout
**************

To override partial html templates in the theme, the documentation project's _template
folder should imitate the structure of HTML partial templates in this theme's
`src directory <https://github.com/jbms/sphinx-immaterial/tree/main/src>`_.

For example, this theme (unlike the mkdocs-material theme) still supports a user defined
``extracopyright`` block. To make use of this, create a file titled ``footer.html`` in the
project's ``_templates/partials`` folder. So the project's documentation sources are in a
folder named ``docs``.

.. code-block:: text

    ┌ docs/
    └┬ _templates/
     └┬ partials/
      └─ footer.html

In the ``footer.html`` file, add the necessary code by extending the theme's original
HTML template of the same name.

.. code-block:: jinja

    {% extends "!partials/footer.html" %}
    {# the '!' in "!partials/footer.html" is important #}
    {% block extracopyright %}
      <p>EXTRA COPYRIGHT</p>
    {% endblock %}

Lastly, make sure the project's documentation ``conf.py`` has the following line:

.. code-block:: py

    templates_path = ["_templates"]

New Blocks
**************
This theme has a few new block inherited from the mkdocs-material theme:

``footerrel``
    Previous and next in the footer.

``announce``
    An announcement can be added to the top of the page by extending this theme's base.html
    template. For example, this documentation uses the following custom template to add an
    announcement (`scroll to top to see it in action <#>`_).

    .. literalinclude:: _templates/base.html
        :caption: docs/_templates/base.html
        :language: jinja

    Optionally, add the :python:`"announce.dismiss"` in the :themeconf:`features` list to let readers
    dismiss the announcement banner.
