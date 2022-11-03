.. |semi-colon| replace:: semi-colon (``;``)
.. |comma| replace:: comma (``,``)

Inline icons
============

This theme has a builtin role to use icons within lines of text.

.. warning::
    Using icons in the table of contents or navigation menu is not supported.

.. rst:role:: si-icon

    Set the content of this role to a relative path of an SVG image (excluding the ``.svg`` file
    extension). This path shall be relative to
    
    - the ``.icons`` directory bundled with this theme (this takes precedence)
    - the documentation's static path(s) (set with `html_static_path` in conf.py)

    Optionally, a CSS class can be specified after the icon's path, but the path and CSS class
    **must** be separated by |semi-colon|. Do not use spaces. If specifying multiple CSS
    classes, then separate them with a |comma|.


Using inline icons
------------------

The following sets of icons are bundled with this theme:

.. rst-example:: Using a builtin icon

    - :si-icon:`material/material-design` `Material Design <https://materialdesignicons.com/>`_
    - :si-icon:`fontawesome/regular/font-awesome` `Font Awesome <https://fontawesome.com/search?m=free>`_
    - :si-icon:`octicons/mark-github-16` `Octicons <https://octicons.github.com/>`_
    - :si-icon:`simple/simpleicons` `Simple Icons <https://simpleicons.org/>`_

You can also browse these icons locally from the sphinx-immaterial theme's install path under
``path/to/sphinx-immaterial/sphinx_immaterial/.icons/``.

Using custom CSS
*****************

It is possible to add specific styles to certain inline icons. Simply append a |comma| separated
list of CSS classes, and don't forget to separate the icon's path and CSS classes with a
|semi-colon|.

.. rst-example:: Using an icon with custom CSS

    This is a paragraph with :si-icon:`fontawesome/solid/heart;pulsing-heart` an animated icon
    using the following CSS rules:

    .. literalinclude:: _static/extra_css.css
        :language: css
        :start-after: /* *********************** inline icon pulsing-heart style
        :end-before: /* ************************* badge style inline stuff

Custom inline icons
*******************

Custom icons can be added to the documentation's static files and referenced using the relative
path. For example, this documentation has added the Sphinx application's logo to its ``_static``
folder (which is specified using `html_static_path`).

.. figure:: _static/sphinx_logo.svg

    docs/_static/sphinx_logo.svg

.. note::
    The custom icon **must** be a SVG file!

    Ideally, the custom icon should have no embedded color or style information and use a
    transparent background. Conventionally, a SVG file is optimized using
    `SVGO <https://github.com/svg/svgo>`_ for which there are
    `various ways to use <https://github.com/svg/svgo#other-ways-to-use-svgo>`_.
    
    A dimension of 24 pixels (width and/or height) is preferred. Be mindful
    of the SVG's ``viewbox`` attribute as it must coincide with the path(s) maximum needed
    dimensions.


.. rst-example::

    This icon :si-icon:`sphinx_logo` is located in
    `docs/_static/sphinx_logo.svg
    <https://github.com/jbms/sphinx-immaterial/blob/main/docs/_static/sphinx_logo.svg>`_
