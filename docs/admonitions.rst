
Admonitions
===========

This theme uses the `Admonition Directive`_ for Sphinx admonitions.

.. _predefined_admonitions:

rST and Sphinx
**************

Most of the admonitions that the mkdocs-material theme supports were "borrowed" from
admonitions defined in the reStructuredText specifications. You may recognize them from
usage in other sphinx-based themes.

.. rst-example:: ``note``, ``seealso``, ``todo``
   :name: note-style

   .. seealso::
      This admonition is specific to Sphinx directives and not defined in the reStructuredText
      specifications as you can `seealso`. The `todo` admonition is also defined as an extension
      that is distributed with Sphinx.

      The :dutree:`note` admonition *is* defined by the reStructuredText specifications.

.. rst-example:: ``tip``, ``hint``, ``important``
   :name: important-style

   .. important::
      It is :dutree:`important` to correctly use admonitions.

.. rst-example:: ``attention``, ``caution``, ``warning``
   :name: attention-style caution-style warning-style

   .. warning::
      This is a :dutree:`warning`.

.. rst-example:: ``danger``, ``error``
   :name: error-style

   .. error::
      You have made a grave :dutree:`error`.

.. _inherited_admonitions:

Admonitions from mkdocs-material
********************************

Some additional admonitions are supported via the CSS styles inherited from the mkdocs-material
theme. These admonition styles can be used via the :rst:dir:`admonition` directive's :rst:`:class:`
option. 

.. confval:: sphinx_immaterial_generate_inherited_admonitions

   The inherited admonition styles are conveniently exposed as directives in the sphinx-immaterial
   theme using the `Custom Admonitions`_ feature. Set this config option to :python:`False` to
   disallow the generation of these convenience directives.

   .. code-block:: python
      :caption: in conf.py

      sphinx_immaterial_generate_inherited_admonitions = False

.. rst-example:: :css:`info`
   :name: info-style

   .. si-info::

      Some admonished information.

.. rst-example:: :css:`abstract`
   :name: abstract-style

   .. si-abstract::

      An abstract statement.

.. rst-example:: :css:`success`
   :name: success-style

   .. si-success::

      This style is used for :css:`success` CSS class.

.. rst-example:: :css:`question`
   :name: question-style

   .. si-question::

      Helpful advice goes here.

.. rst-example:: :css:`failure`
   :name: failure-style

   .. si-failure::

      We expected some loss of feature-coverage.

.. rst-example:: :css:`bug`
   :name: bug-style

   .. si-bug::

      Bug reported data/conclusion.

.. rst-example:: :css:`example`
   :name: example-style

   .. si-example::

      Example Body.

.. rst-example:: :css:`quote`
   :name: quote-style

   .. si-quote::

      Somebody somewhere said something catchy.

Admonition Directive
*********************

All admonitions listed above are created or overridden by this theme's `Custom Admonitions`_ feature.
This means that the following options are available to all admonitions.

