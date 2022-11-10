from ._bravo import Bravo


class Alpha(Bravo):
    """
    Class Alpha docstring.
    """

    def my_method_Alpha(self) -> int:
        """
        This is my_method_Alpha.

        This is paragraph two.
        """
        return 1

    @property
    def my_property_Alpha(self) -> str:
        """
        This is my_property_Alpha.

        This is paragraph two.
        """
        return "alpha"
