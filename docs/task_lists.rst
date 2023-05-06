Task Lists
==============

This Sphinx extension mimics the HTML output of the ``pymdownx.tasklist`` Markdown
extension, which allows for the definition of task lists. With this extension and the
mkdocs-material theme's CSS, you can make list items prefixed with ``[ ]`` to render an unchecked
checkbox or ``[x]`` to render a checked checkbox.

This extension can be optionally be used in other sphinx theme's that support checkboxes.

.. code-block:: python
    :caption: This is already done in sphinx-immaterial theme:

    extensions = ["sphinx_immaterial.task_lists"]

.. success:: CSS is not included with this extension
    :collapsible:

    The CSS for checkboxes is not included with this extension. Rather, the CSS is served from the
    sphinx-immaterial theme (which is inherited from mkdocs-material theme).

    To use this extension with a theme that has no CSS support, try adding your own CSS:

    .. code-block:: css

        :root {
          --md-task-list-icon: url('data:image/svg+xml;charset=utf-8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill-rule="evenodd" d="M1 12C1 5.925 5.925 1 12 1s11 4.925 11 11-4.925 11-11 11S1 18.075 1 12zm16.28-2.72a.75.75 0 0 0-1.06-1.06l-5.97 5.97-2.47-2.47a.75.75 0 0 0-1.06 1.06l3 3a.75.75 0 0 0 1.06 0l6.5-6.5z"/></svg>');
          --md-task-list-icon--checked: url('data:image/svg+xml;charset=utf-8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill-rule="evenodd" d="M1 12C1 5.925 5.925 1 12 1s11 4.925 11 11-4.925 11-11 11S1 18.075 1 12zm16.28-2.72a.75.75 0 0 0-1.06-1.06l-5.97 5.97-2.47-2.47a.75.75 0 0 0-1.06 1.06l3 3a.75.75 0 0 0 1.06 0l6.5-6.5z"/></svg>');
        }

        /* style for the unchecked checkboxes */
        .task-list-indicator::before {
          -webkit-mask-image: var(--md-task-list-icon);
          mask-image: var(--md-task-list-icon);
          background-color: hsla(232deg, 75%, 90%, 0.12);

          content: "";
          height: 1.25em;
          -webkit-mask-repeat: no-repeat;
          mask-repeat: no-repeat;
          -webkit-mask-size: contain;
          mask-size: contain;
          position: absolute;
          top: .15em;
          width: 1.25em;
        }

        /* style for the checked checkboxes */
        .task-list-control > [type="checkbox"]:checked + .task-list-indicator::before {
          -webkit-mask-image: var(--md-task-list-icon--checked);
          mask-image: var(--md-task-list-icon--checked);
          background-color: hsl(122deg, 84%, 45%);
        }

Config variables
----------------

.. confval:: custom_checkbox

    A global conf.py `bool` variable to enable custom CSS for all checkboxes shown. Default is `False`.

.. confval:: clickable_checkbox

    A global conf.py `bool` variable to enable user interaction with the checkboxes shown. Default is `False`.

    .. note::
        If this option is used, then any user changes will not be saved.

``task-list`` Directive
-----------------------

.. rst:directive:: task-list

    This directive traverses the immediate list's items and adds a checkbox according to
    GitHub Flavored MarkDown.


    .. rst:directive:option:: class
        :type: string

        A space delimited list of qualified names that get used as the HTML element's
        ``class`` attribute.

        The ``class`` option is only applied to the containing ``div`` element.

        .. md-tab-set::

            .. md-tab-item:: rST code

                .. rst-example:: Custom icons scoped to immediate list only (not child lists)

                    .. task-list::
                        :class: custom-task-list-style
                        :custom:

                        + [ ] Custom unchecked checkbox
                        + [x] Custom checked checkbox

                          .. task-list::
                              :custom:

                              * [ ] A goal for a task.
                              * [x] A fulfilled goal.

            .. md-tab-item:: CSS Hint

                .. literalinclude:: _static/extra_css.css
                    :language: css
                    :start-after: /* **************************** custom-task-list style rules
                    :end-before: /* *************************** custom admonition style rules

    .. rst:directive:option:: name
        :type: string

        A qualified name that get used as the HTML element's ``name`` attribute.

        The ``name`` option is only applied to the containing ``div`` element.
        Use the `ref` role to reference the element by name.

    .. rst:directive:option:: custom
        :type: flag

        Allow custom styled checkboxes. Default is `False` unless `custom_checkbox` is enabled.

    .. rst:directive:option:: clickable
        :type: flag

        Allow user interaction with checkboxes. Default is `False` unless `clickable_checkbox` is enabled.

        .. note::
            If this option is used, then any user changes will not be saved.

Task List Example
-----------------

The following `task-list` example demonstrates nested `task-list`.
Notice that indentation is important with reStructuredText lists.

.. rst-example:: A feature spanning ``task-list`` example

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
