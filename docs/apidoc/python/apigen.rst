Python API documentation generation
===================================

This theme includes an optional extension that generates Python API
documentation pages.

- A separate page is generated for each documented entity.

- Top-level module-level entities are organized into *groups*, specified by the
  ``:group:`` field within the docstring.  The :rst:dir:`python-apigen-group`
  directive is used to insert a *summary* of a group into an existing page.

- The summary of a group shows an abbreviated signature and an abbreviated
  description for each entity in the group; the name portion of the signature is
  a link to the separate page for that entity.

- Class members are also organized into groups, also using the ``:group:`` field
  within their docstrings.  Class members without a group are assigned to a
  default group based on their name.  The summaries for each class member group
  are included on the page that documents the class.

- There is special support for pybind11-defined overloaded functions.  Each
  overload is documented as a separate function; each overload is identified by
  the ``:overload:`` field specified within its docstring.

Usage
-----

To use this extension, add :python:`"sphinx_immaterial.apidoc.python.apigen"` to
the list of extensions in :file:`conf.py` and define the
:confval:`python_apigen_modules` configuration option.

For example:

.. code-block:: python

    extensions = [
        # other extensions...
        "sphinx_immaterial.apidoc.python.apigen",
    ]

    python_apigen_modules = {
          "my_module": "api",
    }

This configuration is sufficient to generate a documentation page for every
top-level member of the specified modules.  To generate a listing of those
top-level members and add the generated documentation pages to the global table
of contents, the :rst:dir:`python-apigen-group` directive may be used.

.. tip::

   This extension works well with the :themeconf:`toc_title_is_page_title`
   configuration option.

Groups
^^^^^^

Each documented module member and class member is assigned to a member group.
The group is either explicitly specified or determined automatically.

The group may be specified explicitly using the :rst:`:group:` field within the
docstring:

.. code-block:: python

   def foo(x: int) -> int:
       """Does something or other.

       :param x: The parameter.
       :group: My group

When using the :py:obj:`sphinx.ext.napoleon` extension, the group can also be
specified using the ``Group:`` section:

.. code-block:: python

   def foo(x: int) -> int:
       """Does something or other.

       Args:
         x: The parameter.

       Group:
         My group

If the group is not specified explicitly, it is determined automatically based
on the :confval:`python_apigen_default_groups` option.

.. _python-apigen-member-order:

Member order
^^^^^^^^^^^^

For each each member there is also assigned an associated integer ``order``
value that determines the order in which members are listed: members are listed
in ascending order by their associated ``order`` value, and ties are broken
according to the :confval:`python_apigen_order_tiebreaker` option.

Similarly to the group name, the order value may be specified explicitly using
the :rst:`:order:` field within the docstring:

.. code-block:: python

   def foo(x: int) -> int:
       """Does something or other.

       :param x: The parameter.
       :group: My group
       :order: 1

When using the :py:obj:`sphinx.ext.napoleon` extension, the group can also be
specified using the ``Order:`` section:

.. code-block:: python

   def foo(x: int) -> int:
       """Does something or other.

       Args:
         x: The parameter.

       Group:
         My group

       Order:
         1

If the order value is not specified explicitly, it is determined automatically
based on the :confval:`python_apigen_default_order` option.

The order associated with a member determines both:

- the relative order in which the member is listed within its associated group;
- for class members, the order of the per-group sections for which an explicit
  section is not already listed in the class docstring (the order value
  associated with a group is the minimum of the order values of all of its
  members).

rST Directives
^^^^^^^^^^^^^^

.. rst:directive:: .. python-apigen-group:: group-name

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

   The group namespace for module-level members is global: if module ``a``
   defines a member ``foo`` in group ``My group`` and module ``b`` defines a
   member ``bar`` that is also in ``My group``, then the following example would
   insert a summary of both ``a.foo`` and ``b.bar``:

   .. rst-example:: Example usage

      .. python-apigen-group:: Some other group
         :notoc:

   .. note::

      This directive only includes top-level module members (for the modules
      specified by :confval:`python_apigen_modules`).  Class members are also
      organized into groups, but these groups are per-class and are listed
      (along with their members) on the documentation page for the class.

.. rst:directive:: .. python-apigen-entity-summary:: entity-name

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

Sections defined within docstrings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When using this extension, docstrings can define sections, including nested
sections, using the usual `reStructedText section syntax<rst-sections>`.  The
mapping between punctuation characters and heading levels is local to the
individual docstring.  Therefore, it is not necessary (though still recommended)
to use a consistent order of punctuation characters across different docstrings.

In addition to providing a way to organize any explanatory content, for classes,
sections can also correspond to member groups, as described below.

.. _python-apigen-class-member-groups:

