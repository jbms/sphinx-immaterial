Code Annotations
================

A special directive was created to make use of the mkdocs-material theme's
`Code Annotations <https://squidfunk.github.io/mkdocs-material/reference/code-blocks/#adding-annotations>`_
feature.

.. rst:directive:: code-annotations

    This directive shall hold an :duref:`enumerated list <enumerated-lists>` of annotations that can be used in a
    `code-block` immediately prior to this directive. The given list will not be rendered in the
    generated output (even if there is no code snippet to annotate).

    :throws: A `ValueError` will be raised if the given list is not recognized as a
        :duref:`enumerated list <enumerated-lists>`.

    .. note::
        When using this directive the :python:`"content.code.annotate"` does not need to be
        specified in the :themeconf:`features` list.

Usage
*****

Each annotation in the code snippet should be comment starting with the identifying number
(in parenthesis) of the corresponding annotation specified in the list of
:rst:dir:`code-annotations`.

.. rst-example:: Example of code annotations

    .. code-block:: python

        html_theme_options = {
            "features" : [
                "content.code.annotate"  # (1)!
            ],
        }

    .. code-annotations::
        1. .. admonition:: Obsolete
               :class: failure

               This has no special affect because the :rst:dir:`code-annotations` directive already
               enables the feature accordingly.

.. rst-example:: rST ordered lists' markers are normalized according to nested level

    .. code-block:: yaml
        :linenos:

        name: Build # (1)
        # (2)
    
    .. code-annotations::
        A. The display name of the workflow
        B. 1. first item in a nested ordered list
           2. second item in a nested ordered list.

Custom tooltip width
--------------------

For annotations with an excess of content,it might be desirable to change the width of the
annotations' tooltip using by changing the following CSS variable:

.. code-block:: css

    :root {
      --md-tooltip-width: 600px;
    }


Annotation buttons with numbers
-------------------------------

The mkdocs-material legacy behavior waas to use the anotation items list number in the button
that was rendered. To enable this, use the following custom CSS rules:

.. code-block:: css

    .md-typeset .md-annotation__index > ::before {
      content: attr(data-md-annotation-id);
    }
    .md-typeset :focus-within > .md-annotation__index > ::before {
      transform: none;
    }
