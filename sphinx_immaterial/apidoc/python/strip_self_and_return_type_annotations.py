import re

import sphinx.addnodes
import sphinx.application
import sphinx.config


def _maybe_strip_type_annotations(
    app: sphinx.application.Sphinx,
    domain: str,
    objtype: str,
    contentnode: sphinx.addnodes.desc_content,
) -> None:
    if domain != "py":
        return
    obj_desc = contentnode.parent
    assert isinstance(obj_desc, sphinx.addnodes.desc)
    strip_self_type_annotations = app.config.python_strip_self_type_annotations
    strip_return_type_annotations = app.config.python_strip_return_type_annotations
    for signode in obj_desc[:-1]:
        assert isinstance(signode, sphinx.addnodes.desc_signature)
        if strip_self_type_annotations:
            for param in signode.findall(condition=sphinx.addnodes.desc_parameter):
                if param.children[0].astext() == "self":
                    # Remove any annotations on `self`
                    del param.children[1:]
                break
        if strip_return_type_annotations is not None:
            fullname = signode.get("fullname")
            if fullname is None:
                # Python domain failed to parse the signature.  Just ignore it.
                continue
            modname = signode["module"]
            if modname:
                fullname = modname + "." + fullname
            if strip_return_type_annotations.fullmatch(fullname):
                # Remove return type.
                for node in signode.findall(condition=sphinx.addnodes.desc_returns):
                    node.parent.remove(node)


def _config_inited(
    app: sphinx.application.Sphinx, config: sphinx.config.Config
) -> None:
    if (
        config.python_strip_self_type_annotations
        or config.python_strip_return_type_annotations
    ):
        if isinstance(config.python_strip_return_type_annotations, str):
            setattr(
                config,
                "python_strip_return_type_annotations",
                re.compile(config.python_strip_return_type_annotations),
            )
        app.connect("object-description-transform", _maybe_strip_type_annotations)


def setup(app: sphinx.application.Sphinx):
    app.add_config_value(
        "python_strip_self_type_annotations", default=True, rebuild="env", types=(bool,)
    )
    app.add_config_value(
        "python_strip_return_type_annotations",
        default=r".*.(__setitem__|__init__)",
        rebuild="env",
        types=(re.Pattern, type(None)),  # type: ignore[arg-type]
    )
    app.connect("config-inited", _config_inited)

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
