Automatic cross-linking to cppreference.com
===========================================

This theme provides an optional
:python:`sphinx_immaterial.apidoc.cpp.cppreference` extension that provides
automatic linking to C/C++ standard symbols documented at
https://cppreference.com.

To use this extension, simply add it to the list of extensions in :file:`conf.py`:

.. code-block:: python

    extensions = [
        # other extensions...
        "sphinx_immaterial.apidoc.cpp.cppreference",
    ]

.. rst-example::

   .. cpp:function:: template <typename T> \
                     std::enable_if_t<std::is_same_v<T, char> || \
                                      std::is_same_v<T, uint8_t>, \
                                      std::string> \
                     ConvertVectorToString(std::vector<T> x);

      Converts an :cpp:expr:`std::vector` to an :cpp:expr:`std::string`.

.. confval:: cppreference_xml_files

   Overrides the default list of XML data files to use.  This allows an
   alternative (e.g. newer) version of the cppreference XML data files that are
   available at:

   - https://raw.githubusercontent.com/p12tic/cppreference-doc/master/index-functions-c.xml
   - https://raw.githubusercontent.com/p12tic/cppreference-doc/master/index-functions-cpp.xml

   For example, if newer versions of the C and C++ XML files have been copied
   to the documentation root directory, they can be used with the following
   configuration:

   .. code-block:: python

      cppreference_xml_files = [
          ("C", "index-functions-c.xml"),
          ("C++", "index-functions-cpp.xml"),
      ]

.. seealso::

   - :doc:`external_cpp_references`
