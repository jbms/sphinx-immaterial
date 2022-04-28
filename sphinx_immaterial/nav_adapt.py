"""Injects mkdocs-style `nav` and `page` objects into the HTML jinja2 context."""

import collections
import copy
import os
import re
from typing import (
    List,
    Union,
    NamedTuple,
    Optional,
    Tuple,
    Iterator,
    Dict,
    Iterable,
    Set,
)
import urllib.parse
import docutils.nodes
import markupsafe
import sphinx.builders
import sphinx.application
import sphinx.environment.adapters.toctree
import sphinx.util.osutil

from . import apidoc_formatting


# env var is only defined in RTD hosted builds
READTHEDOCS = os.getenv("READTHEDOCS")


def _strip_fragment(url: str) -> str:
    """Returns the url with any fragment identifier removed."""
    fragment_start = url.find("#")
    if fragment_start == -1:
        return url
    return url[:fragment_start]


def _insert_wbr(text: str) -> str:
    """Inserts <wbr> tags after likely split points for API symbols."""
    # Split after punctuation
    text = re.sub("([.:_-]+)", r"\1<wbr>", text)
    # Split before brackets
    text = re.sub(r"([(\[{])", r"<wbr>\1", text)
    # Split between camel-case words
    text = re.sub(r"([a-z])([A-Z])", r"\1<wbr>\2", text)
    return text


class MkdocsNavEntry:
    # Title to display, as HTML.
    title: str

    # Aria label text, plain text.
    aria_label: str = None

    # URL of this page, or the first descendent if `caption_only` is `True`.
    url: Optional[str]
    # List of children
    children: List["MkdocsNavEntry"]
    # Set to `True` if this page, or a descendent, is the current page.
    active: bool
    # Set to `True` if this page is the current page.
    current: bool
    # Set to `True` if this entry does not refer to a unique page but is merely
    # a TOC caption.
    caption_only: bool

    def __init__(self, title_text: str, **kwargs):
        self.__dict__.update(kwargs)
        self.title = f'<span class="md-ellipsis">{_insert_wbr(title_text)}</span>'
        if not self.aria_label:
            self.aria_label = title_text

    def __repr__(self):
        return repr(self.__dict__)


