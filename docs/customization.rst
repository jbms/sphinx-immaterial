:hero: Configuration options to personalize your site.

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

.. themeconf:: show-comments

    If specified, allows comments to be enabled at the bottom of the current page.

    .. code-block:: rst
        :caption: Enable comments at the bottom of the page:

        :show-comments:

    .. seealso::
        Using comments requires extra steps. See `Adding a comment system`_ instructions.

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

    This theme is configured using a :external+sphinx_docs:confval:`html_theme_options` `dict` in
    the conf.py file. The following subsections can be used as keys whose values configure the
    theme in different ways.

    .. themeconf:: site_url

        Specify a site_url used to generate sitemap.xml links. If not specified, then
        no sitemap will be built.

    .. themeconf:: repo_url

        The link to the repository will be rendered next to the search bar on large screens and as
        part of the main navigation drawer on smaller screen sizes. Additionally, for public
        repositories hosted on `GitHub <https://github.com>`_ or `GitLab
        <https://about.gitlab.com/>`_, the number of stars and forks is automatically requested and
        rendered.

        GitHub repositories also include the tag of the latest release. Unfortunately, GitHub
        only provides `an API endpoint to obtain the latest release
        <https://docs.github.com/en/rest/releases/releases#get-the-latest-release>`_ - not the
        latest tag. Thus, make sure to create a release (not pre-release) for the latest tag you
        want to display next to the number of stars and forks.

    .. themeconf:: repo_name

        The name of the repository. If :themeconf:`repo_url` is set, then the repository's name
        will be extracted from the given URL. Optionally, this can be set to customize the
        repository name.

        .. warning::
            If the :themeconf:`repo_url` does not use a ``github``, ``gitlab``, or ``bitbucket``
            domain, then this option must be set explicitly.

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

            .. jinja::

                {% for icon in ["git", "git-alt", "github", "github-alt", "gitlab", "gitkraken", "bitbucket"] %}
                - :si-icon:`fontawesome/brands/{{icon}}` ``fontawesome/brands/{{icon}}``
                {% endfor %}

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

        .. themeconf:: logo

            The icon that is used as a fallback when :confval:`html_logo` is not specified.
            The behavior of this option is inherited from the mkdocs-material theme, so
            `any of the icons bundled with this theme`_ can be used here.

            .. code-block:: python

                html_theme_options = {
                    "icon": {
                        "logo": "material/library"
                    },
                }

        .. themeconf:: alternate

            The icon used for the language selector button. See :themeconf:`languages` to
            configure the options in the language selector drop-down menu.

            .. code-block:: python

                html_theme_options = {
                    "icon": {
                        "logo": "material/translate"
                    },
                }

    .. themeconf:: edit_uri

        This is the url segment that is concatenated with :themeconf:`repo_url` to point readers to the document's
        source file. This is typically in the form of ``"blob/<branch name>/<docs source folder>"``.
        Defaults to a blank string (which disables the edit icon).

    .. themeconf:: features

        Some features that have been ported from the mkdocs-material theme and can be enabled by
        specifying the feature's name in a list of strings. The following features are supported:

        - `content.code.annotate <https://squidfunk.github.io/mkdocs-material/reference/code-blocks/#code-annotations>`_

          .. seealso:: Refer to the :doc:`code_annotations` document for more detail.

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
        Each `dict` can optionally specify a :themeconf:`scheme`, :themeconf:`primary`,
        :themeconf:`accent`, and :themeconf:`media <media (palette preference)>` fields.

        .. themeconf:: scheme

            To use light and dark modes, this theme supports 2 schemes which are specified by a ``scheme`` field.

            .. code-block:: python
                :name: scheme-color-conf-example

                html_theme_options = {
                    "palette": { "scheme": "default" }
                }

            .. only:: html

                - :test-color-scheme:`default` (scheme for light mode)
                - :test-color-scheme:`slate` (scheme for dark mode)

                Click one of the listed schemes to see how it looks.

            .. only:: not html

                - ``default`` (scheme for light mode)
                - ``slate`` (scheme for dark mode)

        .. themeconf:: primary

            The primary color is used for the header, the sidebar, text links and several other
            components.

            .. code-block:: python
                :name: primary-color-conf-example

                html_theme_options = {
                    "palette": { "primary": "green" }
                }

            Primary color options are

            .. only:: html

                .. jinja:: colors

                    .. hlist::
                        :columns: 3

                    {% for color in supported_primary %}
                        - :test-color-primary:`{{color}}`
                    {% endfor %}

                    Click one of the colors to see how it looks.

            .. only:: not html

                .. jinja:: colors

                    .. hlist::
                        :columns: 7

                    {% for color in supported_primary %}
                        - ``{{color}}``
                    {% endfor %}

        .. themeconf:: accent

            The accent color is used to denote elements that can be interacted with, e.g. hovered
            links, buttons, and scrollbars.

            .. code-block:: python
                :name: accent-color-conf-example

                html_theme_options = {
                    "palette": { "accent": "green" }
                }

            Accent color options are

            .. only:: html

                .. jinja:: colors

                    .. hlist::
                        :columns: 4

                    {% for color in supported_accent %}
                        - :test-color-accent:`{{color}}`
                    {% endfor %}

                    Click one of the colors to see how it looks.

            .. only:: (not html)

                .. jinja:: colors

                    .. hlist::
                        :columns: 4

                    {% for color in supported_accent %}
                        - ``{{color}}``
                    {% endfor %}

        .. themeconf:: toggle

            If using a `list` of schemes, then each scheme can have a ``toggle`` `dict` in which

            - The ``name`` field specifies the text in the tooltip.
            - The ``icon`` field specifies an icon to use that visually indicates which scheme is
              currently used.
              Options must be `any of the icons bundled with this theme`_.
              Popular combinations are

              .. csv-table::

                  :si-icon:`material/toggle-switch-off-outline` ``material/toggle-switch-off-outline``, :si-icon:`material/toggle-switch` ``material/toggle-switch``
                  :si-icon:`material/weather-sunny` ``material/weather-sunny``, :si-icon:`material/weather-night` ``material/weather-night``
                  :si-icon:`material/eye-outline` ``material/eye-outline``, :si-icon:`material/eye` ``material/eye``
                  :si-icon:`material/lightbulb-outline` ``material/lightbulb-outline``, :si-icon:`material/lightbulb` ``material/lightbulb``

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

        To use the user's system font instead of (and similar to) the theme's default fonts,
        set this field to :python:`False`.

        .. code-block:: python
            :caption: rely on fonts available in the user's OS.

            html_theme_options = {
                "font": False,
            }

        :Using a self-hosted font:
            Using a custom or self-hosted font requires extra CSS to define the font family and
            overridden CSS theme variables. The following steps were used to self-host Google's
            "Comic Neue" and "Comic Mono" fonts as an example.

            1. Copy the font files to your project's ``_static`` folder. The font's file
               :css:`format()` will be specified in step 2. If the font has different weights, then
               each weight will have a separate file. By default, this theme mainly uses 300, 400, and
               700 weights, although only one weight/variant is technically required (400 weight is
               recommended).
            2. Define the font family in a CSS file and append the CSS file's name to the project's
               list of `html_css_files` in config.py.

               Each weight must have a corresponding :css:`@font-face` rule. The same mandate applies
               to *italic* variants (if any) and their weights.

               .. literalinclude:: _static/custom_font_example.css
                   :caption: docs/_static/custom_font_example.css
                   :language: css

               The path specified in the :css:`url()` is relative to the file defining the font family.
               For example, the above snippet is located in this project's ``_static`` folder where the
               font's files are located in ``_static/example-custom-font/`` folder.
            3. Override the theme's CSS variables.

               .. code-block:: css

                   :root {
                     --md-text-font: "Comic Neue"; /* (1)! \*/
                     --md-code-font: "Comic Mono"; /* (2)! \*/
                   }

               .. code-annotations::
                    1. Used for regular text.
                    2. Used for ``code snippets``.

               .. warning::
                   Always define fonts with the CSS variables shown above and not with
                   :css:`font-family` because :css:`font-family` uses the theme's CSS variables that
                   define the system font fallback.

            .. rst-example::
                :class: custom-font-example

                This text is just an **example**.
                *Notice* the font family used is different (monospaced) in the code snippet.

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
        Collapsed entries cannot be expanded.

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

        Optionally, custom text may be specified for the icon's tooltip with the :python:`"name"`
        field. If the :python:`"name"` is not specified, then the domain of the :python:`"link"`
        is used automatically.

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

    .. themeconf:: scope

        Scope of site preferences (i.e. cookie consent, content tabs, color palette).
        If you have multi-site project, you can set this to "/"
        to share preferences between all sub-sites. See the :ref:`version_dropdown` section
        on how to setup a multi-site project.

    .. themeconf:: languages

        A list of dictionaries to populate the language selector drop-down menu (in the navigation
        bar). Each list item must have the following required fields:

        ``name``
            This value is used inside the language selector as the displayed name of the language
            and must be set to a non-empty string.

        ``link``
            This value is the URI link which points to the relative path of the documentation built
            for the associated language.

        ``lang``
            This value must be an `ISO 639-1 language code
            <https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes>`_ and is used for the
            ``hreflang`` attribute of the link, improving discoverability via search engines.

        For example, the following snippet adds English and French options to the language selector
        drop-down menu:

        .. code-block:: python

            html_theme_options = {
                "languages": [
                    {
                        "name": "English",
                        "link": "en/",  # points to ./en/ subdirectory
                        "lang": "en",
                    },
                    {
                        "name": "French",
                        "link": "fr/",  # points to ./fr/ subdirectory
                        "lang": "fr",
                    },
                ]
            }

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