Class member groups
^^^^^^^^^^^^^^^^^^^

Within the documentation page for a given class, after its normal docstring
content, a summary is added for each documented member, with a separate section
per group.

For each group, if the class docstring defines a section with a title equal to
the group name (or an id equal to the normalized group name), the member
summaries are added to the end of the existing section.  Otherwise, a new
section for the group is added to the end of the class documentation.

New sections are added in the order of first ocurrence of the group within the
:ref:`order<python-apigen-member-order>` defined for the members.

For example, consider the following class definition:

.. code-block:: python

   class Foo:
       """This is some class.

       Constructors
       ------------

       This class defines the following constructors.

       Operations
       ----------

       This class supports the following operations.
       """

       def __init__(self):
           """Constructs the class.

           :group: Constructors
           """

       def foo(self):
           """Performs the foo operation.

           :group: Operations
           """

       def bar(self):
           """Performs the bar operation.

           :group: Operations
           """

       def size(self) -> int:
           """Returns the size.

           :group: Accessors
           :order: 2
           """

       def __setitem__(self, i: int, value: int) -> None:
           """Set the element at the given position.

           :group: Indexing
           :order: 3
           """

       def __getitem__(self, i: int) -> int:
           """Returns the element at the given position.

           :group: Indexing
           :order: 1
           """

The ``__init__`` method will be documented within the existing ``Constructors``
section, the ``foo`` and ``bar`` methods will be documented within the existing
``Operations`` section.  After the ``Operations`` section, a new ``Indexing``
section will be added that lists the ``__getitem__`` and ``__setitem__``
members, and then a new ``Accessors`` section will be added that lists the
``size`` method.

Configuration
-------------

.. confval:: python_apigen_modules

   Maps module names to the output path prefix relative to the source directory.

   All entities defined by the specified modules are documented.

   For example, with the following added to :file:`conf.py`:

   .. code-block:: python

      python_apigen_modules = {
          "my_module": "my_api/",
          "my_other_module": "other_api/my_other_module.",
      }

   The following generated documents will be used (depending on the value of
   :confval:`python_apigen_case_insensitive_filesystem`):

   .. jinja:: python_apigen_path_examples

      .. list-table::
         :widths: auto
         :header-rows: 1

         * - Python object
           - Overload
           - Document (case-sensitive)
           - Document (case-insensitive)

         {%- for full_name, overload_id, case_sensitive, case_insensitive in example_python_apigen_objects %}
         * - :python:`{{ full_name }}`
           - {{ "``" + overload_id + "``" if overload_id else "" }}
           - :file:`{{ case_sensitive }}`
           - :file:`{{ case_insensitive }}`
         {%- endfor %}

   .. note::

      The specified path prefix for each module is treated as a *prefix*, not a
      directory.  It should normally end in either :python:`"/"` or some other
      delimiter like :python:`"."` If you want the generated document name to
      include the module name, choose a prefix of the form
      :python:`"api_directory/module_name."`.  If you want the generated
      document name to exclude the module name, choose a prefix of the form
      :python:`"api_directory/"`.

   .. warning::

      Because Sphinx is not designed to process files outside the source tree,
      these files are actually written to the source tree, and are regenerated
      automatically at the start of the build.  These files should not be
      checked into your source repository.  (When using git, you may wish to add
      a suitable pattern to a :file:`.gitignore` file.)

      The generated files start with a special comment to indicate that they
      were generated by this extension.  Stale files from previous build
      invocations are deleted automatically.  If there is an existing
      non-generated file with the same name as a to-be-generated file, the
      existing file will not be overwritten and the build will fail (showing an
      error message).

.. confval:: python_apigen_default_groups

   :python:`list` of :python:`(pattern, group)` pairs, where :python:`pattern`
   is a regular expression matching strings of the form
   :python:`"<objtype>:<fully_qualified_member_name>"`
   (e.g. :python:`"method:module_name.ClassName.member"`) and :python:`group` is
   the group name to assign.

   The group name for a given member is determined by the *last* matching
   pattern.  If no pattern matches, the group is ``Public members``.

   .. code-block:: python
      :caption: Example addition to :file:`conf.py`

      python_apigen_default_groups = [
          ("class:.*", "Classes"),
          (r".*\.__(init|new)__", "Constructors"),
          (r".*\.__(str|repr)__", "String representation"),
      ]

.. confval:: python_apigen_default_order

   :python:`list` of :python:`(pattern, order)` pairs, where :python:`pattern`
   is a regular expression matching strings of the form
   :python:`"<objtype>:<fully_qualified_member_name>"`
   (e.g. :python:`"method:module_name.ClassName.member"`) and :python:`order` is
   the :py:obj:`int` order to assign.

   The order value for a given member is determined by the *last* matching
   pattern.  If no pattern matches, the order value is 0.

   .. code-block:: python
      :caption: Example addition to :file:`conf.py`

      python_apigen_default_order = [
          ("class:.*", -10),
          (r".*\.__(init|new)__", -5),
          (r".*\.__(str|repr)__", 5),
      ]

