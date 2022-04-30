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

.. confval:: python_qualify_parameter_ids

   Specifies whether function parameters should be assigned fully-qualified ids
   (for cross-linking purposes) of the form ``<parent-id>.<param-name>`` based
   on the id of the parent declaration.

   If set to :python:`False`, instead the shorter unqualified id
   ``p-<param-name>`` is used.  This option should only be set to
   :python:`False` if each Python declaration is on a separate page.
