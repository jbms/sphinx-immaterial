import docutils.nodes
import sphinx
import sphinx.domains.python
import sphinx.environment
import sphinx.addnodes


def _monkey_patch_python_parse_arglist():
    """Ensures default values in signatures are styled as code."""

    if sphinx.version_info >= (7, 3):
        orig_parse_arglist = sphinx.domains.python._annotations._parse_arglist  # type: ignore[attr-defined]
    else:
        orig_parse_arglist = sphinx.domains.python._parse_arglist

    def parse_arglist(
        arglist: str, *args, **kwargs
    ) -> sphinx.addnodes.desc_parameterlist:
        result = orig_parse_arglist(arglist, *args, **kwargs)
        for node in result.findall(condition=docutils.nodes.inline):
            if "default_value" not in node["classes"]:
                continue
            node.replace_self(
                docutils.nodes.literal(
                    text=node.astext(),
                    classes=["code", "python", "default_value"],
                    language="python",
                )
            )
        return result

    if sphinx.version_info >= (7, 3):
        sphinx.domains.python._annotations._parse_arglist = parse_arglist  # type: ignore[attr-defined]
        sphinx.domains.python._object._parse_arglist = parse_arglist  # type: ignore[attr-defined]
    else:
        sphinx.domains.python._parse_arglist = parse_arglist


_monkey_patch_python_parse_arglist()
