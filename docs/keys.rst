Keys extension
==============

.. _pymdownx.keys: https://facelessuser.github.io/pymdown-extensions/extensions/keys/

This extension is meant to mimic the python markdown extension, `pymdownx.keys`_.
It provides an alternative implementation to Sphinx' :rst:role:`kbd` role.

It simply adds a role to invoke inline usage of keyboard keys with custom CSS provided by
the sphinx-immaterial theme.

.. success:: CSS is not included with this extension
    :collapsible:

    To add CSS to a theme that does not support this extension, try using:

    .. code-block:: CSS

        kbd[class^="key-"] {
          background-color: var(--md-typeset-kbd-color);
          border-radius: 0.1rem;
          box-shadow: 0 0.1rem 0 0.05rem var(--md-typeset-kbd-border-color), 0 0.1rem 0 var(--md-typeset-kbd-border-color), 0 -0.1rem 0.2rem var(--md-typeset-kbd-accent-color) inset;
          color: var(--md-default-fg-color);
          display: inline-block;
          font-size: 0.75em;
          padding: 0 0.6666666667em;
          vertical-align: text-top;
          word-break: break-word;
          font-feature-settings: "kern";
          font-family: var(--md-code-font-family);
        }

        .keys span {
          color: var(--md-default-fg-color--light);
          padding: 0 0.2em;
        }

.. _pymdownx-keys-req:

Markdown extension pre-requisite
--------------------------------

This pre-requisite does not mean Markdown support is enabled. However, this extension
does import the ``pymdownx.keymap_db`` module to use for the `keys_map` option's defaults.

To use this extension, the `pymdown-extensions
<https://pypi.org/project/pymdown-extensions/>`__ package needs to be installed.
You can either add it as a dependency directly, or depend on the ``keys``
optional feature of this package:

.. code-block:: shell

    python -m pip install sphinx-immaterial[keys]

And be sure to include the extension in your :file:`conf.py` file.

.. code-block:: python

    extensions = ["sphinx_immaterial.kbd_keys"]

.. _keys_extension_role:

Keys extension role
-------------------

.. rst:role:: keys

    The value of this role is interpreted as a keyboard key name. Each role invocation can
    describe multiple keys pressed simultaneously using the `keys_separator`.

    .. rst-example::

        :keys:`ctrl+alt+tab`

        :keys:`caps-lock`, :keys:`left-cmd+shift+a`, :keys:`backspace`

Keys extension configuration
----------------------------

These variables can be used to control the :rst:role:`keys` role behavior from the Sphinx
project's conf.py file.

.. confval:: keys_strict

    The containing span element can strictly follow HTML5 specifications by using the
    ``kbd`` tag instead of a ``span`` tag.

    The sphinx-immaterial theme does not adhere to the HTML5 strictness, therefore this
    `bool` option is disabled (`False`) by default.

.. confval:: keys_class

    The class attribute `str` value used in the containing span element. Defaults to ``"keys"``.

    Only change this if needed for your theme. The sphinx-immaterial theme is configured to use
    the default value.

.. confval:: keys_separator

    The `str` value used as the delimiter between keys. Defaults to ``"+"``.

    Changing this also requires changing the text provided to the :rst:role:`keys` role.

.. confval:: keys_map

    An additional `dict` where ``key: value`` pairs consist of:

    .. csv-table::
        :header: key, value

        aliased key-\ **name** inputs (preferably a CSS friendly name), displayed output `str`

    By default the english mappings are included from the `pymdownx package <pymdownx-keys-req>`.

    .. seealso::
        The tables in
        `pymdownx.keys`_ docs in `Extending/Modifying Key-Map Index
        <https://facelessuser.github.io/pymdown-extensions/extensions/keys/#extendingmodifying-key-map-index>`_.

    .. md-tab-set::

        .. md-tab-item:: conf.py

            Define the key name and give it a `str` value to display.

            In our case, "Awesome Key" will be shown for ``:keys:`my-special-key```.

            .. literalinclude:: conf.py
                :language: python
                :start-after: # -- sphinx_immaterial.keys extension options
                :end-before: # --

        .. md-tab-item::  CSS code

            Remember to prepend ``key-`` to whatever the `keys_map` key was. In our case,
            ``my-special-key`` turns into ``key-my-special-key``.

            .. literalinclude:: _static/extra_css.css
                :language: css
                :start-after: /* ************************* my-special-key style
                :end-before: /* **************************** custom-task-list style rules


        .. md-tab-item:: rST code

            Specify the key using a known name in the `keys_map` index.

            In our case, ``my-special-key`` to fetch the display text from `keys_map`.

            .. rst-example::

                :keys:`my-special-key` + :keys:`git` = :keys:`git+my-special-key`


            Use of spaces in a key name will result in CSS class that has hyphens instead of
            spaces in a lower case form of the given text. Therefore, entering
            ``My Special Key`` ignores the `keys_map` but still uses the
            ``key-my-special-key`` CSS class.

            .. rst-example::

                :keys:`My Special Key` + :keys:`Git` = :keys:`Git+My Special Key`
