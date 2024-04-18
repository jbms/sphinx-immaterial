Python domain customization
===========================

.. confval:: python_type_aliases

   Maps names or dotted names appearing in type annotations in Python signatures
   to the corresponding fully-qualified name.

   An entire module can be mapped by specifying a source name that ends in
   :python:`"."`.  The target name must either:

   - end in :python:`"."`, to transform the source module name to a different module
     name; or
   - be the empty string :python:`""`, to map the module name to the global
     namespace.

   .. note::

      This substitution happens *before* cross references are resolved, and
      affects both the cross-reference target and the displayed text.
      Therefore, the target name must be a valid cross-reference target if
      cross-referencing is desired.  In contrast, the
      :confval:`python_module_names_to_strip_from_xrefs` affects only the
      displayed text, not the cross-reference target.

   For example, to:

   - map :python:`MyUnqualifiedType` to :python:`alias_ex.MyUnqualifiedType`,
     and
   - map the :python:`example_mod._internal` module to :python:`example_mod`,

   add the following to :file:`conf.py`:

   .. literalinclude:: /conf.py
      :language: python
      :start-after: # BEGIN: python_type_aliases example
      :end-before: # END: python_type_aliases example

   .. rst-example:: Python signature modified by type alias

      .. py:function:: foo(a: MyUnqualifiedType, \
                           b: example_mod._internal.Foo) -> str
         :noindex:

         Function description.

.. confval:: python_resolve_unqualified_typing

   Specifies whether to add the following mappings to
   :confval:`python_type_aliases`:

   .. jinja:: typing_names

      {%- for x in TYPING_NAMES %}
      - :python:`{{ x }}` -> :python:`typing.{{ x }}`
      {%- endfor %}

   If :confval:`python_transform_type_annotations_pep585` is also set to
   :python:`True`, then these aliases are additionally subject to that mapping.

.. confval:: python_transform_type_annotations_pep585

   Specifies whether to add the following :pep:`585` mappings to
   :confval:`python_type_aliases`:

   .. jinja:: pep685_aliases

      {%- for k, v in aliases.items() %}
      - :python:`{{ k }}` -> :python:`{{ v }}`
      {% endfor %}

.. confval:: python_transform_type_annotations_pep604

   Converts type annotations involving :py:obj:`typing.Optional`,
   :py:obj:`typing.Union`, and/or :py:obj:`typing.Literal` to the more concise
   :pep:`604` form.

   .. rst-example::

      .. py:function:: foo(x: typing.Optional[int], \
                           y: typing.Union[int, float])
         :noindex:

.. confval:: python_transform_type_annotations_concise_literal

   If set to :python:`True`, converts :python:`typing.Literal[a]` to
   :python:`a` if :python:`a` is a constant.

   This option requires that :confval:`python_transform_type_annotations_pep604`
   is also enabled.

   .. rst-example::

      .. py:function:: foo(x: typing.Literal[1, 2, "abc"])
         :noindex:

      .. py:function:: foo(x: ~typing.Literal[1, 2, "abc"])
         :noindex:

   .. warning::

      The concise syntax is non-standard and not accepted by Python type
      checkers.

.. confval:: python_transform_typing_extensions

   Transforms a reference to ``typing_extensions.X`` within a type annotation
   into a reference to ``typing.X``.

.. confval:: python_strip_self_type_annotations

   Strip type annotations from the initial :python:`self` parameter of methods.

   Since the :python:`self` type is usually evident from the context, removing
   them may improve readability of the documentation.

   .. note::

      This option is useful when generating documentation from `pybind11
      <https://pybind11.readthedocs.io/en/stable/advanced/misc.html#generating-documentation-using-sphinx>`__
      modules, as pybind11 adds these type annotations.

   .. rst-example::

      .. py:class:: Example
         :noindex:

         .. py:method:: foo(self: Example, a: int) -> int
            :noindex:

            Does something with the object.

