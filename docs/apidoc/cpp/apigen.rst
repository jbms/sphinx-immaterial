C++ API documentation generation
================================

.. warning::

   This functionality is experimental, incomplete and subject to
   backwards-incompatible changes.

This theme includes an optional extension that generates C++ API documentation
pages.

- The entities to document, along with their documentation, are extracted
  automatically from C/C++ header files using `libclang
  <https://pypi.org/project/libclang/>`__.  Doc comments are expected to be in
  reStructuredText syntax, although a limited set of Doxygen commands are also
  supported and converted automatically to their reStructuredText equivalents.

- A separate page is generated for each documented entity.

- Top-level module-level entities are organized into *groups*, specified by the
  :rst:`:group:` field within the docstring.  The :rst:dir:`cpp-apigen-group`
  directive is used to insert a *summary* of a group into an existing page.

- The summary of a group shows an abbreviated signature and an abbreviated
  description for each entity in the group; the name portion of the signature is
  a link to the separate page for that entity.

- Entities have three types of *related* entities:

  - Class members are automatically considered *related members* of their parent
    class.
  - Friend functions defined within a class definition (i.e. hidden friends) are
    also automatically considered *related members* of the containing class.
  - Any other entity may explicitly designate itself as a *related non-member*
    of any other entity using the :rst:`:relates:` field within the docstring.

  For a given parent entity, the related entities are also organized into
  groups, based on the :rst:`:group:` field within the related entities'
  docstrings, as well as default group assignment rules.  The summaries for each
  of these groups are included on the documentation page for the parent entity.

Usage
-----

To use this extension, add :python:`"sphinx_immaterial.apidoc.cpp.apigen"` to
the list of extensions in :file:`conf.py` and define the
:confval:`cpp_apigen_configs` configuration option.

For example:

.. code-block:: python

    extensions = [
        # other extensions...
        "sphinx_immaterial.apidoc.cpp.apigen",
    ]

    cpp_apigen_configs = {
        ...
    }

This configuration is sufficient to generate a documentation page for every
top-level member of the specified modules.  To generate a listing of those
top-level members and add the generated documentation pages to the global table
of contents, the :rst:dir:`cpp-apigen-group` directive may be used.

.. tip::

   This extension works well with the :themeconf:`toc_title_is_page_title`
   configuration option.

rST Directives
^^^^^^^^^^^^^^

.. rst:directive:: .. cpp-apigen-group:: group-name

   Generates a summary of all top-level members that are in the specified group,
   and also inserts a table-of-contents entry for each member at the current
   document position.

   Before matching the specified group name to the group name of every top-level
   member, all the group names are normalized by converting each letter to
   lowercase and converting spaces to ``-``.

   .. rst:directive:option:: notoc

      By default, this directive also adds the pages corresponding to the
      members of the specified group to the global table of contents as children
      of the current page/section.  Specifying this flag disables that behavior.

   .. rst-example:: Example usage

      .. cpp-apigen-group:: indexing
         :notoc:

.. rst:directive:: .. cpp-apigen-entity-summary:: entity-name

   Generates a summary of a single Python entity.

   The ``entity-name`` should be specified as
   :python:`module_name.ClassName.member` or
   :python:`module_name.ClassName.member(overload)`.

   .. rst:directive:option:: notoc

      By default, this directive also adds the page corresponding to the
      specified Python entity to the global table of contents as a child of the
      current page/section.  Specifying this flag disables that behavior.

   .. rst-example:: Example usage

      .. python-apigen-entity-summary:: tensorstore_demo.IndexDomain.__init__(json)
         :notoc:

Configuration
-------------

.. confval:: cpp_apigen_configs

   Specifies the C++ API parsing and documentation generation configurations to
   use.

   .. default-role:: py:obj

   .. autoclass:: sphinx_immaterial.apidoc.cpp.apigen.ApigenConfig
      :members:
      :member-order: bysource
      :exclude-members: __init__

   .. autoclass:: sphinx_immaterial.apidoc.cpp.api_parser.Config
      :members:
      :member-order: bysource
      :exclude-members: __init__

   .. default-role:: any

.. confval:: cpp_apigen_case_insensitive_filesystem

   This extension results in an output file for each documented C++ entity based
   on its fully-qualified name.  C++ names are case-sensitive, meaning both
   :cpp:`foo` and :cpp:`Foo` can be defined within the same scope, but
   some filesystems are case insensitive (e.g. on Windows and macOS), which
   creates the potential for a conflict.

   By default (if :confval:`cpp_apigen_case_insensitive_filesystem` is
   :python:`None`), this extension detects automatically if the filesystem is
   case-insensitive, but detection is skipped if the option is set to an
   explicit value of :python:`True` or :python:`False`:

   .. code-block:: python
      :caption: Add to :file:`conf.py` to force case-insensitive naming scheme

      cpp_apigen_case_insensitive_filesystem = True

   If the filesystem is either detected or specified to be case-insensitive,
   case conflicts are avoided by including a hash in the document name.

.. confval:: cpp_apigen_rst_prolog

   A string of reStructuredText that will be included at the beginning of the
   documentation text for each entity.

   This may be used to set the :dudir:`default-role`, :rst:dir:`highlight`
   language, or :rst:dir:`default-literal-role`.

   .. note::

      The prior default role, default literal role, and default highlight
      langauge are automatically restored after processing the
      :confval:`cpp_apigen_rst_epilog`.  Therefore, it is not necessary to
      manually add anything to :confval:`cpp_apigen_rst_epilog` to restore the
      prior roles or highlight language.

   .. code-block:: python
      :caption: Setting default roles and highlight language in :file:`conf.py`

      rst_prolog = """
      .. role cpp(code)
         :language: cpp
         :class: highlight
      """

      cpp_apigen_rst_prolog = """
      .. default-role:: cpp:expr

      .. default-literal-role:: cpp

      .. highlight:: cpp
      """

.. confval:: cpp_apigen_rst_epilog

   A string of reStructuredText that will be included at the end of the
   documentation text for each entity.

   This option is supported for symmetry with
   :confval:`cpp_apigen_rst_prolog`, but in most cases is not needed because
   any changes to the default role, default literal role, and default highlight
   language due to :confval:`cpp_apigen_rst_prolog` are undone automatically.
