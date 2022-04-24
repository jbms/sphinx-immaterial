
Admonitions
===========

The theme uses the ``admonition`` directives for Sphinx admonitions.

rST and Sphinx
**************

Most of the admonitions that the mkdocs-material theme supports were "borrowed" from
admonitions defined in the reStructuredText specifications. You may recognize them from
usage in other sphinx-based themes. They are:

.. rst-example:: ``note``, ``todo``, ``seealso``

   .. seealso::
      This admonition is specific to Sphinx directives and not defined in the rST specifications
      as you can `seealso`.

      ``note`` and ``todo`` are admonitions defined by the rST specifications.

.. rst-example:: ``tip``, ``hint``, ``important``

   .. important::
      It is **important** to correctly use admonitions.

.. rst-example:: ``attention``, ``caution``, ``warning``

   .. warning::
      This is a **warning**.

.. rst-example:: ``danger``, ``error``

   .. error::
      You have made a grave **error**.

Admonitions from mkdocs-material
********************************

Some additional admonitions are supported via the source code from the mkdocs-material theme.
These admonitions can still be used, but the syntax is a little different because it relies
on the generic admonition defined in the reStructuredText specifications.

To use the following admonitions' styles from the mkdocs-material theme, the rST syntax is
shown to demonstrate using the ``:class:`` option of generic admonitions.

.. important::
   The ``:class:`` options below (in the rST code blocks) must use lower case letters for the
   styling to work. Otherwise, the admonition will look like a `note` (as that is the
   default fallback style).

.. rst-example:: ``todo``, ``info``

   .. admonition:: Info
      :class: info

      Thanks to the mkdocs-material theme, the ``todo`` class is also an alias of the
      ``info`` class when not using the `.. todo:: <todo>` directive.

.. rst-example:: ``abstract``, ``summary``, ``tldr``

   .. admonition:: TL;DR
      :class: tldr

      The ``:class: tldr`` part is important.

.. rst-example:: ``success``, ``check``, ``done``

   .. admonition:: Accomplished
      :class: done

      This style is used for ``success``, ``check``, ``done`` CSS classes.

.. rst-example:: ``question``, ``help``, ``faq``

   .. admonition:: FAQ
      :class: faq

      Helpful advice goes here.

.. rst-example:: ``failure``, ``fail``, ``missing``

   .. admonition:: Something Missing
      :class: missing

      We expected some loss of feature-coverage.

.. rst-example:: ``bug``

   .. admonition:: Known Bug
      :class: bug

      Bug reported data/conclusion.

.. rst-example:: ``example``

   .. admonition:: Example Admonition
      :class: example

      Example Body.

.. rst-example:: ``cite``, ``quote``

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

If the ``:class:`` option is not supplied to the ``details`` directive then the admonition
style falls back to a `note` admonition style.

.. rst-example::

   .. details:: Open by default
      :class: example
      :open:

      Use the ``:open:`` option as a flag to expand the admonition by default.

.. rst-example::

   .. details:: Closed by default
      :class: help

      Without the ``:open:`` flag, the admonition is collapsed by default.

Removing the title
******************

Since the mkdocs-material theme relies on a markdown extension that also allows removing the title
from an admonition, this theme has an added directive to do just that: ``md-admonition``.

The admonition's title can be removed if the ``md-admonition`` directive is not provided
any arguments. Because the ``md-admonition`` directive is an adaptation of the generic
``admonition`` directive, the ``class`` option is still respected.

.. rst-example::

   .. md-admonition::
      :class: error

      This example uses the styling of the ``error`` admonition

.. rst-example::

   .. md-admonition:: Using a title
      :class: help

      This example uses the styling of the ``help`` admonition

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
