**********************************************
sample API documentation and generated content
**********************************************

.. contents:: Table of Contents

Python API
==========

``test_py_module``
------------------

.. rst-example:: autodoc example

   .. automodule:: test_py_module.test
      :members:
      :private-members:
      :special-members:

.. rst-example:: Python function with multiple signatures

   .. py:function:: overloaded_func(a: int, b: int) -> int
                    overloaded_func(a: float, b: float) -> float

      Adds :py:param:`a` and :py:param:`b`.

      :param a: First operand.
      :param b: Second operand.

C++ API
=======

.. rst-example::

   .. cpp:type:: MyType

      Some type

.. rst-example::

   .. c:macro:: DEFAULT_LENGTH

   .. cpp:function:: template <typename T, int K> \
                     const MyType Foo(\
                         const MyType bar, uint8_t* arr, \
                         unsigned int len = DEFAULT_LENGTH, \
                         bool baz= false)
                     const MyType Foo(\
                         const MyType bar, uint16_t* arr, \
                         unsigned int len = DEFAULT_LENGTH, \
                         bool baz= false)

      Some function type thing

      :tparam T: Some type template parameter.
      :tparam K: Some non-type template parameter.
      :param bar: This is the bar parameter.
      :param arr[out]: Array of something.  Elements may be either
          :cpp:expr:`uint8_t` or :cpp:expr:`uint16_t`.
      :param len: Length of :cpp:expr:`arr`.
      :param baz: Baz parameter.

.. rst-example:: Cross-linking of macro parameters.

   .. c:macro:: MY_MACRO(X, Y, Z)

      Expands to something.

      :param X: The X parameter to the macro.
      :param Y: The Y parameter to the macro.

.. rst-example::

   .. cpp:class:: template<typename T, typename A, typename B, typename C, std::size_t N> std::array

      Some cpp class

.. rst-example::

   .. cpp:member:: float Sphinx::version

      The description of `Sphinx::version`.

.. rst-example::

   .. cpp:var:: int version

      The description of version.

.. rst-example::

   .. cpp:type:: std::vector<int> List

      The description of List type.

.. rst-example::

   .. cpp:enum:: MyEnum

      An unscoped enum.

      .. cpp:enumerator:: A

   .. cpp:enum-class:: MyScopedEnum

      A scoped enum.

      .. cpp:enumerator:: B

         Description of enumerator B.

   .. cpp:enum-struct:: protected MyScopedVisibilityEnum : std::underlying_type_t<MyScopedEnum>

      A scoped enum with non-default visibility, and with a specified underlying type.

      .. cpp:enumerator:: B

.. rst-example:: C++ synopses

   .. cpp:type:: synopses_ex::SomeType

      Description will be shown as a tooltip when hovering over
      cross-references to :cpp:expr:`SomeType` in other signatures as well as
      in the TOC.

      Additional description not shown in tooltip.  This is the return type
      for :cpp:expr:`Foo`.

   .. cpp:function:: template <typename T, int N> \
                     synopses_ex::SomeType synopses_ex::Foo(\
                       T param, \
                       const int (&arr)[N]\
                     );

      Synopsis for this function, shown when hovering over cross references
      as well as in the TOC.

      :tparam T: Tooltip shown when hovering over cross-references to this
          template parameter.  Additional description not included in
          tooltip.
      :tparam N: Tooltip shown for N.
      :param param: Tooltip shown for cross-references to this function
          parameter param.
      :param arr: Tooltip shown for cross-references to this function
          parameter arr.  To cross reference another parameter, use the
          :rst:role:`cpp:expr` role, e.g.: :cpp:expr:`N`.  Parameters can
          also be referenced via their fake qualified name,
          e.g. :cpp:expr:`synopses_ex::Foo::N`.
      :returns: Something or other.

.. rst-example:: C++ function with parameter descriptions nested within class.

   .. cpp:class:: synopses_ex::Class

       .. cpp:function:: Class(uint16_t _cepin, uint16_t _cspin, uint32_t _spi_speed=RF24_SPI_SPEED)

           :param _cepin: The pin attached to Chip Enable on the RF module
           :param _cspin: The pin attached to Chip Select (often labeled CSN) on the radio module.
           :param _spi_speed: The SPI speed in Hz ie: 1000000 == 1Mhz


JavaScript API
==============

.. Copied from sphinx-doc/sphinx/tests/roots

.. js:module:: module_a.submodule

.. rst-example::

   * Link to :js:class:`ModTopLevel`

.. rst-example::

   .. js:class:: ModTopLevel

      * Link to :js:meth:`mod_child_1`
      * Link to :js:meth:`ModTopLevel.mod_child_1`

.. rst-example::

   .. js:method:: ModTopLevel.mod_child_1

      * Link to :js:meth:`mod_child_2`

   .. js:method:: ModTopLevel.mod_child_2

      * Link to :js:meth:`module_a.submodule.ModTopLevel.mod_child_1`

.. rst-example::

   * Link to :js:class:`ModTopLevel`

.. js:module:: module_b.submodule

.. rst-example::

   .. js:class:: ModNested

      .. js:method:: nested_child_1

         * Link to :js:meth:`nested_child_2`

      .. js:method:: nested_child_2

         * Link to :js:meth:`nested_child_1`

      .. js:method:: getJSON(href, callback, priority[, err_back, flags])

         :param string href: An URI to the location of the resource.
         :param callback: Gets called with the object.
         :param err_back:
            Gets called in case the request fails. And a lot of other
            text so we need multiple lines.
         :throws SomeError: For whatever reason in that case.
         :returns: Something.

Generated Index
===============

.. rst-example::

   A generated index (:ref:`genindex`) is part of the Sphinx build process, unless
   `html_use_index` is set to :python:`False`.

   Sphinx also allows indexing by domain (programming language), as seen in the
   :ref:`modindex` for the demo Python module that is documented on this page.

.. note::

   This theme does not support a separate search page, since the search
   functionality is accessible in the site's navigation bar.

Data
====

.. rst-example::

   .. data:: Data_item_1
             Data_item_2
             Data_item_3

      Lorem ipsum dolor sit amet, consectetur adipiscing elit. Fusce congue elit eu hendrerit mattis.

   Some data link :data:`Data_item_1`.
