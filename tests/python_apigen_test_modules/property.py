class Example:
    @property
    def foo(self) -> int:
        return 42

    bar = foo


class InheritsFromExample(Example):
    foo = "abc"

    baz = Example.bar
