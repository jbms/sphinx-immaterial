"""Generates a search index for use by the lunr.js-based mkdocs-material search."""

import multiprocessing
import pathlib
from typing import Optional

import docutils.nodes
import jinja2.sandbox
import sphinx.application
import sphinx.util.logging
import sphinx.builders.html

from .plugins.search import plugin as search_plugin

logger = sphinx.util.logging.getLogger(__name__)

_SEARCH_QUEUE_KEY = "_sphinx_immaterial_search_entry_queue"
_SEARCH_CONFIG = "_sphinx_immaterial_search_config"


def _get_search_config(app: sphinx.application.Sphinx):
    search_config = getattr(app, _SEARCH_CONFIG, None)
    if search_config is not None:
        return search_config
    theme_options = app.config["html_theme_options"]
    search_config = search_plugin.SearchConfig.model_validate(
        theme_options.get("plugins", {}).get("material/search", {})
    )
    plugin = search_plugin.SearchPlugin()
    plugin.config = search_config
    plugin.on_config(_ThemeConfig(app))
    setattr(app, _SEARCH_CONFIG, search_config)
    return search_config


class _ThemeConfig:
    def __init__(self, app):
        self.theme = _Theme(app)


class _Page:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class _Theme:
    def __init__(self, app: sphinx.application.Sphinx):
        self._app = app
        builder = self._app.builder
        self._jinja2_env: Optional[jinja2.sandbox.SandboxedEnvironment]
        if isinstance(builder, sphinx.builders.html.StandaloneHTMLBuilder):
            # only useful if using HTML output
            self._jinja2_env = jinja2.sandbox.SandboxedEnvironment(loader=builder.templates)
            self._jinja2_env.globals.update(builder.globalcontext)
        else:
            self._jinja2_env = None

    def get_env(self):
        return self._jinja2_env


def _make_indexer(app: sphinx.application.Sphinx):
    return search_plugin.SearchIndex(**dict(_get_search_config(app)))


def _html_page_context(
    app: sphinx.application.Sphinx,
    pagename: str,
    templatename: str,
    context: dict,
    doctree: docutils.nodes.Node,
):
    content = context.get("body")
    if content is None:
        # Special page like `genindex`, exclude from search index.
        return
    indexer = _make_indexer(app)
    url = app.builder.get_target_uri(pagename)
    indexer.add_entry_from_context(
        _Page(
            content=content,
            title=context["page"]["title"],
            meta={},
            url=url,
            toc=context["page"]["toc"],
        )
    )
    queue = getattr(app, _SEARCH_QUEUE_KEY)
    queue.append(indexer.entries)


def _build_finished(app: sphinx.application.Sphinx, exception) -> None:
    queue = getattr(app, _SEARCH_QUEUE_KEY)
    indexer = _make_indexer(app)
    for entries in queue[:]:
        indexer.entries.extend(entries)
    output_path = pathlib.Path(app.outdir) / "search" / "search_index.json"
    # try:
    #     existing_data = output_path.read_text(encoding='utf-8')

    # except FileNotFoundError:
    #     pass
    json_data = indexer.generate_search_index(prev=None)

    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(json_data, encoding="utf-8")
    logger.info("Wrote search index: %s", output_path)


def setup(app: sphinx.application.Sphinx):
    app.connect("html-page-context", _html_page_context)
    app.connect("build-finished", _build_finished)
    manager = multiprocessing.Manager()
    setattr(app, "_sphinx_immaterial_search_multiprocessing_manager", manager)
    setattr(app, _SEARCH_QUEUE_KEY, manager.list())
    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
