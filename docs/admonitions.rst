
Admonitions
===========

This theme uses the :dutree:`admonition` directives for Sphinx admonitions.

rST and Sphinx
**************

Most of the admonitions that the mkdocs-material theme supports were "borrowed" from
admonitions defined in the reStructuredText specifications. You may recognize them from
usage in other sphinx-based themes. They are:

.. rst-example:: ``note``, ``todo``, ``seealso``

   .. seealso::
      This admonition is specific to Sphinx directives and not defined in the reStructuredText
      specifications as you can `seealso`. The `todo` admonition is also defined by Sphinx.

      The :dutree:`note` admonition *is* defined by the reStructuredText specifications.

.. rst-example:: ``tip``, ``hint``, ``important``

   .. important::
      It is :dutree:`important` to correctly use admonitions.

.. rst-example:: ``attention``, ``caution``, ``warning``

   .. warning::
      This is a :dutree:`warning`.

.. rst-example:: ``danger``, ``error``

   .. error::
      You have made a grave :dutree:`error`.

Admonitions from mkdocs-material
********************************

Some additional admonitions are supported via the source code from the mkdocs-material theme.
These admonitions can still be used, but the syntax is a little different because it relies
on the generic :dutree:`admonition` defined in the reStructuredText specifications.

To use the following admonitions' styles from the mkdocs-material theme, the rST syntax is
shown to demonstrate using the :rst:`:class:` option of generic admonitions.

.. important::
   The :rst:`:class:` options below (in the rST code blocks) must use lower case letters for the
   styling to work. Otherwise, the admonition will look like a `note` (as that is the
   default fallback style).

.. rst-example:: :css:`todo`, :css:`info`

   .. admonition:: Info
      :class: info

      Thanks to the mkdocs-material theme, the :css:`todo` class is also an alias of
      the :css:`info` class when not using the `todo` directive.

.. rst-example:: :css:`abstract`, :css:`summary`, :css:`tldr`

   .. admonition:: TL;DR
      :class: tldr

      The :rst:`:class: tldr` part is important.

.. rst-example:: :css:`success`, :css:`check`, :css:`done`

   .. admonition:: Accomplished
      :class: done

      This style is used for :css:`success`, :css:`check`, :css:`done` CSS classes.

.. rst-example:: :css:`question`, :css:`help`, :css:`faq`

   .. admonition:: FAQ
      :class: faq

      Helpful advice goes here.

.. rst-example:: :css:`failure`, :css:`fail`, :css:`missing`

   .. admonition:: Something Missing
      :class: missing

      We expected some loss of feature-coverage.

.. rst-example:: :css:`bug`

   .. admonition:: Known Bug
      :class: bug

      Bug reported data/conclusion.

.. rst-example:: :css:`example`

   .. admonition:: Example Admonition
      :class: example

      Example Body.

.. rst-example:: :css:`cite`, :css:`quote`

   .. admonition:: Unknown Quote
      :class: quote

      Somebody somewhere said something catchy.

Collapsible dropdown
*********************

.. _sphinxcontrib-details-directive extension: https://pypi.org/project/sphinxcontrib-details-directive

For collapsible dropdown admonitions, the mkdocs-material theme relies on a markdown syntax
extension that cannot be used with sphinx. Instead, this sphinx-immaterial theme relies on
the `sphinxcontrib-details-directive extension`_
to get similar results.

The `sphinxcontrib-details-directive extension`_ should be added to conf.py's extension list.

.. code-block:: python

   extensions = ["sphinx_immaterial", "sphinxcontrib.details.directive"]

If the :rst:`:class:` option is not supplied to the ``details`` directive then the admonition
style falls back to a `note` admonition style.

.. rst-example::

   .. details:: Open by default
      :class: example
      :open:

      Use the :rst:`:open:` option as a flag to expand the admonition by default.

.. rst-example::

   .. details:: Closed by default
      :class: help

      Without the :rst:`:open:` flag, the admonition is collapsed by default.

Removing the title
******************

Since the mkdocs-material theme relies on a markdown extension that also allows removing the title
from an admonition, this theme has an added directive to do just that: ``md-admonition``.

