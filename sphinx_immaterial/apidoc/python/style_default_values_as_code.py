import docutils.nodes
import sphinx.domains.python
import sphinx.environment
import sphinx.addnodes


def _monkey_patch_python_parse_arglist():
    """Ensures default values in signatures are styled as code."""

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

    sphinx.domains.python._parse_arglist = parse_arglist


_monkey_patch_python_parse_arglist()
