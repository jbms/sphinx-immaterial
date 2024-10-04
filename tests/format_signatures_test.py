import sphinx.addnodes


TEST_SIGNATURES = {
    "cpp_function": "cpp:function:: void foo(int something, int something_else, bool third_param, bool fourth_param, int fifth_param)",
    "cpp_function_long": r"cpp:function:: template <typename T, \
                                       typename U = void, \
                                       int AnotherParameter = 42> \
                             requires std::is_const_v<T> \
                             const MyType LongFunctionSignatureExample(\
                               const MyType bar, \
                               uint8_t* arr, \
                               unsigned int len = DEFAULT_LENGTH, \
                               bool baz = false)",
    "cpp_function_long_return_type": r"cpp:function:: std::integral_constant<ptrdiff_t, N> tensorstore::GetStaticOrDynamicExtent(span<X, N>);",
    "py_function": r"py:function:: some_module.method_name( \
                              some_parameter_with_a_long_name: \
                                collections.abc.MutableMapping[\
                                  tuple[str, float, numbers.Real], \
                                  dict[int, tuple[list[frozenset[int]]]]], \
                            ) -> collections.abc.MutableMapping[\
                                   tuple[str, float, numbers.Real], \
                                   dict[int, tuple[list[frozenset[int]]]]]",
}


def test_format_signatures(immaterial_make_app, snapshot):
    app = immaterial_make_app(
        extra_conf="""
extensions.append("sphinx_immaterial.apidoc.format_signatures")
object_description_options = [
    ("cpp:.*", dict(clang_format_style={"BasedOnStyle": "LLVM"})),
    ("py:.*", dict(black_format_style={})),
]
        """,
        files={
            "index.rst": "\n\n".join(
                f"""
.. {directive}

   Synopsis goes here.
"""
                for directive in TEST_SIGNATURES.values()
            )
        },
    )

    app.build()

    assert not app._warning.getvalue()

    doc = app.env.get_and_resolve_doctree("index", app.builder)

    formatted_signatures = {
        identifier: signature
        for identifier, signature in zip(
            TEST_SIGNATURES.keys(),
            doc.findall(condition=sphinx.addnodes.desc_signature),
        )
    }
    for identifier in TEST_SIGNATURES.keys():
        node = formatted_signatures[identifier]
        snapshot.assert_match(node.astext(), f"{identifier}_astext.txt")
