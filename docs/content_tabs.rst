.. _sphinx-design tabs: https://sphinx-design.readthedocs.io/en/furo-theme/tabs.html

Using tabbed content
====================

.. note::
    This document focused on content tabs, not navigation tabs.

Use of `content tabs in mkdocs-material <https://squidfunk.github.io/mkdocs-material/reference/content-tabs/>`_
theme relies on a markdown extension that isn't used in the world of Sphinx. Instead,
the sphinx-immaterial theme provides its own directives to make use of content tabs.

.. code-block:: python
    :caption: These directives require an added entry in conf.py's extension list:

    extensions = ["sphinx_immaterial", "sphinx_immaterial.content_tabs"]

.. admonition:: Linked Tabs
    :class: missing

    The `linked content tabs <https://squidfunk.github.io/mkdocs-material/reference/content-tabs/#linked-content-tabs>`_
    seen in mkdocs-material is not supported until that feature transitions from the mkdocs-material theme's insider
    releases to it's public releases.

    However, you can use other sphinx extensions (like `sphinx-design tabs`_) to achieve this functionality.
    Although, other extensions will require some custom CSS styling to match the mkdocs-material
    theme's styling for content tabs.

.. confval:: md-tab-set

    Each set of tabs on a page must begin with a `md-tab-set` directive. This directive
    only accepts children that `md-tab-item` directives.

    This directive supports ``:class:`` and ``:name:`` options to use custom CSS classes
    and reference links (respectively)

    .. code-block:: rst

        .. md-tab-set::
            :class: custom-tab-set-style
            :name: ref_this_tab_set

            .. md-tab-item:: Local Ref

                A reference to this tab set renders like so:
                `tab set description <ref_this_tab_set>`.
                
                This syntax can only be used on the same page as the tab set.

            .. md-tab-item:: Cross-page Ref

                To cross-reference this tab set from a different page, use
                :ref:`tab set description <ref_this_tab_set>`

                Use this syntax to give a tab set a custom description.
                Clearly this also works on the same page.

            .. md-tab-item:: Custom CSS

                .. literalinclude:: _static/extra_css.css
                    :language: css
                    :start-at: /* ************************ custom-tab-set-style
                    :end-before: /* *********************** custom-tab-item-style

    .. md-tab-set::
        :class: custom-tab-set-style
        :name: ref_this_tab_set

        .. md-tab-item:: Local Ref

            A reference to this tab set renders like so:
            `tab set description <ref_this_tab_set>`.
            
            This syntax can only be used on the same page as the tab set.

        .. md-tab-item:: Cross-page Ref

            To cross-reference this tab set from a different page, use
            :ref:`tab set description <ref_this_tab_set>`

            Clearly this also works on the same page as the tab set.

        .. md-tab-item:: Custom CSS

            .. literalinclude:: _static/extra_css.css
                :language: css
                :start-at: /* ************************ custom-tab-set-style
                :end-before: /* *********************** custom-tab-item-style

.. confval:: md-tab-item

    This directive is used to create a tab within a set of content tabs. It requires a
    label as it's argument. Additionally, it also supports the ``:class:`` option, to
    optionally provide custom CSS classes to the tab's content (not the tab's label).

    .. code-block:: rst

        .. md-tab-set::

            .. md-tab-item:: Customized content
                :class: custom-tab-item-style

                This content could be styled differently from other page content.

            .. md-tab-item:: Custom CSS

                .. literalinclude:: _static/extra_css.css
                    :language: css
                    :start-at: /* *********************** custom-tab-item-style
                    :end-before: /* ************************* inline icon stuff

    .. md-tab-set::

        .. md-tab-item:: Customized content
            :class: custom-tab-item-style

            This content could be styled differently from other page content.

        .. md-tab-item:: Custom CSS

            .. literalinclude:: _static/extra_css.css
                :language: css
                :start-at: /* *********************** custom-tab-item-style
                :end-before: /* ************************* inline icon stuff

Typical examples are seen in this documentations'
`Custom admonitions <admonitions.html#custom-admonitions>`_ and
:ref:`Version Information Structure <version_info_example>` sections.