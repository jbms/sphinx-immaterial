"""Sphinx-Immaterial theme."""

import os
import re
from urllib.parse import urlparse
from typing import cast, List, Type, Dict, Mapping, Optional

import docutils.nodes
from sphinx.application import Sphinx
import sphinx.builders
import sphinx.builders.html
import sphinx.theming
import sphinx.util.logging
import sphinx.util.fileutil
import sphinx.util.matching
import sphinx.util.docutils
import sphinx.writers.html5
from sphinx import version_info

from . import html_translator_mixin
from .apidoc import apidoc_formatting
from .apidoc import fix_sphinx_issue_11147  # noqa: F401
from . import nav_adapt
from . import sections  # noqa: F401

logger = sphinx.util.logging.getLogger(__name__)


DEFAULT_THEME_OPTIONS = {
    "features": [],
    "font": {"text": "Roboto", "code": "Roboto Mono"},
    "plugins": {
        "search": {},
    },
    "icon": {},
    "repo_url": "",
    "edit_uri": "",
    "globaltoc_collapse": True,
    "toc_title": None,
    "toc_title_is_page_title": False,
}


def _get_html_builder(base_builder: Type[sphinx.builders.html.StandaloneHTMLBuilder]):
    """Returns a modified HTML translator."""

    class CustomHTMLBuilder(base_builder):  # type: ignore
        if version_info < (7, 2):
            css_files: List[sphinx.builders.html.Stylesheet]
        else:
            _css_files: List[sphinx.builders.html._assets._CascadingStyleSheet]  # type: ignore[name-defined]
        theme: sphinx.theming.Theme
        templates: sphinx.jinja2glue.BuiltinTemplateLoader

        @property
        def default_translator_class(self):
            return html_translator_mixin.get_html_translator(
                super().default_translator_class
            )

        def init_js_files(self):
            super().init_js_files()

            # Remove unnecessary scripts

            excluded_scripts = set(
                [
                    "_static/underscore.js",
                    "_static/doctools.js",
                    "_static/language_data.js",
                    "_static/documentation_options.js",
                    "_static/sphinx_highlight.js",
                ]
            )
            if nav_adapt.READTHEDOCS is None:
                excluded_scripts.add("_static/jquery.js")
                excluded_scripts.add("_static/_sphinx_javascript_frameworks_compat.js")
            if version_info < (7, 2):
                self.script_files: List[sphinx.builders.html.JavaScript] = [
                    x for x in self.script_files if x.filename not in excluded_scripts
                ]
            else:
                self._js_files: List[sphinx.builders.html._assets._JavaScript] = [  # type: ignore[name-defined]
                    x for x in self._js_files if x.filename not in excluded_scripts
                ]

        def init_css_files(self):
            super().init_css_files()

            # Remove unnecessary styles

            excluded = frozenset(
                [
                    "_static/pygments.css",
                    "_static/material.css",
                    "_static/basic.css",
                ]
            )
            if version_info < (7, 2):
                self.css_files = [
                    x
                    for x in cast(List[sphinx.builders.html.Stylesheet], self.css_files)
                    if x.filename not in excluded
                ]
            else:
                self._css_files = [
                    x
                    for x in cast(
                        List[sphinx.builders.html._assets._CascadingStyleSheet],  # type: ignore[name-defined]
                        self._css_files,
                    )
                    if x.filename not in excluded
                ]

        def gen_additional_pages(self):
            # Prevent the search.html page from being written since this theme provides
            # its own search results display that does not use it.
            search = self.search  # type: ignore[has-type]
            self.search = False
            super().gen_additional_pages()
            self.search = search

        def create_pygments_style_file(self):
            pass

        def copy_theme_static_files(self, context: Dict) -> None:
            # Modified from version in sphinx.builders.html.__init__.py to
            # exclude copying unused static files from `basic` theme.
            def onerror(filename: str, error: Exception) -> None:
                logger.warning(
                    "Failed to copy a file in html_static_file: %s: %r", filename, error
                )

            if self.theme:
                for entry in self.theme.get_theme_dirs()[::-1]:
                    if os.path.basename(entry) == "basic":
                        excluded_list = [
                            "**/.*",
                            "**/doctools.js",
                            "**/underscore*.js",
                            "**/*.png",
                            "**/basic.css_t",
                            "**/documentation_options.js_t",
                            "**/searchtools.js",
                            "**/sphinx_highlight.js",
                        ]
                        if nav_adapt.READTHEDOCS is None:
                            excluded_list.append("**/jquery*.js")
                            excluded_list.append(
                                "**/_sphinx_javascript_frameworks_compat.js"
                            )
                        excluded = sphinx.util.matching.Matcher(excluded_list)
                    else:
                        excluded = sphinx.util.matching.DOTFILES
                    sphinx.util.fileutil.copy_asset(
                        os.path.join(entry, "static"),
                        os.path.join(self.outdir, "_static"),
                        excluded=excluded,
                        context=context,
                        renderer=cast(
                            sphinx.util.template.BaseRenderer, self.templates
                        ),
                        onerror=onerror,
                    )

        def get_target_uri(self, docname: str, typ: Optional[str] = None) -> str:
            """Strips ``index.html`` suffix from URIs for cleaner links."""
            orig_uri = super().get_target_uri(docname, typ)
            if self.app.config["html_use_directory_uris_for_index_pages"]:
                index_suffix = "index" + self.link_suffix
                if orig_uri == index_suffix:
                    return ""
                if orig_uri.endswith("/" + index_suffix):
                    return orig_uri[: -len(index_suffix)]
            return orig_uri

    return CustomHTMLBuilder