class _TocVisitor(docutils.nodes.NodeVisitor):
    """NodeVisitor used by `_get_mkdocs_toc`."""

    def __init__(
        self,
        document: docutils.nodes.document,
        builder: sphinx.builders.html.StandaloneHTMLBuilder,
    ):
        super().__init__(document)
        self._prev_caption: Optional[docutils.nodes.Element] = None
        self._rendered_title_text: Optional[str] = None
        self._url: Optional[str] = None
        self._builder = builder
        # Indicates if this node or one of its descendents is the current page.
        self._active = False
        # List of direct children.
        self._children: List[MkdocsNavEntry] = []

    def _render(self, node: Union[docutils.nodes.Node, List[docutils.nodes.Node]]):
        """Returns the HTML representation of `node`."""
        if not isinstance(node, list):
            node = [node]
        return "".join(self._builder.render_partial(x)["fragment"] for x in node)

    def _render_title(
        self, node: Union[docutils.nodes.Node, List[docutils.nodes.Node]]
    ):
        """Returns the text representation of `node`."""
        if not isinstance(node, list):
            node = [node]
        return str(markupsafe.Markup.escape("".join(x.astext() for x in node)))

    def visit_reference(self, node: docutils.nodes.reference):
        self._rendered_title_text = self._render_title(node.children)
        self._url = node.get("refuri")
        raise docutils.nodes.SkipChildren

    def visit_compact_paragraph(self, node: docutils.nodes.Element):
        pass

    def visit_toctree(self, node: docutils.nodes.Node):
        raise docutils.nodes.SkipChildren

    def visit_paragraph(self, node: docutils.nodes.Node):
        pass

    # In sphinx < 3.5.4, TOC captions are represented using a caption node.
    def visit_caption(self, node: docutils.nodes.caption):
        self._prev_caption = node
        raise docutils.nodes.SkipChildren

    # In sphinx >= 3.5.4, TOC captions are represented using a title node.
    def visit_title(self, node: docutils.nodes.title):
        self._prev_caption = node
        raise docutils.nodes.SkipChildren

    def visit_bullet_list(self, node: docutils.nodes.bullet_list):
        if self._prev_caption is not None and self._prev_caption.parent is node.parent:
            # Insert as sub-entry of the previous caption.
            title_text = self._render_title(self._prev_caption.children)
            self._prev_caption = None
            child_visitor = _TocVisitor(self.document, self._builder)
            if node.get("iscurrent", False):
                child_visitor._active = True
            node.walk(child_visitor)
            url = None
            children = child_visitor._children
            if children:
                url = children[0].url
            self._children.append(
                MkdocsNavEntry(
                    title_text=title_text,
                    url=url,
                    children=children,
                    active=child_visitor._active,
                    current=False,
                    caption_only=True,
                )
            )
            raise docutils.nodes.SkipChildren
        # Otherwise, just process each list_item as direct children.

    def get_result(self) -> MkdocsNavEntry:
        return MkdocsNavEntry(
            title_text=self._rendered_title_text,
            url=self._url,
            children=self._children,
            active=self._active,
            current=self._active and self._url == "",
            caption_only=False,
        )

    def visit_list_item(self, node: docutils.nodes.list_item):
        # Child node.  Collect its url, title, and any children using a separate
        # `_TocVisitor`.
        child_visitor = _TocVisitor(self.document, self._builder)
        if node.get("iscurrent", False):
            child_visitor._active = True
        for child in node.children:
            child.walk(child_visitor)
        child_result = child_visitor.get_result()
        self._children.append(child_result)
        raise docutils.nodes.SkipChildren


def _get_mkdocs_toc(
    toc_node: docutils.nodes.Node, builder: sphinx.builders.html.StandaloneHTMLBuilder
) -> List[MkdocsNavEntry]:
    """Converts a docutils toc node into a mkdocs-format JSON toc."""
    visitor = _TocVisitor(sphinx.util.docutils.new_document(""), builder)

    # toc_node can be None for projects with no toctree or 1 rst-file only.
    if toc_node is not None:
        toc_node.walk(visitor)
    return visitor._children


class _NavContextObject(list):
    homepage: dict


def _traverse_mkdocs_toc(toc: List[MkdocsNavEntry]) -> Iterator[MkdocsNavEntry]:
    for entry in toc:
        yield entry
        yield from _traverse_mkdocs_toc(entry.children)


def _relative_uri_to_root_relative_and_anchor(
    builder: sphinx.builders.html.StandaloneHTMLBuilder,
    base_pagename: str,
    relative_uri: str,
) -> Optional[Tuple[str, str]]:
    """Converts a relative URI to a root-relative uri and anchor."""
    uri = urllib.parse.urlparse(
        urllib.parse.urljoin(builder.get_target_uri(base_pagename), relative_uri)
    )
    if uri.netloc:
        return None
    return (uri.path, uri.fragment)


class DomainAnchorEntry(NamedTuple):
    domain_name: str
    name: str
    display_name: str
    objtype: str
    priority: int
    synopsis: Optional[str]


