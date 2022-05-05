Python domain customization
===========================

.. confval:: python_type_aliases

   Maps names or dotted names appearing in type annotations in Python signatures
   to the corresponding fully-qualified name.

   For example, to map :python:`MyUnqualifiedType` to :python:`alias_ex.MyUnqualifiedType`, add the following
   to :file:`conf.py`:

   .. literalinclude:: conf.py
      :language: python
      :start-after: # BEGIN: python_type_aliases example
      :end-before: # END: python_type_aliases example

   .. rst-example:: Python signature modified by type alias

      .. py:function:: foo(x: MyUnqualifiedType) -> str
         :noindex:

         Function description.

.. confval:: python_resolve_unqualified_typing

   Specifies whether to add the following mappings to
   :confval:`python_type_aliases`:

   .. jinja:: sys

      {%- for x in sys.modules["sphinx_immaterial.python_type_annotation_transforms"].TYPING_NAMES %}
      - :python:`{{ x }}` -> :py:obj:`typing.{{ x }}`
      {%- endfor %}

   If :confval:`python_transform_type_annotations_pep585` is also set to
   :python:`True`, then these aliases are additionally subject to that mapping.

.. confval:: python_transform_type_annotations_pep585

   Specifies whether to add the following :pep:`585` mappings to
   :confval:`python_type_aliases`:

   .. jinja:: sys

      {%- for k, v in sys.modules["sphinx_immaterial.python_type_annotation_transforms"].PEP585_ALIASES.items() %}
      - :py:obj:`{{ k }}` -> :py:obj:`{{ v }}`
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

.. code-block:: python

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