def dict_merge(*dicts: Mapping):
    """Recursively merges the members of one or more dicts."""
    result: dict = {}
    for d in dicts:
        for k, v in d.items():
            if isinstance(v, Mapping) and k in result and isinstance(result[k], dict):
                result[k] = dict_merge(result[k], v)
            else:
                result[k] = v
    return result


def html_page_context(
    app: Sphinx,
    pagename: str,
    templatename: str,
    context: dict,
    doctree: docutils.nodes.Node,
):
    theme_options = app.config["html_theme_options"]
    theme_options = dict_merge(DEFAULT_THEME_OPTIONS, theme_options)

    builder = app.builder
    assert isinstance(builder, sphinx.builders.html.StandaloneHTMLBuilder)

    num_slashes = builder.get_target_uri(pagename).count("/")
    if num_slashes == 0:
        base_url = "."
    else:
        base_url = "/".join(".." for _ in range(num_slashes))

    version_config = None
    if theme_options.get("version_dropdown"):
        version_config = {
            "provider": "mike",
            "staticVersions": theme_options.get("version_info"),
            "versionPath": theme_options.get("version_json"),
        }

    analytics = None
    if theme_options.get("google_analytics"):
        # Parse old-style analytics config for backwards compatibility
        analytics = {
            "provider": "google",  # Google is the only provider currently supported
            "property": theme_options.get("google_analytics")[0],
        }
    if theme_options.get("analytics"):
        analytics = theme_options.get("analytics")

    extra = {
        "version": version_config,
        "social": theme_options.get("social"),
        "disqus": theme_options.get("disqus"),
        "manifest": theme_options.get("pwa_manifest"),
        "analytics": analytics,
        "alternate": theme_options.get("languages"),
    }
    scope = theme_options.get("scope")
    if scope is not None:
        extra["scope"] = scope

    context.update(
        config=dict_merge(
            context.get("config", {}),
            {
                "theme": theme_options,
                "site_url": theme_options.get("site_url"),
                "site_name": context["docstitle"],
                "repo_url": theme_options.get("repo_url"),
                "repo_name": theme_options.get("repo_name", None),
                "extra": extra,
                "plugins": theme_options.get("plugins"),
            },
        ),
        base_url=base_url,
    )


def _builder_inited(app: sphinx.application.Sphinx) -> None:
    # For compatibility with mkdocs
    if isinstance(app.builder, sphinx.builders.html.StandaloneHTMLBuilder):
        # Latex builder does not have a `templates` attribute
        app.builder.templates.environment.filters["url"] = lambda url: url


def _config_inited(
    app: sphinx.application.Sphinx, config: sphinx.config.Config
) -> None:
    """Merge defaults into theme options."""
    if config["language"] is None:
        config["language"] = "en"  # default to English language
    config["html_theme_options"] = dict_merge(
        DEFAULT_THEME_OPTIONS, config["html_theme_options"]
    )

    theme_options: dict = config["html_theme_options"]
    repo_url: Optional[str] = theme_options.get("repo_url", None)
    if not theme_options.get("repo_name", None) and repo_url:
        # auto-extract repo_name from repo_url
        url = urlparse(repo_url)
        if re.search("github|gitlab|bitbucket", url.netloc) is None:
            raise AttributeError(
                "'repo_url' does not use a github, gitlab, or bitbucket domain, so"
                " the `repo_name` must be set explicitly."
            )
        config["html_theme_options"]["repo_name"] = url.path.split("/")[2].rstrip(
            ".git"
        )


def setup(app: Sphinx):
    app.connect("config-inited", _config_inited)

    app.setup_extension("sphinx_immaterial.css_and_javascript_bundles")
    app.setup_extension("sphinx_immaterial.external_resource_cache")
    app.setup_extension("sphinx_immaterial.google_fonts")
    app.setup_extension("sphinx_immaterial.local_mathjax")

    app.setup_extension(apidoc_formatting.__name__)
    app.setup_extension("sphinx_immaterial.apidoc.python.default")
    app.setup_extension("sphinx_immaterial.apidoc.cpp.default")
    app.setup_extension(nav_adapt.__name__)
    app.setup_extension("sphinx_immaterial.postprocess_html")

    if sphinx.version_info < (5, 0):
        app.setup_extension("sphinx_immaterial.inlinesyntaxhighlight")

    app.setup_extension("sphinx_immaterial.apidoc.object_toc")
    app.setup_extension("sphinx_immaterial.search_adapt")
    app.setup_extension("sphinx_immaterial.apidoc.object_description_options")
    app.setup_extension("sphinx_immaterial.apidoc.wrap_signatures")
    app.setup_extension("sphinx_immaterial.apidoc.generic_synopses")

    app.connect("html-page-context", html_page_context)
    app.connect("builder-inited", _builder_inited)
    app.add_config_value(
        "html_use_directory_uris_for_index_pages", False, rebuild="html", types=bool
    )
    for builder in ("html", "dirhtml"):
        app.add_builder(
            _get_html_builder(
                cast(
                    Type[sphinx.builders.html.StandaloneHTMLBuilder],
                    app.registry.builders[builder],
                )
            ),
            override=True,
        )
    app.add_html_theme("sphinx_immaterial", os.path.abspath(os.path.dirname(__file__)))

    # register our custom directives/roles that are tied to this theme
    app.setup_extension("sphinx_immaterial.content_tabs")
    app.setup_extension("sphinx_immaterial.mermaid_diagrams")
    app.setup_extension("sphinx_immaterial.task_lists")
    app.setup_extension("sphinx_immaterial.code_annotations")
    app.setup_extension("sphinx_immaterial.default_literal_role")
    app.setup_extension("sphinx_immaterial.highlight_push_pop")
    app.setup_extension("sphinx_immaterial.inline_icons")
    app.setup_extension("sphinx_immaterial.custom_admonitions")

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
