Graphviz
========

This theme adds several improvements to the built-in :py:mod:`sphinx.ext.graphviz` extension:

- default fonts and colors are set to match the fonts and colors used by the
  theme, including support for both light and dark mode;

  .. admonition:: Only compatible with Google fonts

      When not using a Google font via :themeconf:`font` in conf.py (eg. using a
      system/custom/self-hosted font), this extension will use the metrics from Graphviz's
      default font, rather than the actual font, for the purpose of computing the graph layout.
      However, the text will still be displayed in the browser using the user-specified font.

- the rendered diagram is included as inline svg content to allow hyperlinks to
  work;

- colors can be manually specified in terms of CSS variables defined by the
  theme, such as :css:`var(--md-primary-fg-color)`;

- labels can be specified as Sphinx cross references (rather than just plain
  URLs).

Configuration
-------------

This functionality is available as a separate optional extension included with
this theme, which must be specified manually in your :file:`conf.py` file:

.. code-block:: python

    extensions = [
        "sphinx_immaterial",
        # other extensions...
        "sphinx_immaterial.graphviz",
    ]

The :confval:`graphviz_dot` and :confval:`graphviz_dot_args` configuration
options from :py:mod:`sphinx.ext.graphviz` are supported.

.. note::

   The :confval:`graphviz_output_format` configuration option is not supported;
   instead, the graph is always included as inline SVG in the HTML output.

.. confval:: graphviz_ignore_incorrect_font_metrics

   This extension relies on the LibGD graphviz plugin to load the same font used
   by this theme, in order to correctly determine the size of text labels.
   While the LibGD plugin is normally included in the Linux and macOS graphviz
   builds, the official x86_64 Windows build does not include it (before graphviz
   v12.1.0).  If the plugin is not found, by default this theme logs a warning.
   This option may be set to :python:`True` silence that warning.

   .. code-block:: python
      :caption: Add to :file:`conf.py` to silence the warning

      graphviz_ignore_incorrect_font_metrics = True

   .. warning::

      If LibGD is not available, graphviz will compute the size of labels using
      a default system font.  Labels will still be rendered in the browser using
      the correct font; the layout may just be slightly incorrect.

Usage
-----

Using the :rst:dir:`graphviz` directive, graphs can be specified either inline
or included from an external file.

.. rst-example:: Example of a graph defined inline

   .. graphviz::

      digraph {
        graph [
          rankdir = LR
        ]

        node [
          shape=rectangle
        ]

        A [label="Start"]
        B [label="Error?", shape=diamond]
        C [
          label="Hmm...",
          style="solid,filled",
          fillcolor="var(--md-primary-fg-color, green)"
        ]
        D [label="Debug"]
        E [xref=":py:obj:`~tensorstore_demo.DimensionSelection`"]

        A -> B
        B -> C [label="Yes"]
        C -> D
        D -> B
        B -> E [label="No"]
        D -> E [style=invis]
      }

.. literalinclude:: test.dot
   :language: dot
   :caption: Contents of :file:`test.dot`

.. rst-example:: Example of a graph defined in an external file

   .. graphviz:: test.dot

Colors specified using CSS variables
------------------------------------

As demonstrated in the example above, this extension adds support for specifying
color attributes using the CSS syntax :dot:`"var(--css-var)"` or
:dot:`"var(--css-var, fallback)"`.  This may be used to specify colors defined
by the theme that vary depending on whether light or dark mode is enabled.  When
the :py:obj:`latex builder<sphinx.builders.latex.LaTeXBuilder>` is used, the
fallback color, if specified, will be used instead.  If no fallback value is
specified, only HTML builders may be used.

Cross-references
----------------

This extension adds support for a special ``xref`` attribute, which may be set
to a string value containing reStructuredText.  This is demonstrated in the
example above.

The reStructuredText will be parsed as a document fragment, and after resolving any cross references,
will be substituted back into the graph definition as follows:

- A :graphvizattr:`label` will be generated from the parsed fragment's text content.
- If the parsed fragment contains at least one hyperlink, only the last such hyperlink is
  considered, and:

  - an :graphvizattr:`href` will be generated from its URL.
  - a :graphvizattr:`tooltip` will be generated from its title/tooltip, if any.
  - a :graphvizattr:`target` will be generated from its target, if any.

Overriding the cross-reference label
************************************

The :graphvizattr:`label` generated with the new ``xref`` attribute uses graphviz' HTML-like
attribute syntax, but any HTML characters found within the ``xref`` parsed fragments' text are
escaped (eg. ``< f0 >`` becomes ``&lt; f0 &gt;``).
In some graphs, it is preferable to use unescaped HTML characters in the :graphvizattr:`label`.
In this case, the generated :graphvizattr:`label` can be overridden by manually specifying the
:graphvizattr:`label` after the ``xref`` attribute.

.. rst-example:: A graph of record nodes

   .. graphviz::

      digraph {
          graph [rankdir = "LR"]
          module [
              xref=":py:mod:`test_py_module.test`"
              label="<f0> test_py_module.test | <f1> functions | <f2> classes"
              shape = record
          ]
          class [
              xref = ":py:class:`test_py_module.test.Foo`"
              label = "<f0> Foo | <f1> attributes | <f2> methods"
              shape = record
          ]
          method [
              xref = ":py:meth:`test_py_module.test.Foo.capitalize()`"
              label = "<f0> capitalize() | <f1> variables"
              shape = record
          ]
          function [
              xref = ":py:func:`test_py_module.test.func()`"
              label = "<f0> func() | <f1> variables"
              shape = record
          ]
          class_attr [
              // NOTE: cannot adequately angle brackets in xref's text
              xref = ":py:attr:`spam | object <test_py_module.test.Foo.spam>`"
              shape = record
          ]
          module:f2 -> class:f0
          module:f1 -> function:f0
          class:f2 -> method:f0
          class:f1 -> class_attr // edge will point toward center of class_attr
      }

.. info:: Implementation note

   Using a cross reference in a single field of a record node (with multiple fields) is unsupported
   because the manually specified :graphvizattr:`label` is used as is.
