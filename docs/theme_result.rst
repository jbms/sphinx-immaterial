Showcasing
==========

In developing the documentation for this theme, it became apparent that we needed a way to avoid
duplicating code samples to show both document source syntax and HTML rendering of the
document source code.

Introducing the :rst:dir:`rst-example` and :rst:dir:`myst-example` directives! To use these
directives, enable the :python:`"sphinx_immaterial.theme_result"` extension.

.. code-block:: python
    :caption: In conf.py

    extensions = [
        "sphinx_immaterial.theme_result",
    ]

.. bug::
    :title: Root-level syntax cannot be showcased
    :collapsible:

    Some syntax cannot be used as content to these directives. Specifically, any syntax that is
    expected to be at the document's root-level (without any parent blocks) will cause an error.
    For example, these directives cannot be used to showcase section titles or page breaks
    (:html:`<hr>`).

    .. code-block:: rst
        :caption: This causes a parsing error

        .. rst-example::

            Some Title
            ==========

            Some content that ends in a page break.

            ----

    The only way to showcase root-level syntax is to duplicate the code being showcased.
    You can also use raw :html:`<div>` elements to invoke this theme's CSS designed for
    showcasing syntax:

    .. md-tab-set::

        .. md-tab-item:: Markdown

            .. code-block:: rst

                <div class="results">

                ```md
                # Some Title

                And a page break.

                ----
                ```

                <div class="result">

                # Some Title

                And a page break.

                ----

                </div></div>

        .. md-tab-item:: reStructuredText

            .. code-block:: rst

                .. raw:: html

                    <div class="results">

                .. code-block:: rst

                    Some Title
                    ==========

                    And a page break.

                    ----

                .. raw:: html

                    <div class="result">

                Some Title
                ==========

                And a page break.

                ----

                .. raw:: html

                    </div></div>

.. rst:directive:: rst-example

    This directive takes reStructuredText code as content and generates

    .. task-list::
        :custom:

        1. A code block to showcase the reStructuredText syntax
        2. A decorated rendering of the given reStructuredText content

    This directive also takes 1 optional argument to be used as the caption for the
    generated code block.

    .. rst-example::
        :class: recursive-rst-example

        .. rst-example:: A showcase caption

            This example is actually *recursive*!

    .. rst:directive:option:: output-prefix

        This option allows separating the generated code block and rendered result with
        text for conciseness. If no value is given, then the default phrase is used
        "Which renders the following content:"

        .. md-tab-set::

            .. md-tab-item:: Using the default value

                .. rst-example::
                    :class: recursive-rst-example

                    .. rst-example::
                        :output-prefix:

                        The directive content to showcase.

            .. md-tab-item:: Using a custom value

                .. rst-example::
                    :class: recursive-rst-example

                    .. rst-example::
                        :output-prefix: The above code renders the following result:

                        The directive content to showcase.

    .. rst:directive:option:: class

        This option allows specifying a list of space-separated CSS classes.

        Fun fact: This option was used to demonstrate using a self-hosted :themeconf:`font`.

        .. rst-example::
            :class: recursive-rst-example

            .. rst-example::
                :class: custom-font-example

                This text is just an **example**.
                *Notice* the font family used is different (monospaced) in the code snippet.

        .. example::
            :collapsible:

            This option was also used to add padding to this page's recursive examples'
            rendered output.

            .. code-block:: rst

                .. rst-example::
                    :class: recursive-rst-example

            .. literalinclude:: _static/extra_css.css
                :language: css
                :start-at: /* style for recursive rst-example rendering */
                :end-before: /* ************************* animated-admonition-border style

    .. rst:directive:option:: name

        This option allows specifying an id to use for cross-referencing. Ultimately, it adds
        an ``id`` attribute for the rendered HTML element.

        .. rst-example::
            :class: recursive-rst-example

            .. rst-example::
                :name: ref-this-example

                A :ref:`cross-reference link to this example <ref-this-example>`.


.. rst:directive:: myst-example

    This is really just an alias of the :rst:dir:`rst-example` for readability
    in markdown document sources. It is meant to be used with Markdown code as
    content instead of reStructuredText.

    .. warning::
        Markdown syntax is really only parsed when this directive is used from within a
        Markdown file. If this directive is invoked within a reStructuredText file,
        then the given content is parsed as reStructuredText syntax.

        Since this page's source code is written in reStructuredText, no markdown examples
        can be showcased here properly. See :doc:`myst_typography` as those example snippets
        all use this directive.

    All options from the :rst:dir:`rst-example` directive are also available in this directive.
    The optional directive argument is also available with this directive.
    Please refer to the documented directive options and optional argument above.

    An example (using all directive options and an argument as documented above) written in
    :external:doc:`MyST syntax <syntax/roles-and-directives>`
    would look like the following:

    .. code-block:: md

        ```{myst-example} A showcase caption
        :output-prefix: Which renders the following content:
        :class: custom-css-class
        :name: reference-this-example

        This directive __content__ will be
        rendered as a `code snippet` with
        **decorated** results.
        ```
