C++ domain customization
========================

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

   Specifies whether function, template, and macro parameters should be assigned
   fully-qualified ids (for cross-linking purposes) of the form
   ``<parent-id>-p-<param-name>`` based on the id of the parent declaration.

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