.. confval:: sphinx_immaterial_bundle_source_maps

   Write ``.css.map`` and ``.js.map`` source maps for the CSS and JavaScript
   bundles to the output directory.  Source maps are helpful when developing the
   theme.

.. confval:: sphinx_immaterial_font_fetch_max_workers

    The number of workers executed in parallel when fetching a cache of the specified
    :themeconf:`font`. If not specified, this defaults to using 33 maximum *possible* threads.
    If set less than or equal to 0, then this will be determined by the
    :py:class:`~concurrent.futures.ThreadPoolExecutor` default.

.. envvar:: SPHINX_IMMATERIAL_FONT_FETCH_MAX_WORKERS

    An environment variable that can be used to override
    :confval:`sphinx_immaterial_font_fetch_max_workers`.
    This value must be an integer.

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
       work if you use ``file://`` url. When serving the docs from a webserver the
       :themeconf:`version_json` file is resolved relative to the directory that contains
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
    in the ``version`` field.

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

To redirect browsers to the latest version, add a ``index.html`` in the same directory as your
project's ``versions.json`` file to be served as the domain's base URL. It should look something
like the following:

.. code-block:: html

    <!DOCTYPE HTML>
    <html lang="en">
        <head>
            <meta charset="utf-8">
            <meta http-equiv="refresh" content="0; url=latest/" />
            <link rel="canonical" href="latest/" />
        </head>
        <body>
            <p>If this page does not refresh automatically, then please direct your browser to
                <a href="latest/">our latest docs</a>.
            </p>
        </body>
    </html>

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

