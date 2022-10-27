Code Annotations
================

A special directive was created to make use of the mkdocs-material theme's
`Code Annotations <https://squidfunk.github.io/mkdocs-material/reference/code-blocks/#adding-annotations>`_
feature.

.. rst:directive:: code-annotations

    This directive shall hold an :duref:`enumerated list <enumerated-lists>` of annotations that can be used in a
    `code-block` immediately prior to this directive. The given list will not be rendered in the
    generated output (even if there is no code snippet to annotate). Additionally, all annotations will be
    excluded when using the "copy to clipboard" button for an annotated `code-block`; the annotated
    comments' text will still be copied (if not `Hiding the annotated comment`_).

    An error will be shown in the build log if the given list is not recognized as an
    :duref:`enumerated list <enumerated-lists>`.

    .. note::
        When using this directive the :python:`"content.code.annotate"` does not need to be
        specified in the :themeconf:`features` list.

Using annotations
*****************

Each annotation in the code snippet should be a comment starting with the identifying number
(in parenthesis) of the corresponding annotation specified in the list of
:rst:dir:`code-annotations`.

.. note::
    Remember to specify the language syntax for pygments to highlight the `code-block`. Without
    this information, pygments may incorrectly identify comments in a `code-block` which is
    required for the detection of annotations.

.. hint::
    All annotations are hyperlinked. This means you can right click the annotation's button and
    open it as a link in a new tab (or copy the link to sharing).

.. warning::
    Using the same annotation for multiple comments will essentially turn all but the last button
    into hyperlinks to the last button.

.. rst-example:: Example of code annotations

    .. code-block:: python

        html_theme_options = {
            "features" : [
                "content.code.annotate"  # (1)
            ],
        }

    .. code-annotations::
        1. .. admonition:: Obsolete
               :class: failure

               This has no special effect because the :rst:dir:`code-annotations` directive
               automatically enables the feature.

:duref:`Enumerated lists' <enumerated-lists>` markers in reStructuredText can be uniformed with the
``#`` character instead of numbers/letters.

.. rst-example:: 

    .. code-block:: cpp

        // (1)
        /* (2) */
    
    .. code-annotations::
        #. These annotations can have anything that Sphinx supports:
           
           .. image:: desert-flower.jpg
        #. Indentation for lists' items that span multiple lines can
           be tricky in reStructuredText.

           0. First item in a nested list that starts with ``0``.
           #. Checkout the `sphinxemoji <https://sphinxemojicodes.rtfd.io>`_ extension to
              put emojis here.

Hiding the annotated comment
----------------------------

The annotated comment can be hidden in the `code-block` if the annotation's identifying number
ends with a exclamation mark (``!``) after the closing parenthesis.

.. rst-example::

    .. code-block:: cmake
        :caption: Erroneous example!
        :linenos:

        # (1)! remove me

        # (2)! (3) remove me
    
        # (4) some text   (5)! remove me
    
    .. code-annotations::
        1. I'm the first annotation.
        2. I'm the second annotation.
        3. Nothing to see here because it won't be rendered.
        4. I'm the forth annotation.
        5. I'm the fifth annotation.

.. admonition:: Limitations
    :class: bug

    For technical reasons, this hiding mechanism will only work with 1 annotation per code comment.
    In the above example, you should notice that, on line 3, the third annotation is removed
    because the second annotation has the ``!`` appended in the comment. And all text is removed
    from the third comment, on line 5, because the fifth annotation has the ``!`` appended to it.

Custom tooltip width
--------------------

For annotations with an excess of content,it might be desirable to change the width of the
annotations' tooltip using by changing the following CSS variable:

.. code-block:: css

    :root {
      --md-tooltip-width: 600px;
    }

With the above CSS changes, a tooltip would be rendered like so:

.. rst-example::
    :class: very-large-tooltip

    .. code-block:: yaml

        # (1)!

    .. code-annotations::
        1. Muuuuuuuuuuuuuuuuuuuuuuuuuuuuch more space!

Annotation buttons with numbers
-------------------------------

The mkdocs-material legacy behavior was to use the annotation items list number in the button
that was rendered. To enable this, use the following custom CSS rules:

.. code-block:: css

    .md-typeset .md-annotation__index > ::before {
      content: attr(data-md-annotation-id);
    }
    .md-typeset :focus-within > .md-annotation__index > ::before {
      transform: none;
    }

Using the above CSS would render annotations like so:

.. rst-example::
    :class: annotated-with-numbers

    .. code-block:: python

        def my_func(param)  # (1)!
            """A doc string."""
            return param + 1  # (2)!

    .. code-annotations::
        1. Data goes in here.
        2. Data comes out here.
