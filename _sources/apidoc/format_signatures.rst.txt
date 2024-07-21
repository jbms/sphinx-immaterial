Formatting signatures
=====================

This theme provides two alternative ways to automatically format/indent API
documentation signatures.

CSS-based function parameter wrapping
-------------------------------------

There is a CSS-based formatting rule that can be enabled for long function
signatures that displays each function parameter on a separate line.  This is
enabled by default, and works fairly well for Python signatures.

It is controlled by the following `object description
options<object-description-options>`:

.. objconf:: wrap_signatures_with_css

   Indicates whether CSS-based formatting is enabled.  Disabled automatically if
   :objconf:`clang_format_style` is specified.

.. objconf:: wrap_signatures_column_limit

   Maximum signature length before function parameters are displayed on separate
   lines.

   Only applies if :objconf:`wrap_signatures_with_css` is set to :python:`True`,
   or if :objconf:`clang_format_style` is enabled and does not specify a
   ``ColumnLimit`` value.

   The default value is :python:`68`.  This is the number of characters that fit
   under typical display settings with both left and right side bars displayed.

For example, to disable this option for every domain except ``py``, add the
following to :file:`conf.py`:

.. code-block:: python

   object_description_options = [
       (".*", dict(wrap_signatures_with_css=False)),
       ("py:.*", dict(wrap_signatures_with_css=True)),
   ]

.. rst-example:: CSS-based wrapping of Python signature

   .. py:function:: long_function_signature_example(\
                      name: int, \
                      other_param: list[str], \
                      yet_another: bool = False, \
                      finally_another: str = "some long string goes here"\
                    ) -> Tuple[str, bool, float, bytes, int]

External code formatter integration
-----------------------------------

There is a more powerful alternative formatting mechanism that makes use of
external code formatters.

.. warning::

   The LaTeX builder is supported. However, the spacing may not always line up correctly
   because the Latex builder does not use a monospace font for the entire signature.

clang-format
^^^^^^^^^^^^

The `clang-format <https://clang.llvm.org/docs/ClangFormat.html>`__ integration
supports C, C++, Java, JavaScript, Objective-C, and C#.

This functionality is available as a separate extension included with this
theme.  To use it, you must include it in your :file:`conf.py` file and you must
also specify the :objconf:`clang_format_style` option for the object types for
which the extension should be used.

.. code-block:: python

    extensions = [
        # other extensions...
        "sphinx_immaterial.apidoc.format_signatures",
    ]

    object_description_options = [
        # ...
        ("cpp:.*", dict(clang_format_style={"BasedOnStyle": "LLVM"})),
    ]

.. objconf:: clang_format_style

   Specifies the `clang-format style options
   <https://clang.llvm.org/docs/ClangFormatStyleOptions.html>`__ as a
   :python:`dict` (JSON object), or :python:`None` to disable clang-format.

   If the style does not explicitly specify a ``ColumnLimit``, the value of
   :objconf:`wrap_signatures_column_limit` is used.

   .. warning::

      Due to how this extension is implemented, style options that change
      non-whitespace characters, such as setting ``QualifierAlignment`` to a
      value other than ``Leave``, must not be used (if non-whitespace characters
      are changed, the extension will raise an exception and the documentation
      build will fail).

.. confval:: clang_format_command

   Name of ``clang-format`` executable.  May either be a plain filename, in
   which case normal ``PATH`` resolution applies, or a path to the executable.
   Defaults to :python:`"clang-format"`.

   To ensure that a consistent version of ``clang-format`` is available when
   building your documentation, add the `clang-format PyPI package
   <https://pypi.org/project/clang-format/>`__ as a dependency, or depend on the
   ``clang-format`` optional feature of this package:

   .. code-block:: shell

      pip install sphinx-immaterial[clang-format]

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

black
^^^^^

The `Black <https://github.com/psf/black>`__ integration supports Python.

This functionality is available as a separate extension included with this
theme.  To use it, you must include it in your :file:`conf.py` file and you must
also specify the :objconf:`black_format_style` option for the object types for
which the extension should be used.

.. code-block:: python

    extensions = [
        # other extensions...
        "sphinx_immaterial.apidoc.format_signatures",
    ]

    object_description_options = [
        # ...
        ("py:.*", dict(black_format_style={"line_length": 60})),
    ]

.. objconf:: black_format_style

   Specifies style options for black, or :python:`None` to disable black.

   If the style does not explicitly specify a ``line_length``, the value of
   :objconf:`wrap_signatures_column_limit` is used.

   .. autoclass:: sphinx_immaterial.apidoc.format_signatures.BlackFormatStyle
      :exclude-members: __new__, __init__

      .. autoattribute:: line_length
      .. autoattribute:: string_normalization

.. rst-example::

   .. py:function:: some_module.method_name( \
                      some_parameter_with_a_long_name: \
                        collections.abc.MutableMapping[\
                          tuple[str, float, numbers.Real], \
                          dict[int, tuple[list[frozenset[int]]]]], \
                    ) -> collections.abc.MutableMapping[\
                           tuple[str, float, numbers.Real], \
                           dict[int, tuple[list[frozenset[int]]]]]
      :noindex:

      Some function doc.
