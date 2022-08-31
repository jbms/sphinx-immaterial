import docutils.nodes
import sphinx.application
import sphinx.addnodes

from . import object_description_options
from .. import html_translator_mixin


def _wrap_signature(node: sphinx.addnodes.desc_signature, limit: int):
    """Wraps long function signatures.

    Adds the `sig-wrap` class which causes each parameter to be displayed on a
    separate line.
    """
    node_text = node.astext()
    if len(node_text) > limit:
        node["classes"].append("sig-wrap")


def _wrap_signatures(
    app: sphinx.application.Sphinx,
    domain: str,
    objtype: str,
    content: docutils.nodes.Element,
) -> None:
    env = app.env
    assert env is not None
    options = object_description_options.get_object_description_options(
        env, domain, objtype
    )
    if (
        not options["wrap_signatures_with_css"]
        or options.get("clang_format_style") is not None
    ):
        return
    signatures = content.parent[:-1]
    for signature in signatures:
        assert isinstance(signature, sphinx.addnodes.desc_signature)
        _wrap_signature(signature, options["wrap_signatures_column_limit"])


@html_translator_mixin.override
def visit_desc_parameter(
    self: html_translator_mixin.HTMLTranslatorMixin,
    node: sphinx.addnodes.desc_parameter,
    super_func: html_translator_mixin.BaseVisitCallback[sphinx.addnodes.desc_parameter],
) -> None:
    self.body.append('<span class="sig-param-decl">')
    super_func(self, node)


@html_translator_mixin.override
def depart_desc_parameter(
    self: html_translator_mixin.HTMLTranslatorMixin,
    node: sphinx.addnodes.desc_parameter,
    super_func: html_translator_mixin.BaseVisitCallback[sphinx.addnodes.desc_parameter],
) -> None:
    super_func(self, node)
    self.body.append("</span>")


def setup(app: sphinx.application.Sphinx):
    app.setup_extension("sphinx_immaterial.apidoc.object_description_options")
    app.connect("object-description-transform", _wrap_signatures, priority=1000)

    object_description_options.add_object_description_option(
        app, "wrap_signatures_with_css", type_constraint=bool, default=True
    )
    object_description_options.add_object_description_option(
        app, "wrap_signatures_column_limit", type_constraint=int, default=68
    )

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
