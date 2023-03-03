import hashlib
import json
import os
import tempfile
from typing import Dict, Optional, Any

import appdirs
import requests
import sphinx.application
import sphinx.config
import sphinx.util.logging

logger = sphinx.util.logging.getLogger(__name__)


def get_url(
    cache_dir: str, url: str, headers: Optional[Dict[str, str]] = None
) -> bytes:
    if headers is None:
        headers = {}
    req_json = {"url": url, "headers": headers}
    req_json_encoded = json.dumps(req_json).encode("utf-8")
    req_key = hashlib.sha256(req_json_encoded).hexdigest()

    resp_path = os.path.join(cache_dir, f"{req_key}.response")
    try:
        with open(resp_path, "rb") as f:
            return f.read()
    except FileNotFoundError:
        pass

    logger.info("Fetching: %s with %r", url, headers)
    r = requests.get(  # pylint: disable=missing-timeout
        url, headers=headers, stream=True
    )
    r.raise_for_status()

    response_content = r.content

    # Write request.
    req_path = os.path.join(cache_dir, f"{req_key}.request")
    os.makedirs(cache_dir, exist_ok=True)
    with open(req_path, "wb") as f:
        f.write(req_json_encoded)

    # Write response
    temp_name = None

    try:
        with tempfile.NamedTemporaryFile(
            dir=cache_dir, suffix=".tmp", prefix=req_key + ".request.", delete=False
        ) as f:
            temp_name = f.name
            f.write(response_content)
        os.replace(temp_name, resp_path)
        temp_name = None

        return response_content
    finally:
        if temp_name is not None:
            try:
                os.remove(temp_name)
            except (OSError, FileNotFoundError):
                pass


def _get_default_cache_dir(config: sphinx.config.Config):
    cache_dir = os.environ.get("SPHINX_IMMATERIAL_EXTERNAL_RESOURCE_CACHE_DIR")
    if cache_dir is not None:
        return cache_dir

    return os.path.join(
        appdirs.user_cache_dir("sphinx_immaterial", "jbms"), "external_resources"
    )


_RESOURCE_CONFIG_KEY = "sphinx_immaterial_external_resource_cache_dir"


def get_cache_dir(app: sphinx.application.Sphinx) -> str:
    return getattr(app.config, _RESOURCE_CONFIG_KEY)


def _config_inited(
    app: sphinx.application.Sphinx, config: sphinx.config.Config
) -> None:
    """Inject path to local cache of mathjax dist.
    Sphinx machinery will do the rest of the work for us."""
    if "mathjax_path" in config:
        config["mathjax_path"] = "tex-mml-chtml.js"

        assert "mathjax_options" in config
        mathjax_options: Dict[str, Any] = config["mathjax_options"]
        # async attr is not applicable as the script is self-hosted
        mathjax_options.update({"id": "MathJax-script", "async": None})


def setup(app: sphinx.application.Sphinx):
    app.add_config_value(
        _RESOURCE_CONFIG_KEY,
        default=_get_default_cache_dir,
        rebuild="env",
        types=(str,),
    )
    app.connect("config-inited", _config_inited)
    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
