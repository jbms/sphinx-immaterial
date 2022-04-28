External C++ symbol links
=========================

This theme includes an optional
:python:`sphinx_immaterial.external_cpp_references` extension that allows normal
C++ symbol references, e.g. through the :rst:role:`cpp:expr` role or in C++
function signatures, to resolve to externally-defined C++ symbols that are
manually specified in :file:`conf.py`.  Unlike the `sphinx.ext.intersphinx`
extension, template arguments are stripped when resolving references, which
allows template entities to be resolved based on their base name.

To use this extension, add it to the list of extensions in :file:`conf.py` and
define the :confval:`external_cpp_references` configuration option:

.. code-block:: python

    extensions = [
        # other extensions...
        "sphinx_immaterial.external_cpp_references",
    ]

.. literalinclude:: conf.py
   :language: python
   :start-after: # BEGIN: sphinx_immaterial.external_cpp_references extension options
   :end-before: # END: sphinx_immaterial.external_cpp_references extension options

.. rst-example::

   .. cpp:function:: int ExtractValueFromJson(::nlohmann::json json_value);

      Extracts a value from a JSON object.

.. confval:: external_cpp_references

   Specifies for each symbol name a dictionary specifying the URL, object type,
   and description type:

   .. code-block:: python

      class ExternalCppReference(typing.TypedDict):
          url: str
          object_type: str
          desc: str

   The :python:`object_type` should be one of the object types defined by the C++ domain:

   - :python:`"class"`
   - :python:`"union"`
   - :python:`"function"`
   - :python:`"member"`
   - :python:`"type"`
   - :python:`"concept"`
   - :python:`"enum"`
   - :python:`"enumerator"`

.. seealso::

   - :doc:`cppreference`
