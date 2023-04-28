from pathlib import Path
import shutil
from typing import Dict, Any, cast
from sphinx.application import Sphinx
from sphinx.config import Config
from sphinx.errors import ExtensionError
from sphinx.ext.mathjax import MATHJAX_URL, MathDomain


def copy_mathjax_dist(
    app: Sphinx,
    pagename: str,
    templatename: str,
    context: Dict[str, Any],
    event_arg: Any,
) -> None:
    if (
        app.builder.format != "html"
        or app.builder.math_renderer_name != "mathjax"  # type: ignore[attr-defined]
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

    domain = cast(MathDomain, app.env.get_domain("math"))
    if app.registry.html_assets_policy == "always" or domain.has_equations(pagename):
        # copy mathjax fonts only if equations exists (and not already done)
        dst = Path(app.outdir, "_static", "mathjax")
        if Path(app.outdir, "_static", dst).exists():
            return
        shutil.copytree(
            str(Path(__file__).parent / "static" / "mathjax"),
            str(dst),
        )


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
    app.connect("html-page-context", copy_mathjax_dist)
    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
