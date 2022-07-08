C++ domain customization
========================

.. confval:: cpp_strip_namespaces_from_signatures

   :python:`list[str]` specifying namespaces to strip from signatures.  This
   does not apply to the name of the symbol being defined by the signature, only
   to parameter types, return types, default value expressions, etc.

   For example, with the following in :file:`conf.py`:

   .. literalinclude:: /conf.py
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

.. confval:: cpp_xref_resolve_c_macro_pattern

   This theme adds support for resolving C macros and C macro parameters from
   cross references created using C++-domain roles like :rst:role:`cpp:expr` and
   :rst:role:`cpp:texpr`.

   To avoid an additional symbol lookup in most cases, this support relies on a
   regular expression pattern to identify potential C macro targets.  By
   default, only names consisting of uppercase latin letters, underscores, or
   digits are supported.  To support macros with other names, this pattern may
   be changed:

   .. code-block:: python
      :caption: Add to :file:`conf.py` to allow all identifiers as macro names

      cpp_xref_resolve_c_macro_pattern = "[^<>():]+"


:cpp:`#include` directives in signatures
----------------------------------------

This theme extend the C and C++ domains to allow signatures to specify required
:cpp:`#include` directives.

.. rst-example:: Specifying :cpp:`#include` directives in signatures

   .. cpp:function:: #include "my_header.h"
                     #include "another_header.h"
                     void foo(int param);

      Some function.

:rst:`:noindex:` and related advanced options
---------------------------------------------

This theme extends the Sphinx C and C++ domain with support for the following
options.

These options are primarily intended for use by other extensions, such as
``sphinx_immaterial.apidoc.cpp.apigen``, rather than direct use by users.

:rst:`:noindex:`
^^^^^^^^^^^^^^^^

Prevents the creation of a cross-reference target.  Also excludes the object
from search results.

.. rst-example:: Function defined with :rst:`noindex` option.

   .. cpp:function:: int my_function(int x);

      Function defined once.

   .. cpp:function:: int my_function(int x);
      :noindex:

      Function defined again.

.. warning::

   Currently, due to how parameters are cross linked, there must be at least one
   definition of the object for which :rst:`:noindex:` is not specified.

.. seealso::

   Sphinx itself supports the related :rst:`:noindexentry:` option, which
   prevents inclusion of the object in the "general index" (not normally useful
   with this theme anyway).  A cross-reference target is still created, and the
   object still appears in search results.

:rst:`:symbol-ids:`
^^^^^^^^^^^^^^^^^^^

By default, every C++ signature is assigned a symbol identifier automatically
based on its definition (similar to the name mangling scheme used by C++
compilers).

The :rst:`:symbol-ids:` option may be used to specify an alternative identifier
for each signature.

.. rst-example:: Function defined with alternative symbol identifier.

   .. cpp:function:: int my_function_with_custom_identifier(int x);
      :symbol-ids: ["my_custom_id"]

.. warning::

   If the :rst:`:symbol-ids:` option is used to specify a symbol identifier that
   does not match :regexp:`[a-zA-Z0-9_]*`, then :rst:`:node-id:` must also be
   used to specify an alternative valid HTML fragment identifier.

:rst:`:node-id:`
^^^^^^^^^^^^^^^^

The node id is the HTML fragment identifier that is used to link to a given
signature within a document.  By default, the node id is the same as the symbol
identifier, which may be redundant if the document only defines a single
signature.

The :rst:`:node-id:` may be used to specify an alternative HTML fragment
identifier.  This option has no effect if :rst:`:noindex:` is also specified.

.. rst-example:: Function with alternative HTML fragment identifier

   .. cpp:function:: int my_function_with_custom_fragment_identifier(int x);
      :node-id: custom_fragment_id

      Hover over the permalink symbol to see the custom fragment identifier.
