
Admonitions
===========

The theme uses the ``admonition`` directives for Sphinx admonitions.

rST and Sphinx
**************

Most of the admonitions that the mkdocs-material theme supports were "borrowed" from
admonitions defined in the reStructuredText specifications. You may recognize them from
usage in other sphinx-based themes. They are:

``note``, ``todo``, ``seealso``
   .. seealso::
      This admonition is specific to Sphinx directives and not defined in the rST specifications
      as you can `seealso`.

      ``note`` and ``todo`` are admonitions defined by the rST specifications.

``tip``, ``hint``, ``important``
   .. important::
      It is **important** to correctly use admonitions.

``attention``, ``caution``, ``warning``
   .. warning::
      This is a **warning**.

``danger``, ``error``
   .. error::
      You have made a grave **error**.

Admonitions from mkdocs-material
********************************

Some additional admonitions are supported via the source code from the mkdocs-material theme.
These admonitions can still be used, but the syntax is a little different because it relies
on the generic admonition defined in the reStructuredText specifications.

To use the following admonitions' styles from the mkdocs-material theme, the rST syntax is
shown inside the demonstrated admonition.

.. important::
   The ``:class:`` options below (in the rST code blocks) must use lower case letters for the
   styling to work. Otherwise, the admonition will look like a `note` (as that is the
   default fallback style).

``todo``, ``info``
   .. admonition:: Info
      :class: info

      Thanks to the mkdocs-material theme, the ``todo`` class is also an alias of the
      ``info`` class when not using the ``.. todo::`` directive.

      .. code-block:: rst

         .. admonition:: Info
            :class: info

``abstract``, ``summary``, ``tldr``
   .. admonition:: TL;DR
      :class: tldr

      .. code-block:: rst

         .. admonition:: TL;DR
            :class: tldr

``success``, ``check``, ``done``
   .. admonition:: Done
      :class: done

      .. code-block:: rst

         .. admonition:: Done
            :class: done

``question``, ``help``, ``faq``
   .. admonition:: FAQ
      :class: faq

      .. code-block:: rst

         .. admonition:: FAQ
            :class: faq

``failure``, ``fail``, ``missing``
   .. admonition:: Missing
      :class: missing

      .. code-block:: rst

         .. admonition:: Missing
            :class: missing

``bug``
   .. admonition:: Bug
      :class: bug

      .. code-block:: rst

         .. admonition:: Bug
            :class: bug

``example``
   .. admonition:: Example
      :class: example

      .. code-block:: rst

         .. admonition:: Example
            :class: example

``cite``, ``quote``
   .. admonition:: Quote
      :class: quote

      .. code-block:: rst

         .. admonition:: Quote
            :class: quote

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


If the ``:class:`` option is not supplied to the ``details`` directive then the admonition
style falls back to a `note` admonition style.

.. details:: Open by default
   :class: example
   :open:

   .. code-block:: rst

      .. details:: Open by default
         :class: example
         :open:

.. details:: Closed by default
   :class: help

   .. code-block:: rst

      .. details:: Closed by default
         :class: help

Removing the title
******************

Since the mkdocs-material theme relies on a markdown extension that also allows removing the title
from an admonition, this theme has an added directive to do just that: ``md-admonition``.

The admonition's title can be removed if the ``md-admonition`` directive is not provided
any arguments. Because the ``md-admonition`` directive is an adaptation of the generic
``admonition`` directive, the ``class`` option is still respected.

.. md-admonition::
   :class: error

   This example uses the styling of the ``error`` admonition

   .. code-block:: rst

      .. md-admonition::
         :class: error

.. md-admonition:: Using a title
   :class: help

   This example uses the styling of the ``help`` admonition

   .. code-block:: rst

      .. md-admonition:: Using a title
         :class: help

.. hint::
   You can use the ``md-admonition`` directive in other themes by adding the theme's module to your
   ``extensions`` list in *conf.py*

   .. code-block:: python

      extensions = ["sphinx_immaterial.md_admonition"]

Custom admonitions
******************

If you want to add a custom admonition type, all you need is a color and an \*.svg icon.
Copy the icon's code from the `.icons <https://github.com/squidfunk/mkdocs-material/tree/master/material/.icons>`_
folder and add the new CSS to an additional style sheet.

