Unit tests
==========

To run unit tests for the sphinx-immaterial theme, there must first be dependencies installed.
Install the dependencies by executing the following from the repo root folder:

.. code-block:: shell

    pip install -r tests/requirements.txt

The unit tests also require `graphviz <https://graphviz.org/download/>`_ installed.

The sphinx-immaterial theme should also be installed. For developer purposes, we recommend
using an editable install, but this also requires that theme assets be assembled (as is done for
distribution).

.. code-block:: shell

    npm install
    npm run build
    pip install -e .

You should now be ready to run the unit tests. This can be done directly with ``pytest`` CLI:

.. code-block:: shell

    pytest -vv -s

Using ``nox``
-------------

This repo is setup to use `nox <https://nox.thea.codes/en/stable/>`_ in a Continuous Integration
workflow. The above instructions (except installing `graphviz <https://graphviz.org/download/>`_)
can be executed with 1 ``nox`` command.

.. code-block:: shell

    nox -s tests

Code Coverage
-------------

Code coverage is included when using `nox <https://nox.thea.codes/en/stable/>`_ as well.
The coverage report should be generated *after* running the tests with ``nox``.

.. code-block:: shell

    nox -s coverage

This will generate a ``.coverage_.md`` file of the coverage summary and a more in-depth analysis
in HTML form located in the ``htmlcov`` folder at the repo's root.
