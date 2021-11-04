**********************************************
sample API documentation and generated content
**********************************************

.. contents:: Table of Contents

.. python and C++ demo API was copied from sphinx-rtd-theme docs

:mod:`test_py_module`
=====================

.. automodule:: test_py_module.test
    :members:
    :private-members:
    :special-members:


C++ API
=======

.. cpp:type:: MyType

   Some description for a datatype declared as :cpp:type:`MyType`

.. cpp:function:: const MyType Foo(const MyType bar, uint8_t baz, bool flag, uint16_t foobar, int32_t foobaz, unsigned long barbaz)

   Some function description.

   :param bar: Some parameter description.
   :returns: An :cpp:type:`MyType` object similar to the input parameter.

.. cpp:class:: template<typename T, std::size_t N, typename R, typename E, typename S, typename t, typename f> std::array

   Some templated C++ class.

   :tparam T: A description of the template parameter ``T``.
   :tparam N: A description of the template parameter ``N``.


.. cpp:member:: float Sphinx::version

   The description of :cpp:member:`Sphinx::version`.

.. cpp:var:: int version

   The description of :cpp:var:`version`.

.. cpp:type:: std::vector<int> List

   The description of type :cpp:type:`List`.

.. cpp:enum:: MyEnum

   An unscoped enum named :cpp:enum:`MyEnum`.

   .. cpp:enumerator:: A

      The description for :cpp:enumerator:`A`.

.. cpp:enum-class:: MyScopedEnum

   A scoped enum named :cpp:enum:`MyScopedEnum`.

   .. cpp:enumerator:: B

      The description for :cpp:enumerator:`B`.

.. cpp:enum-struct:: protected MyScopedVisibilityEnum : std::underlying_type<MySpecificEnum>::type

   A scoped enum with non-default visibility, and with a specified underlying type.

   .. cpp:enumerator:: B

      The description for :cpp:enumerator:`MyScopedVisibilityEnum::B`.

JavaScript API
==============

.. Copied from sphinx-doc/sphinx/tests/roots

.. js:module:: module_a.submodule

* Link to :js:class:`ModTopLevel`

.. js:class:: ModTopLevel

    * Link to :js:meth:`mod_child_1`
    * Link to :js:meth:`ModTopLevel.mod_child_1`

.. js:method:: ModTopLevel.mod_child_1

    * Link to :js:meth:`mod_child_2`

.. js:method:: ModTopLevel.mod_child_2

    * Link to :js:meth:`module_a.submodule.ModTopLevel.mod_child_1`

.. js:module:: module_b.submodule

* Link to :js:class:`ModTopLevel`

.. js:class:: ModNested

    .. js:method:: nested_child_1

        * Link to :js:meth:`nested_child_2`

    .. js:method:: nested_child_2

        * Link to :js:meth:`nested_child_1`


Generated Index
===============

Part of the sphinx build process in generate and index file: :ref:`genindex`.


Optional parameter args
=======================

At this point optional parameters `cannot be generated from code`_.
However, some projects will manually do it, like so:

This example comes from `django-payments module docs`_.

.. class:: payments.dotpay.DotpayProvider(seller_id, pin[, channel=0[, lock=False], lang='pl'])

   This backend implements payments using a popular Polish gateway, `Dotpay.pl <http://www.dotpay.pl>`_.

   Due to API limitations there is no support for transferring purchased items.


   :param seller_id: Seller ID assigned by Dotpay
   :param pin: PIN assigned by Dotpay
   :param channel: Default payment channel (consult reference guide)
   :param lang: UI language
   :param lock: Whether to disable channels other than the default selected above

.. _cannot be generated from code: https://groups.google.com/forum/#!topic/sphinx-users/_qfsVT5Vxpw
.. _django-payments module docs: http://django-payments.readthedocs.org/en/latest/modules.html#payments.authorizenet.AuthorizeNetProvide


Data
====

.. data:: Data_item_1
          Data_item_2
          Data_item_3

    Lorem ipsum dolor sit amet, consectetur adipiscing elit. Fusce congue elit eu hendrerit mattis.

Some data link :data:`Data_item_1`.
