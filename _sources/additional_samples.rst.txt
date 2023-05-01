==========================
``Additional`` ``Samples``
==========================


Various examples of styling applied to Sphinx constructs. You can
view the `source <./_sources/examples.txt>`_ of this page to see the specific
reStructuredText used to create these examples.

Headings
========
This is a first level heading (``h1``).

Sub-Heading
-----------
This is a second level heading (``h2``).

Sub-Sub-Heading
~~~~~~~~~~~~~~~
This is a third level heading (``h3``).


Code
====

.. rst-example::

   The theme uses pygments for ``inline code text`` and
   ::

      multiline
      code text

Here's an included example with line numbers.

.. rst-example::

   .. literalinclude:: ../sphinx_immaterial/apidoc/python/autodoc_property_type.py
      :caption: source from this theme in *sphinx_immaterial/apidoc/python/autodoc_property_type.py*
      :linenos:

It also works with existing Sphinx highlighting:

.. rst-example::

   .. code-block:: html

      <html>
        <body>Hello World</body>
      </html>

   .. code-block:: python

      def hello():
          """Greet."""
          return "Hello World"

   .. code-block:: javascript

      /**
      * Greet.
      */
      function hello(): {
          return "Hello World";
      }

Footnotes
=========

.. rst-example::

   I have footnoted a first item [#f1]_ and second item [#f2]_.
   This also references the second item [#f2]_.

   .. rubric:: Footnotes
   .. [#f1] My first footnote.
   .. [#f2] My second footnote.

Tables
======
Here are some examples of Sphinx
`tables <http://www.sphinx-doc.org/rest.html#rst-tables>`_. The Sphinx Material
all classes and only applies the default style to classless tables. If you want
to use a custom table class, you will need to do two thing. First, apply it
using ``.. cssclass:: custom-class`` and then add it to your configuration's
``table_classes`` variable.

Grid
----

.. rst-example:: A grid table:

   +------------------------+------------+----------+----------+
   | Header1                | Header2    | Header3  | Header4  |
   +========================+============+==========+==========+
   | row1, cell1            | cell2      | cell3    | cell4    |
   +------------------------+------------+----------+----------+
   | row2 ...               | ...        | ...      |          |
   +------------------------+------------+----------+----------+
   | ...                    | ...        | ...      |          |
   +------------------------+------------+----------+----------+


Simple
------

.. rst-example:: A simple table:

   =====  =====  =======
   H1     H2     H3
   =====  =====  =======
   cell1  cell2  cell3
   ...    ...    ...
   ...    ...    ...
   =====  =====  =======

User-styled Table
-----------------

.. note::

   ``table_classes`` is set to ``["plain"]`` in the site's configuration. Only plain
   remains as the class of the table. Other standard classes applied by Sphinx are
   removed.

   This is feature demonstration. There is no css for the plain class, and so
   this is completely unstyled.


.. rst-example::

   .. cssclass:: plain

   =====  ======  =======
   User   Styled  Table
   =====  ======  =======
   cell1  cell2   cell3
   ...    ...     ...
   ...    ...     ...
   =====  ======  =======

List Tables
-----------

.. rst-example::

   .. list-table:: A List Table
      :header-rows: 1

      * - Column 1
        - Column 2
      * - Item 1
        - Item 2

Alignment
~~~~~~~~~

.. rst-example::

   .. list-table:: Center Aligned
      :header-rows: 1
      :align: center

      * - Column 1
        - Column 2
      * - Item 1
        - Item 2


.. rst-example::

   .. list-table:: Right Aligned
      :widths: 15 10 30
      :header-rows: 1
      :align: right

      * - Treat
        - Quantity
        - Description
      * - Albatross
        - 2.99
        - On a stick!
      * - Crunchy Frog
        - 1.49
        - If we took the bones out
      * - Gannet Ripple
        - 1.99
        - On a stick!

Glossaries
==========

.. rst-example::

   .. glossary::

      environment
         A structure where information about all documents under the root is
         saved, and used for cross-referencing.  The environment is pickled
         after the parsing stage, so that successive runs only need to read
         and parse new and changed documents.

      source directory
         The directory which, including its subdirectories, contains all
         source files for one Sphinx project.

Math
====

.. rst-example::

   .. math::

      (a + b)^2 = a^2 + 2ab + b^2

      (a - b)^2 = a^2 - 2ab + b^2

.. rst-example::

   .. math::

      (a + b)^2  &=  (a + b)(a + b) \\
                 &=  a^2 + 2ab + b^2

.. rst-example::

   .. math::
      :nowrap:

      \begin{eqnarray}
         y    & = & ax^2 + bx + c \\
         f(x) & = & x^2 + 2xy + y^2
      \end{eqnarray}



Production Lists
================

The following `productionlist` is a modified example taken from
`the Graphviz documentation <https://graphviz.org/doc/info/lang.html>`_

.. rst-example:: Grammar for dot syntax

    .. productionlist::
       graph      : [ strict ] (`graph` | digraph) [ ID ] '{' `stmt_list` '}'
       stmt_list  : [ `stmt` [ ';' ] `stmt_list` ]
       stmt       : `node_stmt`
                  : `edge_stmt`
                  : `attr_stmt`
                  : ID '=' ID
                  : `subgraph`
       attr_stmt  : (`graph` | node | edge) `attr_list`
       attr_list  : '[' [ `a_list` ] ']' [ `attr_list` ]
       a_list     : ID '=' ID [ (';' | ',') ] [ `a_list` ]
       edge_stmt  : (`node_id` | `subgraph`) `edgeRHS` [ `attr_list` ]
       edgeRHS    : edgeop (`node_id` | `subgraph`) [ `edgeRHS` ]
       node_stmt  : `node_id` [ `attr_list` ]
       node_id    : ID [ `port` ]
       port       : ':' ID [ ':' `compass_pt` ]
                  : ':' `compass_pt`
       subgraph   : [ `subgraph` [ ID ] ] '{' `stmt_list` '}'
       compass_pt : (n | ne | e | se | s | sw | w | nw | c | _)

    This is a reference to the grammar for a :token:`graph` in dot syntax.

Sub-pages
=========

.. toctree::

   subpage1
   subpage2