The admonition's title can be removed if the ``md-admonition`` directive is not provided
any arguments. Because the ``md-admonition`` directive is an adaptation of the generic
:dutree:`admonition` directive, the :rst:`:class:` option is still respected.

.. rst-example::

   .. md-admonition::
      :class: error

      This example uses the styling of the :css:`error` admonition

.. rst-example::

   .. md-admonition:: Using a title
      :class: help

      This example uses the styling of the :css:`help` admonition

.. hint::
   You can use the ``md-admonition`` directive in other Sphinx themes by adding the theme's module to
   your `extensions` list in *conf.py*

   .. code-block:: python

      extensions = ["sphinx_immaterial.md_admonition"]

Custom admonitions
******************

If you want to add a custom admonition type, all you need is a color and an \*.svg icon.
Copy the icon's code from the `.icons <https://github.com/squidfunk/mkdocs-material/tree/master/material/.icons>`_
folder and add the new CSS to an additional style sheet.

.. md-tab-set::

   .. md-tab-item:: rST code

      .. rst-example:: Pied Piper Example
         :output-prefix:

         .. admonition:: Pied Piper
            :class: pied-piper

            Don't tell him you use spaces instead of tabs...

   .. md-tab-item:: CSS code

      .. literalinclude:: _static/extra_css.css
         :language: css
         :caption: docs/_static/extra_css.css
         :start-after: /* *************************** custom admonition style rules
         :end-before: /* **********

   .. md-tab-item:: conf.py code

      .. code-block:: python
         :caption: docs/conf.py

         html_static_path = ["_static"]
         html_css_files = ["extra_css.css"]

.. _change_admonition_icon:

Changing the Admonition Icon
----------------------------

Any of the above builtin admonitions' icons can be changed using the
:themeconf:`icon`\ [:themeconf:`admonition`] field in :confval:`html_theme_options` settings.

.. code-block:: python
   :caption: Changing the `note` icon in conf.py

   html_theme_options = {
       "icon": {
           "admonition": {
               "note": "material/file-document-outline",
           },
       },
   }

.. admonition:: ``seealso`` uses the ``note`` icon
   :class: missing

   The `seealso` admonition (which is specific to Sphinx - not reStructuredText) will use the same
   icon set for the `note` admonition. If you want to override the icon for the `seealso`
   admonition, then use the tactic shown in the `Custom admonitions`_ section (with regard to
   only the icon changes in CSS).

.. details:: Alternate icon sets
   :class: example

   Here's some recipes for use in conf.py

   .. md-tab-set::

      .. md-tab-item:: Octicons

         .. code-block:: python

            html_theme_options = {
                "icon": {
                    "admonition": {
                        "note": "octicons/tag-16",
                        "abstract": "octicons/checklist-16",
                        "info": "octicons/info-16",
                        "tip": "octicons/squirrel-16",
                        "success": "octicons/check-16",
                        "question": "octicons/question-16",
                        "warning": "octicons/alert-16",
                        "failure": "octicons/x-circle-16",
                        "danger": "octicons/zap-16",
                        "bug": "octicons/bug-16",
                        "example": "octicons/beaker-16",
                        "quote": "octicons/quote-16",
                    },
                },
            }

      .. md-tab-item:: FontAwesome

         .. code-block:: python

            html_theme_options = {
                "icon": {
                    "admonition": {
                        "note": "fontawesome/solid/note-sticky",
                        "abstract": "fontawesome/solid/book",
                        "info": "fontawesome/solid/circle-info",
                        "tip": "fontawesome/solid/bullhorn",
                        "success": "fontawesome/solid/check",
                        "question": "fontawesome/solid/circle-question",
                        "warning": "fontawesome/solid/triangle-exclamation",
                        "failure": "fontawesome/solid/bomb",
                        "danger": "fontawesome/solid/skull",
                        "bug": "fontawesome/solid/robot",
                        "example": "fontawesome/solid/flask",
                        "quote": "fontawesome/solid/quote-left",
                    },
                },
            }