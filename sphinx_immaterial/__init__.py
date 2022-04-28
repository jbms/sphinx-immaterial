"""Sphinx-Immaterial theme."""

import os
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

from . import apidoc_formatting
from . import autodoc_property_type
from . import cpp_domain_fixes
from . import inlinesyntaxhighlight
from . import generic_synopses
from . import nav_adapt
from . import object_toc
from . import postprocess_html
from . import python_domain_fixes
from . import python_type_annotation_transforms
from . import search_adapt
from .details_patch import monkey_patch_details_run

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


def _get_html_translator(
    base_translator: Type[sphinx.writers.html5.HTML5Translator],
) -> Type[sphinx.writers.html5.HTML5Translator]:
    class CustomHTMLTranslator(
        apidoc_formatting.HTMLTranslatorMixin, base_translator
    ):  # pylint: disable=abstract-method
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            # Ensure pygments uses <code> elements, for compatibility with the
            # mkdocs-material CSS which expects that.
            self.highlighter.formatter_args.update(wrapcode=True)

            # Ensure all tables are marked as data tables.  The material CSS only
            # applies to tables with this class, in order to leave tables used for
            # layout purposes alone.
            self.settings.table_style = ",".join(
                self.settings.table_style.split(",") + ["data"]
            )

            # Ensure classes like `s` (used for string literals in code
            # highlighting) aren't converted to `<s>` elements (strikethrough).
            # Sphinx already overrides this, but for some reason due to
            # `__init__` invocation order it gets overridden.
            self.supported_inline_tags = set()

        def visit_section(self, node: docutils.nodes.section) -> None:
            # Sphinx normally writes sections with a section heading as:
            #
            #     <div id="identifier" class="section"><hN>...</hN>...</div>
            #
            # but that is incompatible with the way scroll-margin-top and the
            # `:target` selector are used in the mkdocs-material CSS.  For
            # compatibility with mkdocs-material, we strip the outer `<div>` and
            # instead add the `id` to the inner `<hN>` element.
            #
            # That is accomplished by overriding `visit_section` and
            # `depart_section` not to add the `<div>` and `</div>` tags, and also
            # modifying `visit_title` to insert the `id`.
            self.section_level += 1

        def depart_section(self, node: docutils.nodes.section) -> None:
            self.section_level -= 1

        def visit_title(self, node: docutils.nodes.title) -> None:
            if isinstance(node.parent, docutils.nodes.section):
                if node.parent.get("ids") and not node.get("ids"):
                    node["ids"] = node.parent.get("ids")
                    super().visit_title(node)
                    del node["ids"]
                    return
            super().visit_title(node)

    return CustomHTMLTranslator


def _get_html_builder(base_builder: Type[sphinx.builders.html.StandaloneHTMLBuilder]):
    """Returns a modified HTML translator."""

    class CustomHTMLBuilder(base_builder):

        css_files: List[sphinx.builders.html.Stylesheet]
        theme: sphinx.theming.Theme
        templates: sphinx.jinja2glue.BuiltinTemplateLoader

        @property
        def default_translator_class(self):
            return _get_html_translator(super().default_translator_class)

        def init_js_files(self):
            super().init_js_files()

            # Remove unnecessary scripts

            excluded_scripts = set(
                [
                    "_static/underscore.js",
                    "_static/doctools.js",
                    "_static/language_data.js",
                    "_static/documentation_options.js",
                ]
            )
            if nav_adapt.READTHEDOCS is None:
                excluded_scripts.add("_static/jquery.js")
            self.script_files = [
                x for x in self.script_files if x.filename not in excluded_scripts
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
            self.css_files = [
                x
                for x in cast(List[sphinx.builders.html.Stylesheet], self.css_files)
                if x.filename not in excluded
            ]

        def gen_additional_pages(self):
            # Prevent the search.html page from being written since this theme provides
            # its own search results display that does not use it.
            search = self.search
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
                        ]
                        if nav_adapt.READTHEDOCS is None:
                            excluded_list.append("**/jquery*.js")
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
    result = {}
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

    num_slashes = pagename.count("/")
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

    context.update(
        config=dict_merge(
            context.get("config", {}),
            {
                "theme": theme_options,
                "site_url": theme_options.get("site_url"),
                "site_name": context["docstitle"],
                "repo_url": theme_options.get("repo_url"),
                "repo_name": theme_options.get("repo_name", None),
                "extra": {
                    "version": version_config,
                    "social": theme_options.get("social"),
                    "disqus": theme_options.get("disqus"),
                    "manifest": theme_options.get("pwa_manifest"),
                    "analytics": analytics,
                },
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
    # make code-blocks' line numbers be a separate column of a 1-row table
    config["html_codeblock_linenos_style"] = "table"  # default is "inline"
    config["html_theme_options"] = dict_merge(
        DEFAULT_THEME_OPTIONS, config["html_theme_options"]
    )


def setup(app):
    app.connect("config-inited", _config_inited)
    app.setup_extension(apidoc_formatting.__name__)
    app.setup_extension(python_domain_fixes.__name__)
    app.setup_extension(python_type_annotation_transforms.__name__)
    app.setup_extension(cpp_domain_fixes.__name__)
    app.setup_extension(nav_adapt.__name__)
    app.setup_extension(postprocess_html.__name__)
    app.setup_extension(inlinesyntaxhighlight.__name__)
    app.setup_extension(object_toc.__name__)
    app.setup_extension(search_adapt.__name__)
    app.setup_extension(generic_synopses.__name__)
    app.connect("html-page-context", html_page_context)
    app.connect("builder-inited", _builder_inited)
    app.add_config_value(
        "html_use_directory_uris_for_index_pages", False, rebuild="html", types=bool
    )

    app.add_builder(_get_html_builder(app.registry.builders["html"]), override=True)
    app.add_html_theme("sphinx_immaterial", os.path.abspath(os.path.dirname(__file__)))

    # register our custom adminition directive that are tied to the theme's CSS
    app.setup_extension("sphinx_immaterial.md_admonition")
    app.setup_extension("sphinx_immaterial.content_tabs")
    app.setup_extension("sphinx_immaterial.mermaid_diagrams")
    app.setup_extension("sphinx_immaterial.task_lists")

    # patch the details directive's run method
    monkey_patch_details_run()

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