.. confval:: python_apigen_order_tiebreaker

   Specifies the relative order of members that have the same associated
   ``order`` value.

   :python:`"definition_order"`
     - Top-level members are sorted first by the order their containing module
       is listed in :confval:`python_apigen_modules` and then by the order in
       which they are defined.
     - Class members are sorted by the order in which they are defined.
       Inherited members are listed after direct members, according to the
       method resolution order.

   :python:`"alphabetical"`
     All members are sorted alphabetically, first using case-insensitive
     comparison and then breaking ties with case-sensitive comparison.

   .. code-block:: python
      :caption: Add to :file:`conf.py` to specify alphabetical order.

      python_apigen_order_tiebreaker = "alphabetical"

.. confval:: python_apigen_case_insensitive_filesystem

   This extension results in an output file for each documented Python object
   based on its fully-qualified name.  Python names are case-sensitive, meaning
   both :python:`foo` and :python:`Foo` can be defined within the same scope,
   but some filesystems are case insensitive (e.g. on Windows and macOS), which
   creates the potential for a conflict.

   By default (if :confval:`python_apigen_case_insensitive_filesystem` is
   :python:`None`), this extension detects automatically if the filesystem is
   case-insensitive, but detection is skipped if the option is set to an
   explicit value of :python:`True` or :python:`False`:

   .. code-block:: python
      :caption: Add to :file:`conf.py` to force case-insensitive naming scheme

      python_apigen_case_insensitive_filesystem = True

   If the filesystem is either detected or specified to be case-insensitive,
   case conflicts are avoided by including a hash in the document name.

.. confval:: python_apigen_rst_prolog

   A string of reStructuredText that will be included at the beginning of every
   docstring.

   This may be used to set the :dudir:`default-role`, :rst:dir:`highlight`
   language, or :rst:dir:`default-literal-role`.

   .. note::

      The prior default role, default literal role, and default highlight
      langauge are automatically restored after processing the
      :confval:`python_apigen_rst_epilog`.  Therefore, it is not necessary to
      manually add anything to :confval:`python_apigen_rst_epilog` to restore the
      prior roles or highlight language.

   .. code-block:: python
      :caption: Setting default roles and highlight language in :file:`conf.py`

      rst_prolog = """
      .. role python(code)
         :language: python
         :class: highlight
      """

      python_apigen_rst_prolog = """
      .. default-role:: py:obj

      .. default-literal-role:: python

      .. highlight:: python
      """

.. confval:: python_apigen_rst_epilog

   A string of reStructuredText that will be included at the end of every
   docstring.

   This option is supported for symmetry with
   :confval:`python_apigen_rst_prolog`, but in most cases is not needed because
   any changes to the default role, default literal role, and default highlight
   language due to :confval:`python_apigen_rst_prolog` are undone automatically.

Subscript methods
^^^^^^^^^^^^^^^^^

*Subscript methods* are attributes defined on an object that support subscript
syntax.  For example:

.. code-block:: python

   arr.vindex[1, 2:5, [1, 2, 3]]

These subscript methods can be implemented as follows:

.. code-block:: python

   class MyArray:
       class _Vindex:
           def __init__(self, arr: MyArray):
               self.arr = arr

           def __getitem__(self, sel: Selection):
               # Do something with `self.arr` and `sel`.
               return result

       @property
       def vindex(self) -> MyArray._Vindex:
           return MyArray._Vindex(self)

Based on the :confval:`python_apigen_subscript_method_types` option, this
extension can recognize this pattern and display :python:`vindex` as:

.. code-block::

   vindex[sel: Selection]

rather than as a normal property.

.. confval:: python_apigen_subscript_method_types

   Regular expression pattern that matches the return type annotations of
   properties that define subscript methods.

   Return type annotations can be specified either as real annotations or in the
   textual signature specified as the first line of the docstring.

   The default value matches any name beginning with an underscore,
   e.g. :python:`_Vindex` in the example above.

.. confval:: python_apigen_show_base_classes

   Display the list of base classes when documenting classes.

   Unlike the built-in `sphinx.ext.autodoc` module, base classes are shown using
   the normal Python syntax in a parenthesized list after the class name.

   The list of base classes displayed for each class can be customized by adding
   a listener to the `autodoc-process-bases` event.  This is useful for
   excluding base classes that are not intended to be part of the public API.

   .. note::

      The built-in :py:obj:`object` type is never included as a base class.
