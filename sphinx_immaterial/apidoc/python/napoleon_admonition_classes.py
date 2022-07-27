from typing import List

from sphinx.ext.napoleon.docstring import GoogleDocstring


def _monkey_patch_napoleon_admonition_classes():
    def _add_admonition_class(method_name: str, class_name: str) -> None:
        orig_method = getattr(GoogleDocstring, method_name)

        def wrapper(self: GoogleDocstring, section: str) -> List[str]:
            result = orig_method(self, section)
            result.insert(1, f"   :class: {class_name}")
            return result

        setattr(GoogleDocstring, method_name, wrapper)

    _add_admonition_class("_parse_examples_section", "example")


_monkey_patch_napoleon_admonition_classes()
