Formatting signatures
=====================

This theme provides two alternative ways to automatically format/indent API
documentation signatures.

CSS-based function parameter wrapping
-------------------------------------

There is a CSS-based formatting rule that can be enabled for long function
signatures that displays each function parameter on a separate line.  This is
enabled by default, and works fairly well for Python signatures.

.. confval:: html_wrap_signatures_with_css

   Specifies for which `Sphinx domains
   <https://www.sphinx-doc.org/en/master/usage/restructuredtext/domains.html>`__
   this CSS-based formatting is enabled.

   Supported types are:

   :py:obj:`bool`
       If `True`, enable CSS-based formatting for all domains.  If `False`,
       disable CSS-based formatting for all domains.

   :py:obj:`list[str]`
       List of domains for which to enable CSS-based formatting.

   The default value is :python:`True`

.. confval:: html_wrap_signatures_with_css_column_limit

   Maximum signature length before function parameters are displayed on separate
   lines.

   Only applies to domains for which :confval:`html_wrap_signatures_with_css` is
   enabled.

   The default value is :python:`68`.

.. rst-example::

   .. py:function:: long_function_signature_example(\
                      name: int, \
                      other_param: list[str], \
                      yet_another: bool = False, \
                      finally_another: str = "some long string goes here"\
                    ) -> Tuple[A, Very, Long, Return, Type]

clang-format-based function parameter wrapping
-----------------------------------------------

There is a more powerful alternative formatting mechanism based on `clang-format
<https://clang.llvm.org/docs/ClangFormat.html>`__.  This supports C, C++, Java,
JavaScript, Objective-C, and C#.

This functionality is available as a separate extension included with this
theme.  To use it, you must include it in your conf.py file and you must also
set the :confval:`clang_format_signatures_domain_styles` configuration option.

.. code-block:: python

    extensions = [
        # other extensions...
        "sphinx_immaterial.format_signatures",
    ]

    clang_format_signatures_domain_styles = {
        "cpp": """{
        BasedOnStyle: LLVM,
        ColumnLimit: 68,
        }""",
    }

.. confval:: clang_format_signatures_domain_styles

   Dictionary that specifies the `clang-format style options
   <https://clang.llvm.org/docs/ClangFormatStyleOptions.html>`__ for each
   domain.  Formatting is enabled *only* for domains that are listed.

   .. literalinclude:: conf.py
      :language: python
      :start-after: # BEGIN: sphinx_immaterial.format_signatures extension options
      :end-before: # END: sphinx_immaterial.format_signatures extension options

   When specifying an inline style (as opposed to a predefined style), it is
   necessary to enclose the style in curly braces, as in the example above.
   Since the predefined styles (such as ``Google``, ``LLVM``, etc.) do not use a
   column limit of 68, it is not recommended to use a predefined style.

   .. tip::

      It is recommended to include ``ColumnLimit: 68`` as a style option.  This
      is the default for the CSS-based wrapping, and is the number of characters
      that fit under typical display settings with both left and right side bars
      displayed.

   .. warning::

      Due to how this extension is implemented, style options that change
      non-whitespace characters, such as setting ``QualifierAlignment`` to a
      value other than ``Leave``, must not be used (if non-whitespace characters
      are changed, the extension will raise an exception and the documentation
      build will fail).

.. confval:: clang_format_command

   Name of ``clang-format`` executable.  May either be a plain filename, in
   which case normal ``PATH`` resolution applies, or a path to the executable.

   To ensure that a consistent version of ``clang-format`` is available when
   building your documentation, add the `clang-format PyPI package
   <https://pypi.org/project/clang-format/>`__ as a dependency.

.. rst-example::

   .. cpp:function:: template <typename T, \
                               typename U = void, \
                               int AnotherParameter = 42> \
                     requires std::is_const_v<T> \
                     const MyType LongFunctionSignatureExample(\
                       const MyType bar, \
                       uint8_t* arr, \
                       unsigned int len = DEFAULT_LENGTH, \
                       bool baz = false);

      Some function type thing
