import shutil
from pathlib import Path
from typing import Any, Dict, Set, cast

import docutils.nodes
from sphinx import version_info as sphinx_version
from sphinx.application import Sphinx
from sphinx.config import Config
from sphinx.domains.math import MathDomain
from sphinx.environment import BuildEnvironment
from sphinx.errors import ExtensionError
from sphinx.ext.mathjax import MATHJAX_URL

_USES_MATHJAX_KEY = "SPHINX_IMMATERIAL_USES_MATHJAX"
_DOCS_WITH_MATH_KEY = "SPHINX_IMMATERIAL_DOCS_WITH_MATH"


def _docs_with_math(env: BuildEnvironment) -> Set[str]:
    docs = getattr(env, _DOCS_WITH_MATH_KEY, None)
    if docs is None:
        docs = set()
        setattr(env, _DOCS_WITH_MATH_KEY, docs)
    return docs


def _is_math_node(node: docutils.nodes.Node) -> bool:
    return isinstance(node, (docutils.nodes.math, docutils.nodes.math_block))


def doctree_has_equations(app: Sphinx, doctree: docutils.nodes.document) -> None:
    """Records which documents contain equations.

    Unlike ``html-page-context`` (which, in a parallel build, is emitted in
    subprocesses whose env changes are discarded), data recorded while reading
    is merged back into the main process via ``env-merge-info``.

    Only called when sphinx is v8.2 or newer.
    """
    if any(doctree.findall(_is_math_node)):
        _docs_with_math(app.env).add(app.env.docname)


def env_purge_doc(app: Sphinx, env: BuildEnvironment, docname: str) -> None:
    """Only called when sphinx is v8.2 or newer."""
    _docs_with_math(env).discard(docname)


def env_merge_info(
    app: Sphinx, env: BuildEnvironment, docnames: Set[str], other: BuildEnvironment
) -> None:
    """Only called when sphinx is v8.2 or newer."""
    _docs_with_math(env).update(_docs_with_math(other) & set(docnames))


def page_has_equations(
    app: Sphinx,
    pagename: str,
    templatename: str,
    context: dict,
    doctree: docutils.nodes.Node,
) -> None:
    """Determines if mathjax dist is need on a per page basis.

    Only called when sphinx is v8.2 or newer.
    """

    if context.get("has_maths_elements", False):
        setattr(app.builder.env, _USES_MATHJAX_KEY, True)


def copy_mathjax_dist(app: Sphinx) -> None:
    if (
        app.builder.format != "html" or app.builder.math_renderer_name != "mathjax"  # type: ignore[attr-defined]
    ):
        return
    if not app.config.mathjax_path:
        raise ExtensionError(
            "mathjax_path config value must be set for the mathjax extension to work"
        )
    if (
        "mathjax_path" in app.config
        and app.config["mathjax_path"] != "mathjax/tex-mml-chtml.js"
    ):
        return  # not using theme's cache of mathjax dist

    uses_mathjax = False
    if sphinx_version[:3] < (8, 2):
        domain = cast(MathDomain, app.env.get_domain("math"))
        uses_mathjax = domain.has_equations()
    elif getattr(app.env, _USES_MATHJAX_KEY, False) is True or _docs_with_math(app.env):
        uses_mathjax = True
    if app.registry.html_assets_policy == "always" or uses_mathjax:
        # copy mathjax fonts only if equations exists
        shutil.copytree(
            str(Path(__file__).parent / "bundles" / "mathjax"),
            str(Path(app.outdir, "_static", "mathjax")),
            dirs_exist_ok=True,  # for consecutive builds
        )


def build_finished(app: Sphinx, exc: Exception | None):
    """Only called when sphinx is v8.2 or newer."""
    if exc is None:
        copy_mathjax_dist(app)


def env_updated(app: Sphinx, env: BuildEnvironment):
    """Only called when sphinx is older than v8.2."""
    copy_mathjax_dist(app)


def _config_inited(app: Sphinx, config: Config) -> None:
    """Inject path to local cache of mathjax dist.
    Sphinx machinery will do the rest of the work for us."""
    if "mathjax_path" in config:
        is_default = config["mathjax_path"] == MATHJAX_URL
        if is_default:
            config["mathjax_path"] = "mathjax/tex-mml-chtml.js"

            assert "mathjax_options" in config
            mathjax_options: Dict[str, Any] = config["mathjax_options"]
            # async attr is not applicable as the script is self-hosted
            mathjax_options.update({"id": "MathJax-script", "async": None})


def setup(app: Sphinx):
    app.connect("config-inited", _config_inited)
    if sphinx_version[:3] >= (8, 2):
        app.connect("doctree-read", doctree_has_equations)
        app.connect("env-purge-doc", env_purge_doc)
        app.connect("env-merge-info", env_merge_info)
        app.connect("html-page-context", page_has_equations)
        app.connect("build-finished", build_finished)
    else:
        app.connect("env-updated", env_updated)
    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
