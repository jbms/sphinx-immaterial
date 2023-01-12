"""Bundles CSS and JavaScript resources."""

import hashlib
import json
import os
import pathlib
from typing import NamedTuple, Optional, List

import sphinx.application
import sphinx.environment


class Entry(NamedTuple):
    code: str
    sourcemap: Optional[str]
    priority: int


_CSS_KEY = "_sphinx_immaterial_global_css"
_JAVASCRIPT_KEY = "_sphinx_immaterial_global_javascript"
_BUNDLE_SOURCE_MAPS_KEY = "sphinx_immaterial_bundle_source_maps"


def _get_css_entries(app: sphinx.application.Sphinx) -> List[Entry]:
    entries = getattr(app, _CSS_KEY, None)
    if entries is None:
        entries = []
        setattr(app, _CSS_KEY, entries)
    return entries


def _get_javascript_entries(app: sphinx.application.Sphinx) -> List[Entry]:
    entries = getattr(app, _JAVASCRIPT_KEY, None)
    if entries is None:
        entries = []
        setattr(app, _JAVASCRIPT_KEY, entries)
    return entries


def add_global_css(
    app: sphinx.application.Sphinx,
    code: str,
    sourcemap: Optional[str] = None,
    priority: int = 500,
):
    _get_css_entries(app).append(
        Entry(code=code, sourcemap=sourcemap, priority=priority)
    )


def add_global_javascript(
    app: sphinx.application.Sphinx,
    code: str,
    sourcemap: Optional[str] = None,
    priority: int = 500,
):
    _get_javascript_entries(app).append(
        Entry(code=code, sourcemap=sourcemap, priority=priority)
    )


def generate_bundle(
    app: sphinx.application.Sphinx,
    env: sphinx.environment.BuildEnvironment,
    entries: List[Entry],
    source_mapping_url_prefix: str,
    source_mapping_url_suffix: str,
    output_prefix: str,
    output_ext: str,
) -> str:
    entries.sort(key=lambda e: e.priority)

    # Use the special "sections" support in Source Map v3 to combine source maps
    # without needing to decode them.
    #
    # https://sourcemaps.info/spec.html
    sourcemap_sections = []
    lines: List[str] = []

    entries.sort(key=lambda entry: entry.priority)
    for entry in entries:
        entry_lines = [
            x
            for x in entry.code.rstrip().splitlines()
            if not x.startswith(source_mapping_url_prefix)
        ]
        offset = len(lines)
        lines.extend(entry_lines)
        if entry.sourcemap:
            sourcemap = json.loads(entry.sourcemap)
            sourcemap_sections.append(
                {"offset": {"line": offset, "column": 0}, "map": sourcemap}
            )
    lines.append("")
    output_data = "\n".join(lines).encode("utf-8")

    # hash data and write to generated file
    output_data_hash = hashlib.sha256(output_data).hexdigest()
    static_dir = pathlib.Path(app.outdir) / "_static"
    output_path = f"{output_prefix}.{output_data_hash[:17]}.min.{output_ext}"
    output_path_obj = static_dir / output_path
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    if sourcemap_sections and getattr(app.config, _BUNDLE_SOURCE_MAPS_KEY):
        sourcemap_path = output_path + ".map"
        (static_dir / sourcemap_path).write_text(
            json.dumps({"version": 3, "sections": sourcemap_sections}),
            encoding="utf-8",
        )
        output_data += (
            source_mapping_url_prefix
            + os.path.basename(sourcemap_path)
            + source_mapping_url_suffix
            + "\n"
        ).encode("utf-8")
    output_path_obj.write_bytes(output_data)
    return output_path


def generate_bundles(
    app: sphinx.application.Sphinx, env: sphinx.environment.BuildEnvironment
) -> None:
    """Bundles the theme CSS with any additional CSS added using `add_global_css`."""

    css_entries = list(_get_css_entries(app))

    # copy pre-minified CSS from theme's bundles
    theme_bundles = pathlib.Path(__file__).parent / "bundles" / "stylesheets"
    css_entries.append(
        Entry(
            code=(theme_bundles / "main.css").read_text(encoding="utf-8"),
            sourcemap=(theme_bundles / "main.css.map").read_text(encoding="utf-8"),
            priority=200,
        )
    )

    theme_options = app.config["html_theme_options"]
    if theme_options and "palette" in theme_options:
        css_entries.append(
            Entry(
                code=(theme_bundles / "palette.css").read_text(encoding="utf-8"),
                sourcemap=(theme_bundles / "palette.css.map").read_text(
                    encoding="utf-8"
                ),
                priority=200,
            )
        )

    css_bundle = generate_bundle(
        app=app,
        env=env,
        entries=css_entries,
        source_mapping_url_prefix="/*# sourceMappingURL=",
        source_mapping_url_suffix=" */",
        output_prefix="sphinx_immaterial_theme",
        output_ext="css",
    )
    app.add_css_file(css_bundle, priority=200)

    js_entries = list(_get_javascript_entries(app))
    js_entries.append(
        Entry(
            code=(
                pathlib.Path(__file__).parent / "bundles" / "javascripts" / "bundle.js"
            ).read_text(encoding="utf-8"),
            sourcemap=(
                pathlib.Path(__file__).parent
                / "bundles"
                / "javascripts"
                / "bundle.js.map"
            ).read_text(encoding="utf-8"),
            priority=200,
        )
    )

    js_bundle = generate_bundle(
        app=app,
        env=env,
        entries=js_entries,
        source_mapping_url_prefix="//# sourceMappingURL=",
        source_mapping_url_suffix="",
        output_prefix="sphinx_immaterial_theme",
        output_ext="js",
    )
    app.add_js_file(js_bundle, priority=200)


def setup(app: sphinx.application.Sphinx):
    app.connect("env-check-consistency", generate_bundles, priority=999)

    app.add_config_value(
        _BUNDLE_SOURCE_MAPS_KEY,
        default=False,
        rebuild="env",
        types=(bool,),
    )

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
