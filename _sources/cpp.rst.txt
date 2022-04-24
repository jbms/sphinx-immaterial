C++ domain customization
========================

.. confval:: cpp_generate_synopses

   :python:`bool` specifying whether to generate a *synopsis* for C++ domain
   objects based on the first paragraph of their content (first sentence for
   parameters).  The synopsis is shown as a tooltip when hovering over a
   cross-reference link, and is also shown in the search results list.

   Defaults to :python:`True`.

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


   .. rst-example::

      .. cpp:class:: synopses_ex::Class

          .. cpp:function:: Class(uint16_t _cepin, uint16_t _cspin, uint32_t _spi_speed=RF24_SPI_SPEED)

              :param _cepin: The pin attached to Chip Enable on the RF module
              :param _cspin: The pin attached to Chip Select (often labeled CSN) on the radio module.
              :param _spi_speed: The SPI speed in Hz ie: 1000000 == 1Mhz

.. confval:: cpp_strip_namespaces_from_signatures

   :python:`list[str]` specifying namespaces to strip from signatures.  This
   does not apply to the name of the symbol being defined by the signature, only
   to parameter types, return types, default value expressions, etc.

   For example, with the following in :file:`conf.py`:

   .. literalinclude:: conf.py
      :language: python
      :start-after: # BEGIN: cpp_strip_namespaces_from_signatures option
      :end-before: # END: cpp_strip_namespaces_from_signatures option

   .. rst-example:: C++ function definition with stripped namespaces

      .. cpp:type:: my_ns1::A

      .. cpp:type:: my_ns2::my_nested_ns::B

      .. cpp:type:: my_ns3::C

      .. cpp:function:: void my_ns1::MyFunction(my_ns1::A x, my_ns2::my_nested_ns::B y, my_ns3::C);

   .. warning::

      If a nested symbol name like :python:`"my_ns1::abc"` is specified in
      :confval:`cpp_strip_namespaces_from_signatures`, then a reference like
      :cpp:`my_ns1::abc::X` will be converted to :cpp:`my_ns1::X`.  To also
      strip the :cpp:`my_ns1::` portion, :python:`"my_ns1"` must also be
      specified in :confval:`cpp_strip_namespaces_from_signatures`.

.. confval:: cpp_qualify_parameter_ids

   :python:`bool` specifying whether function, template, and macro parameters
   should be assigned fully-qualified ids (for cross-linking purposes) of the
   form ``<parent-id>-p-<param-name>`` based on the id of the parent
   declaration.  Defaults to :python:`True`.

   If set to :python:`False`, instead the shorter unqualified id
   ``p-<param-name>`` is used.  This option should only be set to
   :python:`False` if each C++ declaration is on a separate page.


:cpp:`#include` directives in signatures
----------------------------------------

This theme extend the C and C++ domains to allow signatures to specify required
:cpp:`#include` directives.

.. rst-example:: Specifying :cpp:`#include` directives in signatures

   .. cpp:function:: #include "my_header.h"
                     #include "another_header.h"
                     void foo(int param);

      Some function.
