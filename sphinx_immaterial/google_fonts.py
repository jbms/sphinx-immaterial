"""Downloads the user-requested Google Fonts and includes them in the output.

This ensures the generated output does not depend on any external servers.

Additionally, the fonts are used by the graphviz extension.
"""

import asyncio
import concurrent.futures
import hashlib
import io
import json
import os
import re
from typing import Dict, List, Set, Tuple, Optional, cast, Any
import urllib.parse

import sphinx.application
import sphinx.config
import sphinx.util.logging

from .css_and_javascript_bundles import add_global_css
from .external_resource_cache import get_url, get_cache_dir

logger = sphinx.util.logging.getLogger(__name__)

# https://stackoverflow.com/questions/25011533/google-font-api-uses-browser-detection-how-to-get-all-font-variations-for-font
_FONT_FORMAT_USER_AGENT = {
    "ttf": "Safari 3.1 Mozilla/5.0 (Macintosh; U; PPC Mac OS X 10_5_2; en-gb) AppleWebKit/526+ (KHTML, like Gecko) Version/3.1 iPhone",
    "woff": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36",
    # "Safari 6.0 Mozilla/5.0 (iPad; CPU OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5355d Safari/8536.25",
    # 'woff2': 'Firefox 36.0 Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0',
}


_CSS_URL_PATTERN = re.compile(r"url\(([^\)]+)\)")

_FILE_EXT_PATTERN = re.compile(r".*(\.[^\.]+)")


def _extract_urls(css_content: bytes) -> Set[str]:
    urls = set()
    for m in _CSS_URL_PATTERN.finditer(css_content.decode("utf-8")):
        urls.add(m.group(1))
    return urls


def _adjust_css_urls(css_content: bytes, renamed_fonts: Dict[str, str]) -> str:
    css_text = css_content.decode("utf-8")
    return _CSS_URL_PATTERN.sub(
        lambda m: f"url(fonts/{renamed_fonts[m.group(1)]})", css_text
    )


_MAX_CONCURRENT_FETCHES_KEY = "sphinx_immaterial_font_fetch_max_workers"
_MAX_CONCURRENT_FETCHES_ENV_KEY = "SPHINX_IMMATERIAL_FONT_FETCH_MAX_WORKERS"

_TTF_FONT_PATHS_KEY = "sphinx_immaterial_ttf_font_paths"


