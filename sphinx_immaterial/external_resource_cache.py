import asyncio
import concurrent.futures
import hashlib
import json
import os
import re
import tempfile
from typing import Dict, Optional, List, Set, Tuple
import urllib.parse

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
            except:  # pylint: disable=bare-except
                pass


def _get_default_cache_dir(config: sphinx.config.Config):
    cache_dir = os.environ.get("SPHINX_IMMATERIAL_EXTERNAL_RESOURCE_CACHE_DIR")
    if cache_dir is not None:
        return cache_dir

    return os.path.join(
        appdirs.user_cache_dir("sphinx_immaterial", "jbms"), "external_resources"
    )


_RESOURCE_CONFIG_KEY = "sphinx_immaterial_external_resource_cache_dir"

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


_MAX_CONCURRENT_FETCHES = 128

_TTF_FONT_PATHS_KEY = "sphinx_immaterial_ttf_font_paths"


def add_google_fonts(app: sphinx.application.Sphinx, fonts: List[str]):

    cache_dir = getattr(app.config, _RESOURCE_CONFIG_KEY)
    static_dir = os.path.join(app.outdir, "_static")
    # _static path
    font_dir = os.path.join(static_dir, "fonts")
    os.makedirs(font_dir, exist_ok=True)

    with concurrent.futures.ThreadPoolExecutor(max_workers=32) as executor:

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
            for font in fonts:
                for style in ["300", "300i", "400", "400i", "700", "700i"]:
                    css_future_keys.append((font, style))
                    css_futures.append(fetch_font(font, style))
            css_content = dict(zip(css_future_keys, await asyncio.gather(*css_futures)))
            return css_content

        css_content = asyncio.run(do_fetch())

    # Write fonts css file
    ttf_font_paths = {}
    with open(os.path.join(static_dir, "google_fonts.css"), "w", encoding="utf-8") as f:
        for key, (css_format_content, ttf_font_path) in css_content.items():
            ttf_font_paths[key] = os.path.join(font_dir, ttf_font_path)
            for content in css_format_content.values():
                f.write(content)

    app.add_css_file("google_fonts.css")
    setattr(app, _TTF_FONT_PATHS_KEY, ttf_font_paths)


def get_ttf_font_paths(app: sphinx.application.Sphinx) -> Dict[Tuple[str, str], str]:
    return getattr(app, _TTF_FONT_PATHS_KEY)


def _builder_inited(app: sphinx.application.Sphinx):
    font_options = app.config["html_theme_options"]["font"]
    if not font_options:
        return
    add_google_fonts(app, list(font_options.values()))


def setup(app: sphinx.application.Sphinx):
    app.add_config_value(
        _RESOURCE_CONFIG_KEY,
        default=_get_default_cache_dir,
        rebuild="env",
        types=(str,),
    )

    app.connect("builder-inited", _builder_inited)

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
