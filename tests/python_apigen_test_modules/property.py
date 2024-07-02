class Example:
    @property
    def foo(self) -> int:
        return 42

    bar = foo


class InheritsFromExample(Example):
    foo = "abc"  # type: ignore[assignment]

    baz = Example.bar
