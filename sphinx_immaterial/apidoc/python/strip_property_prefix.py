from typing import Type, Union, List, cast

import docutils.nodes
import sphinx.domains.python


def _monkey_patch_python_get_signature_prefix(
    directive_cls: Type[sphinx.domains.python.PyObject],
) -> None:
    orig_get_signature_prefix = directive_cls.get_signature_prefix

    def get_signature_prefix(self, sig: str) -> Union[str, List[docutils.nodes.Node]]:
        prefix = orig_get_signature_prefix(self, sig)
        if not self.env.config.python_strip_property_prefix:
            return prefix
        if sphinx.version_info >= (4, 3):
            prefix = cast(List[docutils.nodes.Node], prefix)
            assert isinstance(prefix, list)
            for prop_idx, node in enumerate(prefix):
                if node == "property":
                    assert isinstance(
                        prefix[prop_idx + 1], sphinx.addnodes.desc_sig_space
                    )
                    prefix = list(prefix)
                    del prefix[prop_idx : prop_idx + 2]
                    break
            return prefix
        prefix = cast(str, prefix)  # type: ignore
        assert isinstance(prefix, str)
        parts = prefix.strip().split(" ")
        if "property" in parts:
            parts.remove("property")
        if parts:
            return " ".join(parts) + " "
        return ""

    directive_cls.get_signature_prefix = get_signature_prefix  # type: ignore


_monkey_patch_python_get_signature_prefix(sphinx.domains.python.PyFunction)
_monkey_patch_python_get_signature_prefix(sphinx.domains.python.PyMethod)
_monkey_patch_python_get_signature_prefix(sphinx.domains.python.PyProperty)


def setup(app: sphinx.application.Sphinx):
    app.add_config_value(
        "python_strip_property_prefix", default=False, rebuild="env", types=(bool,)
    )
    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
