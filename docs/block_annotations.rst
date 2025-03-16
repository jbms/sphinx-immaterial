
Block Annotations
=================

The sphinx-immaterial theme has support for adding annotations to block level document elements.
To do this, we will use the :dudir:`class` which is re-exported by sphinx as ``rst-class``.

.. important::

    Please read the :dudir:`class` documentation to better understand how Sphinx'
    ``rst-class`` directive works.

.. seealso::
    A special directive is needed to produce :rst:dir:`code-annotations`.

Annotating paragraphs
---------------------

The first block-level element that follows a ``rst-class`` directive (without directive content)
is appended with the ``annotate`` class.

.. rst-example::

    .. rst-class:: annotate

    An annotated paragraph. (1)

    An unannotated paragraph. (2)

    1. I'm an annotation! I can contain ``code``, *formatted text*, images, ...
       basically anything that can be used. :si-icon:`material/emoticon-happy`
    2. This won't show.

When the ``rst-class`` is given content, then all blocks within the content are
appended with the ``annotate`` class.

.. rst-example::

    .. rst-class:: annotate

        First paragraph (1)

        Second paragraph (2)

    1. I'm an annotation!
    2. I'm an annotation as well!

Annotating lists
----------------

Lists can be annotated as well. Beware that lists are typically started and ended with a blank line.
So, consecutive lists (as in the case of annotating lists) might look odd.

.. rst-example::

    .. rst-class:: annotate

    1. An ordered list item (1)

       1. A nested list does not need to end in a blank line.
    2. A second list item (2)

    1. I'm an annotation!
    2. I'm an annotation as well!

Nested annotations
******************

Nested annotations can be done as well, although the indentation gets tricky.
Beware that the paragraph within the annotated list must also be flagged with
``.. rst-class:: annotate``, otherwise the nested annotation will just appear
as a nested list.

.. rst-example::

    .. rst-class:: annotate

    Lorem ipsum dolor sit amet, (1) consectetur adipiscing elit.

    1. .. rst-class:: annotate

       I'm an annotation! (1)

       1. I'm an annotation as well!

Annotating admonitions
----------------------

The :rst:dir:`admonition` directives already contain an option to specify CSS classes.
Therefore, we don't need to use the ``rst-class`` directive for admonitions.
Instead, we can just add the ``annotate`` class to the admonition's :rst:`:class:` option.

.. rst-example::

    .. note::
        :title: Phasellus posuere in sem ut cursus (1)
        :class: annotate

        Lorem ipsum dolor sit amet, (2) consectetur adipiscing elit. Nulla et
        euismod nulla. Curabitur feugiat, tortor non consequat finibus, justo
        purus auctor massa, nec semper lorem quam in massa.

    1. I'm an annotation!
    2. I'm an annotation as well!

Annotating tabbed content
-------------------------

Here is a simple example of `annotating paragraphs`_ within tabbed content
(using :doc:`content_tabs`).

.. rst-example::

    .. md-tab-set::

        .. md-tab-item:: Tab 1

            .. rst-class:: annotate

            Lorem ipsum dolor sit amet, (1) consectetur adipiscing elit.

            1. I'm an annotation!

        .. md-tab-item:: Tab 2

            .. rst-class:: annotate

            Phasellus posuere in sem ut cursus (1)

            1. I'm an annotation as well!

Annotating blockquotes
----------------------

There is a noteworthy clash between the syntax for :duref:`block-quotes` versus the :dudir:`class`.
The suggested workaround is a single rST comment immediately after the ``rst-class`` invocation.

.. rst-example::

    .. rst-class:: annotate
    ..

        A blockquote with an annotation. (1)

    1. I'm an annotation!

.. info:: Implementation Detail
    :collapsible:

    The ``rst-class`` directive is not given any content in the example above.
    The empty comment :rst:`..` (followed by a blank line) implicitly signifies this to the rST parser.

    If we instead provide a blockquote as the sole content to the ``rst-class`` directive,
    then indentation is normalized by the rST parser and the blockquote is
    interpreted as a simple paragraph.

    .. rst-example:: A blockquote as sole directive content *does not work*

        .. rst-class:: annotate

                A blockquote (normalized to a paragraph) with an annotation. (1)

        1. I'm an annotation!

    Using a blockquote as subsequent content preserves the indentation needed to satisfy
    the :duref:`block-quotes` specification.

    .. rst-example:: A blockquote as subsequent directive content *can work*

        .. rst-class:: annotate

            An annotated paragraph (1) which does not get annotated by the JS implementation.

                A blockquote with an annotation. (2)

        1. I'm an annotation!
        2. I'm an annotation as well!