def _make_domain_anchor_map(
    env: sphinx.environment.BuildEnvironment,
) -> Dict[Tuple[str, str], DomainAnchorEntry]:
    builder = env.app.builder
    docname_to_url = {
        docname: builder.get_target_uri(docname) for docname in env.found_docs
    }
    m: Dict[Tuple[str, str], DomainAnchorEntry] = {}
    for domain_name, domain in env.domains.items():
        synopses = {}
        get_object_synopses = getattr(domain, "get_object_synopses", None)
        if get_object_synopses is not None:
            for key, synopsis in get_object_synopses():
                synopses.setdefault(key, synopsis)
        for (
            name,
            dispname,
            objtype,
            docname,
            anchor,
            priority,
        ) in domain.get_objects():
            url = docname_to_url.get(docname)
            if url is None:
                continue
            key = (url, anchor)
            synopsis = synopses.get((docname, anchor))
            m.setdefault(
                key,
                DomainAnchorEntry(
                    domain_name, name, dispname, objtype, priority, synopsis
                ),
            )
    return m


def _get_domain_anchor_map(
    app: sphinx.application.Sphinx,
) -> Dict[Tuple[str, str], DomainAnchorEntry]:
    key = "sphinx_immaterial_domain_anchor_map"
    m = getattr(app.env, key, None)
    if m is None:
        m = _make_domain_anchor_map(app.env)
        setattr(app.env, key, m)
    return m


def _add_domain_info_to_toc(
    app: sphinx.application.Sphinx, toc: List[MkdocsNavEntry], pagename: str
) -> None:
    m = _get_domain_anchor_map(app)
    for entry in _traverse_mkdocs_toc(toc):
        if entry.caption_only or entry.url is None:
            continue
        refinfo = _relative_uri_to_root_relative_and_anchor(
            app.builder, pagename, entry.url
        )
        if refinfo is None:
            continue
        objinfo = m.get(refinfo)
        if objinfo is None:
            continue
        domain = app.env.domains[objinfo.domain_name]
        label = domain.get_type_name(domain.object_types[objinfo.objtype])
        options = apidoc_formatting.get_object_description_options(
            app.env, objinfo.domain_name, objinfo.objtype
        )
        tooltip = apidoc_formatting.format_object_description_tooltip(
            app.env, options, objinfo.name, objinfo.synopsis
        )
        toc_icon_text = options["toc_icon_text"]
        toc_icon_class = options["toc_icon_class"]
        title_prefix = ""
        if toc_icon_text is not None and toc_icon_class is not None:
            title_prefix = (
                f'<span aria-label="{label}" '
                f'class="objinfo-icon objinfo-icon__{toc_icon_class}" '
                f'title="{label}">{toc_icon_text}</span>'
            )
        span_prefix = "<span "
        assert entry.title.startswith(span_prefix)
        entry.title = (
            title_prefix
            + f'<span title="{markupsafe.Markup.escape(tooltip)}" '
            + entry.title[len(span_prefix) :]
        )


def _get_current_page_in_toc(toc: List[MkdocsNavEntry]) -> Optional[MkdocsNavEntry]:
    for entry in toc:
        if not entry.active:
            continue
        if entry.current:
            return entry
        return _get_current_page_in_toc(entry.children)
    return None


def _collapse_children_not_on_same_page(entry: MkdocsNavEntry) -> MkdocsNavEntry:
    entry = copy.copy(entry)
    if not entry.active:
        entry.children = []
    else:
        entry.children = [
            _collapse_children_not_on_same_page(child) for child in entry.children
        ]
    return entry


TocEntryKey = Tuple[int, ...]


def _build_toc_index(toc: List[MkdocsNavEntry]) -> Dict[str, List[TocEntryKey]]:
    """Builds a map from URL to list of toc entries.

    This is used by `_get_global_toc` to efficiently prune the cached TOC for a
    given page.
    """
    url_map: Dict[str, List[TocEntryKey]] = collections.defaultdict(list)

    def _traverse(entries: List[MkdocsNavEntry], parent_key: TocEntryKey):
        for i, entry in enumerate(entries):
            child_key = parent_key + (i,)
            url = entry.url
            if url is not None and not entry.caption_only:
                url = _strip_fragment(url)
                url_map[url].append(child_key)
            _traverse(entry.children, child_key)

    _traverse(toc, ())
    return url_map


