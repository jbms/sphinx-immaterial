"""Tests related to theme's task list extension."""

from sphinx.testing.util import SphinxTestApp

index_rst = """
The Test
========

.. task-list::
    :name: task_list_example
    :custom:

    1. [x] Task A
    2. [ ] Task B

       .. task-list::
           :clickable:

           * [x] Task B1
           * [x] Task B2
           * [] Task B3

           A rogue paragraph with a reference to
           the `parent task_list <task_list_example>`.

           - A list item without a checkbox.
           - [ ] Another bullet point.

    3. [ ] Task C
"""


def test_task_list(immaterial_make_app):
    app: SphinxTestApp = immaterial_make_app(
        extra_conf="extensions.append('sphinx_immaterial.task_lists')",
        files={"index.rst": index_rst},
    )

    app.build()
    assert not app._warning.getvalue()  # type: ignore[attr-defined]
