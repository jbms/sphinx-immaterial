General API customization
=========================

.. confval:: include_object_description_fields_in_toc

   :python:`bool` indicating whether to include domain object description
   fields, like "Parameters", "Returns", "Raises", etc. in the table of
   contents.  Defaults to :python:`True`.

   For an example, see: :cpp:expr:`synopses_ex::Foo` and note the ``Template
   Parameters``, ``Parameters``, and ``Returns`` headings shown in the
   right-side table of contents.

   .. note::

      This option does not control whether there are separate TOC entries for
      individual parameters, such as for :cpp:expr:`synopses_ex::Foo::T`,
      :cpp:expr:`synopses_ex::Foo::N`, :cpp:expr:`synopses_ex::Foo::param`, and
      :cpp:expr:`synopses_ex::Foo::arr`.  Currently, for the C and C++ domains,
      any parameter documented by a :rst:``:param x:`` field will always result
      in a TOC entry, regardless of the value of
      :confval:`include_object_description_fields_in_toc`.  Other domains are
      not yet supported.