class CachedTocInfo:
    """Cached representation of the global TOC.

    This is generated once (per writer process) and re-used for all pages.

    Obtaining the global TOC via `TocTree.get_toctree_for` is expensive because
    we first have to obtain a complete TOC of all pages, and then prune it for
    the current page.  The overall cost to generate the TOCs for all pages
    therefore ends up being quadratic in the number of pages, and in practice as
    the number of pages reaches several hundred, a significant fraction of the
    total documentation generation time is due to the TOC.

    By the caching the TOC and a `url_map` that allows to efficiently prune the
    TOC for a given page, the cost of generating the TOC for each page is much
    lower.
    """

    def __init__(self, app: sphinx.application.Sphinx):
        # Sphinx always generates a TOC relative to a particular page, and
        # converts all page references to relative URLs.  Use an empty string as
        # the page name to ensure the relative URLs that Sphinx generates are
        # relative to the base URL.  When generating the per-page TOCs from this
        # cached data structure the URLs will be converted to be relative to the
        # current page.
        fake_pagename = ""
        global_toc_node = sphinx.environment.adapters.toctree.TocTree(
            app.env
        ).get_toctree_for(
            fake_pagename,
            app.builder,
            collapse=False,
            maxdepth=-1,
            titles_only=False,
        )
        global_toc = _get_mkdocs_toc(global_toc_node, app.builder)
        _add_domain_info_to_toc(app, global_toc, fake_pagename)
        self.entries = global_toc
        self.url_map = _build_toc_index(global_toc)


def _get_cached_globaltoc_info(app: sphinx.application.Sphinx) -> CachedTocInfo:
    """Obtains the cached global TOC, generating it if necessary."""
    key = "sphinx_immaterial_global_toc_cache"
    data = getattr(app.env, key, None)
    if data is not None:
        return data
    data = CachedTocInfo(app)
    setattr(app.env, key, data)
    return data


def _get_ancestor_keys(keys: Iterable[TocEntryKey]) -> Set[TocEntryKey]:
    ancestors = set()
    for key in keys:
        while key not in ancestors:
            ancestors.add(key)
            key = key[:-1]
    return ancestors


def _get_global_toc(app: sphinx.application.Sphinx, pagename: str, collapse: bool):
    """Obtains the global TOC for a given page."""
    cached_data = _get_cached_globaltoc_info(app)
    url = app.builder.get_target_uri(pagename)
    keys = set(cached_data.url_map[url])
    ancestors = _get_ancestor_keys(keys)

    fake_pagename = ""

    fake_page_url = app.builder.get_target_uri(fake_pagename)

    real_page_url = app.builder.get_target_uri(pagename)

    def _make_toc_for_page(key: TocEntryKey, children: List[MkdocsNavEntry]):
        children = list(children)
        for i, child in enumerate(children):
            child_key = key + (i,)
            child = children[i] = copy.copy(child)
            if child.url is not None:
                root_relative_url = urllib.parse.urljoin(fake_page_url, child.url)
                uri = urllib.parse.urlparse(root_relative_url)
                if not uri.netloc:
                    child.url = sphinx.util.osutil.relative_uri(
                        real_page_url, root_relative_url
                    )
                    if uri.fragment:
                        child.url += f"#{uri.fragment}"
            in_ancestors = child_key in ancestors
            if in_ancestors:
                child.active = True
                if child_key in keys:
                    child.current = True
            if in_ancestors or child.caption_only:
                child.children = _make_toc_for_page(child_key, child.children)
            else:
                child.children = []
        return children

    return _make_toc_for_page((), cached_data.entries)


