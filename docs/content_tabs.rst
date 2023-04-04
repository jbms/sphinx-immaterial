.. _sphinx-design tabs: https://sphinx-design.readthedocs.io/en/furo-theme/tabs.html

Content tabs
============

.. note::
    This document discusses content tabs, not navigation tabs.

Use of `content tabs in the mkdocs-material <https://squidfunk.github.io/mkdocs-material/reference/content-tabs/>`_
theme relies on a markdown extension that isn't used in the world of Sphinx. Instead,
the sphinx-immaterial theme provides its own directives to make use of content tabs.

.. rst:directive:: md-tab-set

    Each set of tabs on a page must begin with a `md-tab-set` directive. This directive
    only accepts children that are `md-tab-item` directives.

    .. rst:directive:option:: class
        :type: string

        A space delimited list of qualified names that get used as the HTMl element's
        ``class`` attribute.

    .. rst:directive:option:: name
        :type: string

        A qualified name that get used as the HTML element's ``id`` attribute.

        Use the `ref` role to reference the element by name.

    This directive supports ``:class:`` and ``:name:`` options to use custom CSS classes
    and reference links (respectively).

    .. rst-example:: ``md-tab-set`` Example

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

                Clearly, this also works on the same page.

            .. md-tab-item:: Custom CSS

                .. literalinclude:: _static/extra_css.css
                    :language: css
                    :start-after: /* ************************ custom-tab-set-style
                    :end-before: /* *********************** custom-tab-item-style


.. rst:directive:: md-tab-item

    This directive is used to create a tab within a set of content tabs. It requires a
    label as it's argument.

    .. rst:directive:option:: class
        :type: string

        A space delimited list of qualified names that get used as the HTMl element's
        ``class`` attribute.

        Use the ``:class:`` option to optionally provide custom CSS classes to the tab's content
        (not the tab's label).

        .. rst-example:: ``md-tab-item`` Example

            .. md-tab-set::

                .. md-tab-item:: Customized content
                    :class: custom-tab-item-style

                    This content could be styled differently from other page content.

                .. md-tab-item:: Custom CSS

                    .. literalinclude:: _static/extra_css.css
                        :language: css
                        :start-after: /* *********************** custom-tab-item-style
                        :end-before: /* *********************** inline icon pulsing-heart style

.. _linked_tabs:

Linked tabs
-----------

Content tabs that share the same label can be selected synchronously by adding
:python:`"content.tabs.link"` to the list of :themeconf:`features` in conf.py.

.. code-block:: python
    :caption: in conf.py

    html_theme_options = {
        "features": [
            "content.tabs.link",
        ],

Synchronized selection will automatically persist across separate pages. Contradictory to the
equivalent implementation in mkdocs-material theme, the :python:`"navigation.instant"` feature
does not need to be explicitly specified.

.. important::
    Linked content tabs must share the same **exact** label. Meaning, the argument given to the
    :rst:dir:`md-tab-item` must be exactly the same (case sensitive) across all content tabs that
    shall be synchronized.

.. rst-example:: Linked content tabs example

    .. md-tab-set::

        .. md-tab-item:: Python

            .. code-block:: python

                def main():
                    print("Hello world!")

        .. md-tab-item:: C++

            .. code-block:: cpp

                #include <iostream>

                int main(void) {
                    std::cout << "Hello world!" << std::endl;
                    return 0;
                }


    .. md-tab-set::

        .. md-tab-item:: C only

            .. code-block:: c

                #include <stdio.h>

                int main(void) {
                    printf("Hello world!\n");
                    return 0;
                }

        .. md-tab-item:: C++

            .. code-block:: cpp

                #include <iostream>

                int main(void) {
                    std::cout << "Hello world!" << std::endl;
                    return 0;
                }

        .. md-tab-item:: Python

            .. code-block:: python

                def main():
                    print("Hello world!")
