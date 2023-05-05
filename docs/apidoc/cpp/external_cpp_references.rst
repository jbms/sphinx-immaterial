External C++ symbol links
=========================

This theme includes an optional
:python:`sphinx_immaterial.apidoc.cpp.external_cpp_references` extension that
allows normal C++ symbol references, e.g. through the :rst:role:`cpp:expr` role
or in C++ function signatures, to resolve to externally-defined C++ symbols that
are manually specified in :file:`conf.py`.  Unlike the `sphinx.ext.intersphinx`
extension, template arguments are stripped when resolving references, which
allows template entities to be resolved based on their base name.

To use this extension, add it to the list of extensions in :file:`conf.py` and
define the :confval:`external_cpp_references` configuration option:

.. code-block:: python

    extensions = [
        # other extensions...
        "sphinx_immaterial.apidoc.cpp.external_cpp_references",
    ]

.. literalinclude:: /conf.py
    :language: python
    :start-after: # BEGIN: sphinx_immaterial.apidoc.cpp.external_cpp_references extension options
    :end-before: # END: sphinx_immaterial.apidoc.cpp.external_cpp_references extension options

.. rst-example::

    .. cpp:function:: int ExtractValueFromJson(::nlohmann::json json_value);

        Extracts a value from a JSON object.

.. confval:: external_cpp_references

    A dictionary specifying the URL, object type, and descriptive text for each externally
    documented symbol name.

    .. autoclass:: sphinx_immaterial.apidoc.cpp.external_cpp_references.ExternalCppReference
        :members:
        :show-inheritance:
        :exclude-members: __new__

.. seealso::
    :doc:`cppreference`
