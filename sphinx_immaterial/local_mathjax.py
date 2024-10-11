from pathlib import Path
import shutil
from typing import Dict, Any, cast
from sphinx.application import Sphinx
from sphinx.config import Config
from sphinx.errors import ExtensionError
from sphinx.domains.math import MathDomain
from sphinx.ext.mathjax import MATHJAX_URL
from sphinx.environment import BuildEnvironment


def copy_mathjax_dist(app: Sphinx, env: BuildEnvironment) -> None:
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

    domain = cast(MathDomain, env.get_domain("math"))
    if app.registry.html_assets_policy == "always" or domain.has_equations():
        # copy mathjax fonts only if equations exists
        shutil.copytree(
            str(Path(__file__).parent / "bundles" / "mathjax"),
            str(Path(app.outdir, "_static", "mathjax")),
            dirs_exist_ok=True,  # for consecutive builds
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
    app.connect("env-updated", copy_mathjax_dist)
    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