def _get_mkdocs_tocs(
    app: sphinx.application.Sphinx, pagename: str, duplicate_local_toc: bool
) -> Tuple[List[MkdocsNavEntry], List[MkdocsNavEntry]]:
    theme_options = app.config["html_theme_options"]
    global_toc = _get_global_toc(
        app=app,
        pagename=pagename,
        collapse=theme_options.get("globaltoc_collapse", False),
    )
    local_toc = []
    if pagename != app.env.config.master_doc:
        # Extract entry from `global_toc` corresponding to the current page.
        current_page_toc_entry = _get_current_page_in_toc(global_toc)
        if current_page_toc_entry:
            local_toc = [_collapse_children_not_on_same_page(current_page_toc_entry)]
            if not duplicate_local_toc:
                current_page_toc_entry.children = []

    else:
        # Every page is a child of the root page.  We still want a full TOC
        # tree, though.
        local_toc_node = sphinx.environment.adapters.toctree.TocTree(
            app.env
        ).get_toc_for(
            pagename,
            app.builder,
        )
        local_toc = _get_mkdocs_toc(local_toc_node, app.builder)
        _add_domain_info_to_toc(app, local_toc, pagename)

    if len(local_toc) == 1 and len(local_toc[0].children) == 0:
        local_toc = []

    return global_toc, local_toc


def _html_page_context(
    app: sphinx.application.Sphinx,
    pagename: str,
    templatename: str,
    context: dict,
    doctree: docutils.nodes.Node,
) -> None:
    theme_options: dict = app.config["html_theme_options"]
    page_title = markupsafe.Markup.escape(
        markupsafe.Markup(context.get("title")).striptags()
    )
    meta = context.get("meta", {})
    global_toc, local_toc = _get_mkdocs_tocs(
        app,
        pagename,
        duplicate_local_toc=bool(
            meta and isinstance(meta.get("duplicate-local-toc"), str)
        ),
    )
    context.update(nav=_NavContextObject(global_toc))
    context["nav"].homepage = dict(
        url=context["pathto"](context["master_doc"]),
    )

    toc_title = theme_options.get("toc_title")
    if toc_title:
        toc_title = str(markupsafe.Markup.escape(toc_title))
    elif (
        theme_options.get("toc_title_is_page_title")
        and local_toc
        and len(local_toc) == 1
    ):
        # Use single top-level heading as table of contents heading.
        toc_title = local_toc[0].title

    context.update(
        config={
            "mdx_configs": {
                "toc": {"title": toc_title},
            },
        }
    )

    if len(local_toc) == 1:
        # If there is a single top-level heading, it is treated as the page
        # heading, and it would be redundant to also include it as an entry in
        # the local toc.
        local_toc = local_toc[0].children

    # Add other context values in mkdocs/mkdocs-material format.
    page = dict(
        title=page_title,
        is_homepage=(pagename == context["master_doc"]),
        toc=local_toc,
        meta={"hide": [], "revision_date": context.get("last_updated")},
        content=context.get("body"),
    )
    if meta:
        if meta.get("tocdepth") == 0 or "hide-toc" in meta.keys():
            page["meta"]["hide"].append("toc")
        if "hide-navigation" in meta.keys():
            page["meta"]["hide"].append("navigation")
    if context.get("next"):
        page["next_page"] = {
            "title": markupsafe.Markup.escape(
                markupsafe.Markup(context["next"]["title"]).striptags()
            ),
            "url": context["next"]["link"],
        }
    if context.get("prev"):
        page["previous_page"] = {
            "title": markupsafe.Markup.escape(
                markupsafe.Markup(context["prev"]["title"]).striptags()
            ),
            "url": context["prev"]["link"],
        }
    repo_url: Optional[str] = theme_options.get("repo_url")
    edit_uri: Optional[str] = theme_options.get("edit_uri")
    if repo_url and edit_uri and not READTHEDOCS:
        page["edit_url"] = "/".join(
            [
                repo_url.rstrip("/"),
                edit_uri.strip("/"),
                app.builder.env.doc2path(pagename, False),
            ]
        )
    context.update(
        page=page,
    )


def setup(app: sphinx.application.Sphinx):
    app.connect("html-page-context", _html_page_context)
    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