def add_google_fonts(app: sphinx.application.Sphinx, fonts: List[str]):
    cache_dir = os.path.join(get_cache_dir(app), "google_fonts")
    static_dir = os.path.join(app.outdir, "_static")
    max_workers: Optional[int] = cast(
        int, app.config.config_values.get(_MAX_CONCURRENT_FETCHES_KEY, 128)
    )
    if _MAX_CONCURRENT_FETCHES_ENV_KEY in os.environ:
        try:
            max_workers = int(os.environ[_MAX_CONCURRENT_FETCHES_ENV_KEY])
        except ValueError:
            logger.warning(
                "Environment variable, %s, must be an integer value.",
                _MAX_CONCURRENT_FETCHES_ENV_KEY,
            )
    if max_workers is not None and max_workers <= 0:
        max_workers = None  # use default from ThreadPoolExecutor
    # _static path
    font_dir = os.path.join(static_dir, "fonts")
    os.makedirs(font_dir, exist_ok=True)

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:

        def to_thread(fn, *args, **kwargs) -> asyncio.Future:
            return asyncio.wrap_future(executor.submit(fn, *args, **kwargs))

        async def fetch_font(font: str, style: str):
            css_url = f"https://fonts.googleapis.com/css?family={urllib.parse.quote(font)}:{style}"

            css_content_future = asyncio.gather(
                *[
                    to_thread(
                        get_url,
                        cache_dir,
                        css_url,
                        headers={"user-agent": user_agent},
                    )
                    for user_agent in _FONT_FORMAT_USER_AGENT.values()
                ]
            )

            css_content = dict(
                zip(_FONT_FORMAT_USER_AGENT.keys(), await css_content_future)
            )

            font_files = set()
            ttf_font_files = None

            for font_format, css_data in css_content.items():
                urls = _extract_urls(css_data)
                font_files.update(urls)
                if font_format == "ttf":
                    ttf_font_files = urls

            font_data_futures = asyncio.gather(
                *[to_thread(get_url, cache_dir, font_url) for font_url in font_files]
            )

            all_font_data = dict(zip(font_files, await font_data_futures))

            renamed_fonts = {}

            for font_url, font_data in all_font_data.items():
                h = hashlib.sha256(font_data).hexdigest()[:32]
                m = _FILE_EXT_PATTERN.fullmatch(font_url)
                if m is not None:
                    file_ext = m.group(1)
                else:
                    file_ext = ""
                new_name = h + file_ext
                renamed_fonts[font_url] = new_name
                with open(os.path.join(font_dir, new_name), "wb") as f:
                    f.write(font_data)
            adjusted_css_content = {
                font_format: _adjust_css_urls(css_data, renamed_fonts)
                for font_format, css_data in css_content.items()
            }

            ttf_font_path = None

            if ttf_font_files is None or len(ttf_font_files) != 1:
                logger.error(
                    "Expected 1 TTF font for %s:%s but received: %r",
                    font,
                    style,
                    css_content["ttf"],
                )
            else:
                ttf_font_url = next(iter(ttf_font_files))
                ttf_font_path = renamed_fonts[ttf_font_url]

            return adjusted_css_content, ttf_font_path

        async def do_fetch():
            css_future_keys = []
            css_futures = []
            # Fetch list of fonts
            font_metadata = json.loads(
                get_url(cache_dir, "https://fonts.google.com/metadata/fonts").decode(
                    "utf-8"
                )
            )
            font_families = {
                item["family"]: item for item in font_metadata["familyMetadataList"]
            }
            for font in fonts:
                metadata = font_families.get(font)
                if metadata is None:
                    logger.error(
                        "Invalid font family %r, available font families are: %r",
                        font,
                        sorted(font_families),
                    )
                    continue
                for variant in cast(
                    Dict[str, Dict[str, Any]], metadata["fonts"]
                ).keys():
                    css_future_keys.append((font, variant))
                    css_futures.append(fetch_font(font, variant))
            css_content = dict(zip(css_future_keys, await asyncio.gather(*css_futures)))
            return css_content

        # Note: Placing the asyncio.run() into a separate thread mitigates
        #       issues if we're running in an environment with a loop already
        #       running (like within the Esbonio language server).  Technically
        #       that'll block that loop, but it's better than causing a crash.
        css_content = executor.submit(lambda: asyncio.run(do_fetch())).result()

    # Write fonts css file
    ttf_font_paths = {}
    css_data = io.StringIO()
    for key, (css_format_content, ttf_font_path) in css_content.items():
        ttf_font_paths[key] = os.path.join(font_dir, ttf_font_path)
        for content in css_format_content.values():
            css_data.write("".join(re.split(r"(?:\s*\n\s*|/\*.*\*/)", content)))
    add_global_css(app, code=css_data.getvalue())
    setattr(app, _TTF_FONT_PATHS_KEY, ttf_font_paths)


def get_ttf_font_paths(
    app: sphinx.application.Sphinx,
) -> Optional[Dict[Tuple[str, str], str]]:
    if hasattr(app, _TTF_FONT_PATHS_KEY):
        return getattr(app, _TTF_FONT_PATHS_KEY)
    return None


def _builder_inited(app: sphinx.application.Sphinx):
    font_options = app.config["html_theme_options"]["font"]
    if not font_options:
        return
    add_google_fonts(app, list(font_options.values()))


def setup(app: sphinx.application.Sphinx):
    app.setup_extension("sphinx_immaterial.external_resource_cache")
    app.connect("builder-inited", _builder_inited)
    app.add_config_value(
        _MAX_CONCURRENT_FETCHES_KEY, default=128, rebuild="", types=int
    )

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
