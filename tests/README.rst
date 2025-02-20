Unit tests
==========

The unit tests require `graphviz <https://graphviz.org/download/>`_ to be installed.

.. code-block:: shell

    uv run --group test pytest -vv -s

Using ``nox``
-------------

This repo is setup to use `nox <https://nox.thea.codes/en/stable/>`_ in a Continuous Integration
workflow. The above instructions (except installing `graphviz <https://graphviz.org/download/>`_)
can be executed with 1 ``nox`` command.

.. code-block:: shell

    uvx nox -s tests

Code Coverage
-------------

Code coverage is included when using `nox <https://nox.thea.codes/en/stable/>`_ as well.
The coverage report should be generated *after* running the tests with ``nox``.

.. code-block:: shell

    uvx nox -s coverage

This will generate a ``.coverage_.md`` file of the coverage summary and a more in-depth analysis
in HTML form located in the ``htmlcov`` folder at the repo's root.
