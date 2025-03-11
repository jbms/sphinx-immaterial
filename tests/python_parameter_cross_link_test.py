def test_python_parameter_cross_link(immaterial_make_app, snapshot):
    app = immaterial_make_app(
        files={
            "index.rst": r"""
.. py:function:: foo(x: int, *args: list[int], **kwargs: dict[str, int]) -> int

   Description goes here.

   :param x: X parameter.
   :param \*args: Args parameter.
   :param \*\*kwargs: Kwargs parameter.

"""
        },
    )

    app.build()

    assert not app._warning.getvalue()
