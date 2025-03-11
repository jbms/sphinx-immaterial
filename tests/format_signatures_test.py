import re

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
    "py_function2": r"py:method:: create(chunk_key_encoding: zarr.core.chunk_key_encodings.ChunkKeyEncoding | tuple[Literal['default'], Literal['.', '/']] | tuple[Literal['v2'], Literal['.', '/']] | None = None) -> Array",
    # Note: This style of class signature, while valid Python syntax, is not
    # natively supported by Sphinx, but is produced by the
    # sphinx_immaterial.apidoc.python.apigen extension.
    "py_class": r"py:class:: my.very.long.python_class.ClassName(zarr.core.chunk_key_encodings.ChunkKeyEncoding1, zarr.core.chunk_key_encodings.GenericBase[tuple[str, float, numbers.Real], dict[int, str]])",
    # Sphinx-style "constructor" syntax, not valid Python syntax.
    "py_class_constructor": r"py:class:: zarr.abc.store.Store(*, read_only: bool = False)",
    "py_class_constructor_long": r"py:class:: zarr.abc.store.Store2(some_long_positional_parameter: collections.abc.MutableMapping[\
                                  tuple[str, float, numbers.Real], \
                                  dict[int, tuple[list[frozenset[int]]]]], *, read_only: bool = False)",
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

    def validate(doc):
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

            for refnode in node.findall(condition=sphinx.addnodes.pending_xref):
                refnode_text = refnode.astext()
                # Whitespace or added parentheses in a pending_xref node could
                # lead to slightly weird display of the hyperref. It is hard to
                # avoid entirely but should be avoided for these examples.
                assert not re.search(r"[ \t\n\(\)]", refnode_text)

    class AfterFormatSignatures(sphinx.transforms.SphinxTransform):
        # 1 larger than `FormatSignaturesTransform` priority
        default_priority = 1

        def apply(self, **kwargs):
            validate(self.document)

    # Validate before resolving references, to ensure that pending_xref nodes
    # don't contain whitespace.
    app.add_post_transform(AfterFormatSignatures)

    app.build()

    assert not app._warning.getvalue()

    # Validate that the correct formatted result is preserved after references
    # are resolved.
    doc = app.env.get_and_resolve_doctree("index", app.builder)
    validate(doc)
