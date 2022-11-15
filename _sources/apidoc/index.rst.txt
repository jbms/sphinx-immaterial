General API customization
=========================

This theme supports a number of options that can be customized for each
domain/object type pair.

.. confval:: object_description_options

   :python:`list` of :python:`(pattern, options)` pairs, where :python:`pattern`
   is a regular expression matching strings of the form
   :python:`"domain:objtype"` and :python:`options` is a dictionary of supported
   `object-description-options`.

   The actual options for a given object type are determined by first
   initializing each option to its default value, and then applying as overrides
   the options associated with each matching pattern in order.

.. _object-description-options:

Object description options
--------------------------

The following options can be customized for each object type using
:confval:`object_description_options`.

.. objconf:: include_in_toc

   Indicates whether to include the object description in the table of contents.

   .. example::

      To prevent C++ parameter descriptions from appearing in the TOC, add the
      following to :file:`conf.py`:

      .. code-block:: python

         object_description_options = [
             ("cpp:.*Param", dict(include_in_toc=False)),
         ]

.. objconf:: generate_synopses

   Indicates whether to generate a *synopsis* from the object description.  The
   synopsis is shown as a tooltip when hovering over a cross-reference link, and
   is also shown in the search results list.  Supported values are:

   :python:`None`
     Disables synopsis generation.

   :python:`"first_paragraph"`
     Uses the first paragraph of the description as the synopsis.

   :python:`"first_sentence"`
     Uses the first sentence of the first paragraph of the description as the synopsis.

   The default is :python:`"first_paragraph"` except for :regexp:`c(pp)?:.*Param`
   where the default is :python:`"first_sentence"`.

   .. note::

      Synopsis generation is currently supported only for the following domains:

      - ``std`` (including object types added using :py:obj:`sphinx.application.Sphinx.add_object_type`)
      - ``c`` and ``cpp``
      - ``py``
      - ``json``

   .. example::

      To use the first sentence rather than the first paragraph as the synopsis
      for C++ class descriptions, add the following to :file:`conf.py`:

      .. code-block:: python

         object_description_options = [
             ("cpp:class", dict(generate_synopses="first_sentence")),
         ]

.. objconf:: include_object_type_in_xref_tooltip

   Indicates whether to include the object type in cross-reference and TOC
   tooltips.

   .. note::

      For TOC entries, this is supported for all domains.  For regular cross
      references, this is supported only for the following domains:

      - ``std`` (including object types added using :py:obj:`sphinx.application.Sphinx.add_object_type`)
      - ``c`` and ``cpp``
      - ``py``
      - ``json``

   .. example::

      To exclude the object type from all ``py`` domain xrefs, add the following
      to :file:`conf.py`:

      .. code-block:: python

         object_description_options = [
             ("py:.*", dict(include_object_type_in_xref_tooltip=False)),
         ]

.. objconf:: include_fields_in_toc

   Indicates whether to include fields, like "Parameters", "Returns", "Raises",
   etc., in the table of contents.

   For an example, see: :cpp:expr:`synopses_ex::Foo` and note the ``Template
   Parameters``, ``Parameters``, and ``Returns`` headings shown in the
   right-side table of contents.

   .. note::

      To control whether there are separate TOC entries for individual
      parameters, such as for :cpp:expr:`synopses_ex::Foo::T`,
      :cpp:expr:`synopses_ex::Foo::N`, :cpp:expr:`synopses_ex::Foo::param`, and
      :cpp:expr:`synopses_ex::Foo::arr`, use the :objconf:`include_in_toc`
      option.


   .. example::

      To exclude object description fields from the table of contents for all
      ``py`` domain objects, add the following to :file:`conf.py`:

      .. code-block:: python

         object_description_options = [
             ("py:.*", dict(include_fields_in_toc=False)),
         ]

.. objconf:: include_rubrics_in_toc

   Indicates whether to include rubrics in object descriptions, like "Notes", "References", "Examples",
   etc., in the table of contents.

   .. note::

      Traditionally, rubrics are not intended to be included in the table of contents. However with
      :objconf:`include_fields_in_toc`, rubric-like fields may be included in the TOC. Including
      other rubrics from the object description in the TOC is provided for visual consistency.

   .. example::

      To include object description rubrics in the table of contents for all
      ``py`` domain objects, add the following to :file:`conf.py`:

      .. code-block:: python

         object_description_options = [
             ("py:.*", dict(include_rubrics_in_toc=True)),
         ]

Other options described elsewhere include:

- :objconf:`wrap_signatures_with_css`
- :objconf:`wrap_signatures_column_limit`
- :objconf:`clang_format_style`

.. _object-toc-icons:

Table of contents icons
^^^^^^^^^^^^^^^^^^^^^^^

For object descriptions included in the table of contents (when
:objconf:`include_in_toc` is :python:`True`), a text-based "icon" can optionally
be included to indicate the object type.

Default icons are specified for a number of object types, but they can be
overridden using the following options:

.. objconf:: toc_icon_class

   Indicates the icon class, or :python:`None` to disable the icon.  The class
   must be one of:

   - :python:`"alias"`
   - :python:`"procedure"`
   - :python:`"data"`
   - :python:`"sub-data"`

.. objconf:: toc_icon_text

   Indicates the text content of the icon, or :python:`None` to disable the
   icon.  This should normally be a single character, such as :python:`"C"` to
   indicate a class or :python:`"F"` to indicate a function.

.. example::

   To define a custom object type and specify an icon for it, add the following to
   :file:`conf.py`:

   .. code-block:: python

      object_description_options = [
          ("std:confval", dict(toc_icon_class="data", toc_icon_text="C")),
      ]

      def setup(app):
          app.add_object_type(
              "confval",
              "confval",
              objname="configuration value",
              indextemplate="pair: %s; configuration value",
          )