.. md-tab-set::

   .. md-tab-item:: rST code

      .. code-block:: rst

         .. admonition:: Pied Piper
               :class: pied-piper

               Don't tell him you use spaces instead of tabs...

   .. md-tab-item:: CSS code

      .. code-block:: css
         :caption: docs/_static/extra_css.css

         :root {
           --md-admonition-icon--pied-piper: url('data:image/svg+xml;charset=utf-8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 576 512"><path d="M244 246c-3.2-2-6.3-2.9-10.1-2.9-6.6 0-12.6 3.2-19.3 3.7l1.7 4.9zm135.9 197.9c-19 0-64.1 9.5-79.9 19.8l6.9 45.1c35.7 6.1 70.1 3.6 106-9.8-4.8-10-23.5-55.1-33-55.1zM340.8 177c6.6 2.8 11.5 9.2 22.7 22.1 2-1.4 7.5-5.2 7.5-8.6 0-4.9-11.8-13.2-13.2-23 11.2-5.7 25.2-6 37.6-8.9 68.1-16.4 116.3-52.9 146.8-116.7C548.3 29.3 554 16.1 554.6 2l-2 2.6c-28.4 50-33 63.2-81.3 100-31.9 24.4-69.2 40.2-106.6 54.6l-6.3-.3v-21.8c-19.6 1.6-19.7-14.6-31.6-23-18.7 20.6-31.6 40.8-58.9 51.1-12.7 4.8-19.6 10-25.9 21.8 34.9-16.4 91.2-13.5 98.8-10zM555.5 0l-.6 1.1-.3.9.6-.6zm-59.2 382.1c-33.9-56.9-75.3-118.4-150-115.5l-.3-6c-1.1-13.5 32.8 3.2 35.1-31l-14.4 7.2c-19.8-45.7-8.6-54.3-65.5-54.3-14.7 0-26.7 1.7-41.4 4.6 2.9 18.6 2.2 36.7-10.9 50.3l19.5 5.5c-1.7 3.2-2.9 6.3-2.9 9.8 0 21 42.8 2.9 42.8 33.6 0 18.4-36.8 60.1-54.9 60.1-8 0-53.7-50-53.4-60.1l.3-4.6 52.3-11.5c13-2.6 12.3-22.7-2.9-22.7-3.7 0-43.1 9.2-49.4 10.6-2-5.2-7.5-14.1-13.8-14.1-3.2 0-6.3 3.2-9.5 4-9.2 2.6-31 2.9-21.5 20.1L15.9 298.5c-5.5 1.1-8.9 6.3-8.9 11.8 0 6 5.5 10.9 11.5 10.9 8 0 131.3-28.4 147.4-32.2 2.6 3.2 4.6 6.3 7.8 8.6 20.1 14.4 59.8 85.9 76.4 85.9 24.1 0 58-22.4 71.3-41.9 3.2-4.3 6.9-7.5 12.4-6.9.6 13.8-31.6 34.2-33 43.7-1.4 10.2-1 35.2-.3 41.1 26.7 8.1 52-3.6 77.9-2.9 4.3-21 10.6-41.9 9.8-63.5l-.3-9.5c-1.4-34.2-10.9-38.5-34.8-58.6-1.1-1.1-2.6-2.6-3.7-4 2.2-1.4 1.1-1 4.6-1.7 88.5 0 56.3 183.6 111.5 229.9 33.1-15 72.5-27.9 103.5-47.2-29-25.6-52.6-45.7-72.7-79.9zm-196.2 46.1v27.2l11.8-3.4-2.9-23.8zm-68.7-150.4l24.1 61.2 21-13.8-31.3-50.9zm84.4 154.9l2 12.4c9-1.5 58.4-6.6 58.4-14.1 0-1.4-.6-3.2-.9-4.6-26.8 0-36.9 3.8-59.5 6.3z"/></svg>')
         }
         .md-typeset .admonition.pied-piper {
           border-color: rgb(43, 155, 70);
         }
         .md-typeset .pied-piper > .admonition-title {
           background-color: rgba(43, 155, 70, 0.1);
           border-color: rgb(43, 155, 70);
         }
         .md-typeset .pied-piper > .admonition-title::before {
           background-color: rgb(43, 155, 70);
           -webkit-mask-image: var(--md-admonition-icon--pied-piper);
                 mask-image: var(--md-admonition-icon--pied-piper);
         }

   .. md-tab-item:: conf.py code

      .. code-block:: python

         html_static_path = ["_static"]
         html_css_files = ["extra_css.css"]


.. admonition:: Pied Piper
   :class: pied-piper

   Don't tell him you use spaces instead of tabs...