Adding a comment system
-----------------------

.. _Giscus: https://giscus.app/

This theme supports using a third-party comment system of your choice at the bottom of any page.
There are several services that can deliver an integrated comment system, but the following example
demonstrates using Giscus_ which is Open Source and built on Github's Discussions feature.

1. Ensure these requisites are completed:

   - Install the `Giscus Github App <https://github.com/apps/giscus>`_ and grant access to the
     repository that should host comments as GitHub discussions. Note that this can be a repository
     different from your documentation.
   - Visit Giscus_ and generate the snippet through their configuration tool to load the comment
     system. Copy the snippet for the next step. The resulting snippet should look similar to this:

     .. code-block:: html

         <script
           src="https://giscus.app/client.js"
           data-repo="<username>/<repository>"
           data-repo-id="..."
           data-category="..."
           data-category-id="..."
           data-mapping="title"
           data-reactions-enabled="1"
           data-emit-metadata="1"
           data-theme="light"
           data-lang="en"
           crossorigin="anonymous"
           async>
         </script>
2. Override the theme's partials/comments.html template (blank by default) in your documentation
   source, and add the following code to you comments.html template override:

   .. code-block:: html
       :caption: docs/_templates/partials/comments.html
       :emphasize-lines: 3

       {% if page.meta.comments %} <!-- (1)! -->
         <h2 id="__comments">{{ lang.t("meta.comments") }}</h2>
         <!-- Insert generated snippet (2) here -->

         <!-- Synchronize Giscus theme with palette -->
         <script>
           var giscus = document.querySelector("script[src*=giscus]")

           /* Set palette on initial load */
           var palette = __md_get("__palette")
           if (palette && typeof palette.color === "object") {
             var theme = palette.color.scheme === "slate" ? "dark" : "light" // (3)!
             giscus.setAttribute("data-theme", theme)
           }

           /* Register event handlers after documented loaded */
           document.addEventListener("DOMContentLoaded", function() {
             var ref = document.querySelector("[data-md-component=palette]")
             ref.addEventListener("change", function() {
               var palette = __md_get("__palette")
               if (palette && typeof palette.color === "object") {
                 var theme = palette.color.scheme === "slate" ? "dark" : "light" // (4)!

                 /* Instruct Giscus to change theme */
                 var frame = document.querySelector(".giscus-frame")
                 frame.contentWindow.postMessage(
                   { giscus: { setConfig: { theme } } },
                   "https://giscus.app"
                 )
               }
             })
           })
         </script>
       {% endif %}

   .. code-annotations::
       #. This template will only be used if the :themeconf:`show-comments` metadata is added to the document's
          source.
       #. This should be the snippet generated from step 1.
       #. This code block ensures that Giscus renders with a dark theme when the
          :themeconf:`palette`\ [:themeconf:`scheme`] is set to ``slate``. Note that multiple dark
          themes are available, so you can change it to your liking.
       #. If changing the dark theme used by Giscus, then also change the dark theme name here as
          this takes affect when toggling between light and dark color :themeconf:`scheme`\ s.
       #. If changing the dark theme used by Giscus, then also change the dark theme name here as
          this takes affect when toggling between light and dark color :themeconf:`scheme`\ s.
3. Enable comments for a certain page by adding the :themeconf:`show-comments` metadata to the document's source.

Version Banner
--------------

If you're using :ref:`version_dropdown`, you might want to display a warning when the user visits
any other version than the latest version. Using a partial template, you can override the
``outdated`` block with the a new jinja template located in the project's documentation's
``_templates/base.html``.

.. code-block:: jinja
    :caption: docs/_templates/base.html

    {% extends "!base.html" %}

    {% block outdated %}
      You're not viewing the latest version.
      <a href="{{ '../' ~ base_url}}">
        <strong>Click here to go to latest.</strong>
      </a>
    {% endblock %}

.. example:: Changing the color of the banner in dark scheme
    :collapsible:

    Depending on the project's choices for :themeconf:`palette` colors, it might make the banner's
    text more legible to change the background color of the banner.

    .. code-block:: css
        :caption: docs/_static/extra_style.css

        /* only override for dark/slate scheme */
        [data-md-color-scheme="slate"] .md-banner--warning {
          background: var(--md-footer-bg-color);
        }

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
