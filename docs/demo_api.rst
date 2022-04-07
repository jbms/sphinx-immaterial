**********************************************
sample API documentation and generated content
**********************************************

.. contents:: Table of Contents

:mod:`test_py_module`
=====================

.. result:: autodoc example

   .. automodule:: test_py_module.test
      :members:
      :private-members:
      :special-members:

C++ API
=======

.. result::

   .. cpp:type:: MyType

      Some type

.. result::

   .. c:macro:: DEFAULT_LENGTH

   .. cpp:function:: const MyType Foo(const MyType bar, uint8_t* arr, unsigned int len = DEFAULT_LENGTH, bool baz= false)

      Some function type thing

.. result::

   .. cpp:class:: template<typename T, typename A, typename B, typename C, std::size_t N> std::array

      Some cpp class

.. result::

   .. cpp:member:: float Sphinx::version

      The description of `Sphinx::version`.

.. result::

   .. cpp:var:: int version

      The description of version.

.. result::

   .. cpp:type:: std::vector<int> List

      The description of List type.

.. result::

   .. cpp:enum:: MyEnum

      An unscoped enum.

      .. cpp:enumerator:: A

   .. cpp:enum-class:: MyScopedEnum

      A scoped enum.

      .. cpp:enumerator:: B

   .. cpp:enum-struct:: protected MyScopedVisibilityEnum : std::underlying_type<MySpecificEnum>::type

      A scoped enum with non-default visibility, and with a specified underlying type.

      .. cpp:enumerator:: B


JavaScript API
==============

.. Copied from sphinx-doc/sphinx/tests/roots

.. js:module:: module_a.submodule

.. result::

   * Link to :js:class:`ModTopLevel`

.. result::

   .. js:class:: ModTopLevel

      * Link to :js:meth:`mod_child_1`
      * Link to :js:meth:`ModTopLevel.mod_child_1`

.. result::

   .. js:method:: ModTopLevel.mod_child_1

      * Link to :js:meth:`mod_child_2`

   .. js:method:: ModTopLevel.mod_child_2

      * Link to :js:meth:`module_a.submodule.ModTopLevel.mod_child_1`

.. result::

   * Link to :js:class:`ModTopLevel`

.. js:module:: module_b.submodule

.. result::

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

.. result::

   A generated index (:ref:`genindex`) is part of the Sphinx build process, unless
   `html_use_index` is set to `False`.

   Sphinx also allows indexing by domain (programming language), as seen in the
   :ref:`modindex` for the demo Python module that is documented on this page.

.. note::
   This theme does not support a separate search page (usually referenced with
   ``:ref:`search``), since the search is accessible in the site's navigation bar.

Data
====

.. result::

   .. data:: Data_item_1
             Data_item_2
             Data_item_3

      Lorem ipsum dolor sit amet, consectetur adipiscing elit. Fusce congue elit eu hendrerit mattis.

   Some data link :data:`Data_item_1`.