.. confval:: python_module_names_to_strip_from_xrefs

   List of module names to strip from cross references.  This option does not
   have any effect on the cross-reference target; it only affects what is
   displayed.

   For example, to hide the :python:`tensorstore_demo` module name in cross
   references, add the following to :file:`conf.py`:

   .. literalinclude:: /conf.py
      :language: python
      :start-after: # BEGIN: python_module_names_to_strip_from_xrefs example
      :end-before: # END: python_module_names_to_strip_from_xrefs example

   .. rst-example:: Python signature modified by module name stripping

      .. py:function:: foo(a: tensorstore_demo.Dim) -> str
         :noindex:

         Function description.

   .. seealso::

      To strip *all* modules, rather than a limited set, the built-in
      :confval:`python_use_unqualified_type_names` configuration option may be
      used instead.

.. confval:: python_strip_return_type_annotations

   Regular expression pattern that matches the full name (including module) of
   functions for which any return type annotations should be stripped.

   Setting this to `None` disables stripping of return type annotations.

   By default, the return type is stripped from :python:`__init__` and
   :python:`__setitem__` functions (which usually return :python:`None`).

   .. note::

      This option is useful when generating documentation from `pybind11
      <https://pybind11.readthedocs.io/en/stable/advanced/misc.html#generating-documentation-using-sphinx>`__
      modules, as pybind11 adds these type annotations.

   .. rst-example::

      .. py:class:: Example
         :noindex:

         .. py:method:: __setitem__(self, a: int, b: int) -> None
            :noindex:

            Does something with the object.

.. confval:: python_strip_property_prefix

   Strip the ``property`` prefix from :rst:dir:`py:property` object
   descriptions.

Overloaded functions
--------------------

The Sphinx Python domain supports documenting multiple signatures together as
part of the same object description:

.. rst-example::


   .. py:function:: overload_example1(a: int) -> int
                    overload_example1(a: float) -> float
                    overload_example1(a: str) -> str

      Does something with an `int`, `float`, or `str`.

However, it does not provide a way to document each overload with a separate
description, except by using the ``:noindex:`` option to avoid a warning from
duplicate definitions.

This theme extends the Python domain directives with an ``:object-ids:`` option to
allow multiple overloads of a given function to be documented separately:

The value of the ``:object-ids:`` option must be a JSON-encoded array of
strings, where each string specifies the full object name (including module
name) to use for each signature.  The object ids must start with the actual
module name, if any, but the remainder of the id need not match the name
specified in the signature.

.. rst-example::

   .. py:function:: overload_example2(a: int) -> int
                    overload_example2(a: float) -> float
      :object-ids: ["overload_example2(int)", "overload_example2(float)"]

      Does something with an `int` or `float`.

   .. py:function:: overload_example2(a: str) -> str
      :object-ids: ["overload_example2(str)"]

      Does something with a `str`.

If this option is specified, and :objconf:`generate_synopses` is enabled, then a
synopsis will be stored even if ``:noindex`` is also specified.

Separate page for object description
------------------------------------

Normally, the Python domain generates an ``id`` attribute for each object
description based on its full name.  This may be used in a URL to target a
specific object description, e.g. ``api/tensorstore.html#tensorstore.IndexDomain``.

If an entire page is dedicated to a single object description, this ``id`` is
essentially redundant,
e.g. ``api/tensorstore.IndexDomain.html#tensorstore.IndexDomain``.

This theme extends the Python domain directives (as well as the corresponding
``auto<objtype>`` directives provided by the `sphinx.ext.autodoc` extension)
with a ``:nonodeid:`` option:

.. code-block:: rst

   .. py:function:: func(a: int) -> int
      :nonodeid:

If this option is specified, the object description itself will not have an
``id``, and any cross references to the object will simply target the page.
Additionally, any table of contents entry for the page will have an associated
:ref:`icon<object-toc-icons>` if one has been configured for the object type.

.. note::

   Sphinx itself supports two related options for Python domain directives:

   - :rst:`:noindex:`: prevents the creation of a cross-reference target
     entirely.  The object will not appear in search results (except through
     text matches).

   - :rst:`:noindexentry:`: prevents inclusion of the object in the "general
     index" (not normally useful with this theme anyway).  A cross-reference
     target is still created, and the object still appears in search results.

   In contrast, if the :rst:`:nonodeid:` option is specified, a cross-reference
   target is still created, and the object is still included in search results.
   However, any cross references to the object will link to the containing page.