.. rst:directive:: admonition

   This directive was overridden from the :dudir:`docutils definition <generic-admonition>`.
   The only difference (aside from the added options listed below) is that the
   inherently required argument used for a title has been made optional.

   .. rst:directive:option:: title

      This option provides an alternative for custom titles in admonitions defined in
      `rST and Sphinx`_ because they don't accept any directive arguments. When used with the
      generic :rst:dir:`admonition` and the inherited `Admonitions from mkdocs-material`_, the
      value for this option is concatenated with a title given as a directive argument.

      The :rst:`:no-title:` option will supersede any given title.

      .. rst-example:: Equivalent ways to customize the admonition's title.

         .. tip::
            :title: A custom title specified in the directive's :rst:`:title:` option.

            The :dutree:`tip` directive accepts no arguments.

         .. admonition:: A custom title specified in the directive's *argument*.

            The default style for the generic admonition is that of the `note admonition <note-style>`.

         .. example-admonition:: A custom title specified in both the
            :title: directive's *argument* and :rst:`:title:` option.
               It can even span multiple lines.

            Notice the blank line between the directive's beginning block and this content block.

            This admonition's directive was created just for this documentation using the
            sphinx-immaterial theme's `Custom Admonitions`_ feature.

   .. rst:directive:option:: no-title

      This flag will skip rendering the admonition's title. Coincidentally, this option will
      invoke the same behavior of a generic :rst:dir:`admonition` without an argument provided.

      The :rst:`:collapsible:` option will cause the :rst:`:no-title:` to be ignored.

      .. rst-example:: Equivalent ways to exclude rendering the title

         .. admonition::

            This *generic* admonition uses the styling of the `note admonition <note-style>`.

         .. si-success::
            :no-title:

            This *specific* admonition uses the styling of the `success admonition <success-style>`

   .. rst:directive:option:: collapsible

      This option can be used to convert the rendered admonition into a collapsible HTML
      ``<details>`` element. A value of ``open`` will make the admonition expanded by default.
      Any other value is ignored and will make the admonition collapsed by default.

      .. rst-example::

         .. si-example:: Opened by default
            :collapsible: open

            Hide me.

         .. si-question:: Closed by default.
            :collapsible:

            Found me.

   .. rst:directive:option:: name

      Set this option with a qualified ID to reference the admonition from
      other parts of the documentation using the `ref` role.

      .. rst-example::

         .. si-quote:: Referencing an Admonition
            :name: my-admonition

            A reference to :ref:`this admonition <my-admonition>`

   .. rst:directive:option:: class

      If further CSS styling is needed, then use this option to append a CSS
      class name to the rendered HTML elements.

      .. rst-example::

         .. admonition::
            :class: animated-admonition-border

            .. literalinclude:: _static/extra_css.css
               :language: css
               :caption: docs/_static/extra_css.css
               :start-after: /* ************************* animated-admonition-border style
               :end-before: /* ************************* my-special-key style

Custom Admonitions
******************

This theme offers a robust solution that allows user-defined custom admonitions from the
documentation's conf.py.

.. confval:: sphinx_immaterial_custom_admonitions

   A `list` of `dict`\ s that will be used to create custom admonition directives. Each `dict`
   is validated using the data class `CustomAdmonitionConfig`.

   .. autoclass:: sphinx_immaterial.custom_admonitions.CustomAdmonitionConfig
      :exclude-members: __new__

Custom Admonition Example
-------------------------

As a demonstration, we will be using the following configuration:

.. literalinclude:: conf.py
   :language: python
   :start-after: # BEGIN CUSTOM ADMONITIONS
   :end-before: # END CUSTOM ADMONITIONS
   :name: custom-admonition-example-config

Note that the name of the created directive (:rst:dir:`example-admonition`) is directly related to
the value of the
:py:obj:`~sphinx_immaterial.custom_admonitions.CustomAdmonitionConfig.__init__.name` option.

The above configuration will create a directive that could be documented like so:

.. rst:directive:: example-admonition

   A custom admonition created from the
   `example's configuration <custom-admonition-example-config>`.
   See the :rst:dir:`admonition` directive for all available options and examples.

   .. rst-example::

      .. example-admonition::

         This is simple a example.


.. si-example:: Legacy approach inherited from the mkdocs-material theme.
   :collapsible:

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

.. warning::
   The approach described below will work because it is inherited from the mkdocs-material theme.
   However, using this approach will lead to bloated HTML files as the needed CSS code is embedded
   in ``<style>`` tags rather than a single CSS file.

   The sphinx-immaterial theme offers `custom admonitions`_ as a more efficient alternative.

Any of the above builtin admonitions' icons can be changed using the
:themeconf:`icon`\ [:themeconf:`admonition`] field in :confval:`html_theme_options` settings.
This will only work with `any of the icons bundled with this theme
<https://github.com/squidfunk/mkdocs-material/tree/master/material/.icons>`_.

.. code-block:: python
   :caption: Changing the `note` icon in conf.py

   html_theme_options = {
       "icon": {
           "admonition": {
               "note": "material/file-document-outline", # (1)!
           },
       },
   }

.. code-annotations::
   #. Uses the icon :si-icon:`material/file-document-outline`


.. si-example:: Alternate icon sets
   :collapsible:

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
