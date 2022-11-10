class Foo:
    @classmethod
    def my_classmethod(cls, arg: str) -> int:
        return 1

    @staticmethod
    def my_staticmethod(arg: str) -> int:
        return 1

    def my_method(self, arg: str) -> int:
        return 1
