"""Injects mkdocs-style `nav` and `page` objects into the HTML jinja2 context.

This generates global and local tables-of-contents (TOCs) usable by (a modified
version of) the mkdocs-material HTML templates.

In particular, for each document, this module generates three separate TOCs:

`global_toc`:
    The `global_toc` is the global table of contents.  If the
    `globaltoc_collapse` theme option is `False`, it contains all documents
    reachable from the root document, as well as any sections of non-root
    documents that contain non-empty TOCs.  If the `globaltoc_collapse` theme
    option is `True`, then the global TOC is restricted to children of:

    - the root,
    - the current document,
    - ancestors of the current document.

`local_toc`:
    The `local_toc` is the local table of contents for the specified document.
    It contains all sections of the current document, but does not contain any
    entries that link outside the current document.

`integrated_local_toc`:
    The `integrated_local_toc` contains all sections of the current document, as
    well as any child documents referenced by a TOC contained in the current
    document.  Whether children of the child docuemnts are included depends on
    the `globaltoc_collapse` theme option.

Background
----------

The Sphinx document model differs from the mkdocs document model in that
documents can be organized as children of other documents and sections within
those documents.

Similar functionality is optionally available in mkdocs-material, through the
`navigation.indexes` feature, which effectively allows documents to be children
of other documents (but not sections within those documents).

However, mkdocs-material specifically documents that `navigation.indexes` is
incompatible with the `toc.integrate` feature.  Furthermore, as noted in
https://github.com/squidfunk/mkdocs-material/issues/3819, the local TOC is
inaccessible in the layered navigation menu used with narrow viewports.  This is
because under the mkdocs-material document model (with `navigation.indexes`
feature enabled), there is no natural way to combine both the local TOC for a
page and the nested list of child documents into a single TOC.

With Sphinx, non-leaf documents are the common case, not a special added
feature, and it is not very reasonable for the TOC to not behave correctly on
such documents.  Furthermore, under the Sphinx document model, child documents
are already organized within the sections of their parent document.  Therefore,
there *is* a natural way to display the local TOC and the nested child documents
as a single TOC --- this combined toc is the `integrated_local_toc`.

The mkdocs-material package uses the global and local TOCs as follows:

Left sidebar:
- Doc 1 (from global_toc)
- Group (from global_toc)
  - Doc 2 (from global_toc)
  - Current page (from global_toc)
    - Section 1 (from local_toc)
    - Section 2 (from local_toc)

Right side bar:
- Section 1 (from local_toc)
- Section 2 (from local_toc)

Note that the local TOC is duplicated into the left sidebar as well, but is
hidden in the normal non-mobile layout, unless the `toc.integrate` feature is
enabled (in that case the right side bar is always hidden).  With a sufficiently
narrow layout, the right side bar is hidden and the duplicate copy of the local
toc in the left sidebar is shown in the layered "hamburger" navigation menu.

The above example is for the case where the current page is a leaf page.  If the
`navigation.indexes` feature is in use and the current page is a non-leaf page,
the sidebars are instead generated as follows:

Left sidebar:
- Doc 1 (from global_toc)
- Group (from global_toc)
  - Doc 2 (from global_toc)
  - Current page (from global_toc)
    - Doc 3 (from global_toc)
    - Doc 4 (from global_toc)

Right side bar:
- Section 1 (from local_toc)
- Section 2 (from local_toc)

In order to support a separate `integrated_local_toc`, this theme modifies the
mkdocs-material templates to generate the sidebars as follows:

Left sidebar:
- Doc 1 (from global_toc)
- Group (from global_toc)
  - Doc 2 (from global_toc)
  - Current page (from global_toc) [class=md-nav__current-nested]
    - Doc 3 (from global_toc)
    - Doc 4 (from global_toc)
  - Current page (from global_toc) [class=md-nav__current-toc]
    - Section 1 (from local_toc_integrated)
    - Section 2 (from local_toc_integrated)

Right side bar:
- Section 1 (from local_toc)
- Section 2 (from local_toc)

The left sidebar contains two copies of the local toc, one generated from
`global_toc` and the other from `local_toc_integrated`, but CSS rules based on
the added `md-nav__current-nested` and `md-nav__current-toc` ensure that at most
one copy is shown at a time.

The root document is an exception: in Sphinx the global document structure is
defined by adding `toctree` nodes to the root document.  Technically those
`toctree` nodes are still contained within the usual section structure of the
root document, but the built-in TOC functionality in Sphinx treats the root
document specially, and extacts any `toctree` nodes into a separate global TOC
hierarchy, independent of the section structure of the root document.  In
practice, users often place the `toctree` nodes at the end of the root document,
effectively making them children of the last section, but it is not intended
that they are actually a part of any section.  Therefore, for the root document
there is no natural way to integrate the local and global TOCs, and consequently
the local TOC is simply unavailable when the `toc.integrate` feature is enabled
or when using the "layered" navigation menu.

"""

import collections
import copy
import os
import re
from typing import (
    cast,
    List,
    Union,
    NamedTuple,
    Optional,
    Tuple,
    Iterator,
    Dict,
    Iterable,
    Set,
    Type,
)
import urllib.parse
import docutils.nodes
import markupsafe
import sphinx
import sphinx.builders
import sphinx.builders.html
import sphinx.application
import sphinx.environment.adapters.toctree
import sphinx.util.docutils
import sphinx.util.osutil

from .apidoc import object_description_options

meta_node_types: Tuple[Type[docutils.nodes.Element], ...]

if sphinx.version_info >= (6,):
    meta_node_types = (docutils.nodes.meta,)  # type: ignore[attr-defined]
else:
    from sphinx.addnodes import (  # type: ignore[attr-defined]
        docutils_meta,
        meta as sphinx_meta,
    )

    meta_node_types = (docutils_meta, sphinx_meta)

StandaloneHTMLBuilder = sphinx.builders.html.StandaloneHTMLBuilder


# env var is only defined in RTD hosted builds
READTHEDOCS = os.getenv("READTHEDOCS")


def _strip_fragment(url: str) -> str:
    """Returns the url with any fragment identifier removed."""
    return re.sub("#.*", "", url)


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
    aria_label: Optional[str] = None

    # URL of this page, or the first descendent if `caption_only` is `True`.
    url: Optional[str]
    # List of children
    children: List["MkdocsNavEntry"]
    # Set to `True` if this page, or a descendent, is the current page.
    # Excludes links to sections within in an active page.
    active: bool
    # Set to `True` if this page is the current page.  Excludes links to
    # sections within an active page.
    current: bool

    # Set to `True` if `active`, or if this is a link to a section within an `active` page.
    active_or_section_within_active: bool = False

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

    # `only` directives can result in `comment` nodes.
    def visit_comment(self, node: docutils.nodes.comment):
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
                    active=False,
                    current=False,
                    caption_only=True,
                )
            )
            raise docutils.nodes.SkipChildren
        # Otherwise, just process each list_item as direct children.

    def get_result(self) -> MkdocsNavEntry:
        return MkdocsNavEntry(
            title_text=cast(str, self._rendered_title_text),
            url=self._url,
            children=self._children,
            active=False,
            current=False,
            caption_only=False,
        )

    def visit_list_item(self, node: docutils.nodes.list_item):
        # Child node.  Collect its url, title, and any children using a separate
        # `_TocVisitor`.
        child_visitor = _TocVisitor(self.document, self._builder)
        for child in node.children:
            child.walk(child_visitor)
        child_result = child_visitor.get_result()
        self._children.append(child_result)
        raise docutils.nodes.SkipChildren


def _get_mkdocs_toc(
    toc_node: Optional[docutils.nodes.Node],
    builder: sphinx.builders.html.StandaloneHTMLBuilder,
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
    builder = cast(sphinx.builders.Builder, env.app.builder)
    docname_to_url = {
        docname: builder.get_target_uri(docname) for docname in env.found_docs
    }
    m: Dict[Tuple[str, str], DomainAnchorEntry] = {}
    for domain_name, domain in env.domains.items():
        synopses: Dict[Tuple[str, str], str] = {}
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
            if domain_name == "std" and objtype == "doc":
                # Don't add an extra tooltip for plain documents.
                continue
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
    env = app.env
    assert env is not None
    m = getattr(env, key, None)
    if m is None:
        m = _make_domain_anchor_map(env)
        setattr(env, key, m)
    return m


def _add_domain_info_to_toc(
    app: sphinx.application.Sphinx, toc: List[MkdocsNavEntry], pagename: str
) -> None:
    m = _get_domain_anchor_map(app)
    assert isinstance(app.builder, StandaloneHTMLBuilder)
    env = app.env
    assert env is not None
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
        domain = env.domains[objinfo.domain_name]
        label = domain.get_type_name(domain.object_types[objinfo.objtype])
        options = object_description_options.get_object_description_options(
            env, objinfo.domain_name, objinfo.objtype
        )
        tooltip = object_description_options.format_object_description_tooltip(
            env, options, objinfo.name, objinfo.synopsis
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


def _prune_toc_by_active(
    entry: MkdocsNavEntry, active: bool
) -> Optional[MkdocsNavEntry]:
    """Prunes entries from the TOC tree according to whether they are active.

    Any TOC entries with a target on the current page (i.e. a section within the
    current page) are marked active, while entries with a target on a different
    page are not marked active.

    :param entry: TOC root to recursively prune.
    :param active: If `True`, prune targets not on the current page.  If
      `False`, prune targets on the current page, except if they transitively
      contain children not in the current page.
    :returns: Pruned copy of `entry`.
    """
    if active and not entry.active_or_section_within_active:
        return None

    entry = copy.copy(entry)

    new_children = []
    for child in entry.children:
        new_child = _prune_toc_by_active(child, active)
        if new_child is not None:
            new_children.append(new_child)
    entry.children = new_children

    if entry.active_or_section_within_active and not active and not entry.children:
        return None

    return entry


TocEntryKey = Tuple[int, ...]


def _build_toc_index(
    toc: List[MkdocsNavEntry],
) -> Tuple[Dict[str, List[TocEntryKey]], Set[TocEntryKey]]:
    """Builds a map from URL to list of toc entries.

    This is used by `_get_global_toc` to efficiently prune the cached TOC for a
    given page.
    """
    url_map: Dict[str, List[TocEntryKey]] = collections.defaultdict(list)

    global_toc_keys: Set[TocEntryKey] = set()

    def _traverse(
        entries: List[MkdocsNavEntry],
        parent_key: TocEntryKey,
        parent_url: Optional[str],
    ):
        for i, entry in enumerate(entries):
            child_key = parent_key + (i,)
            url: Optional[str] = None
            if not entry.caption_only:
                url = entry.url
                if url is not None:
                    url = _strip_fragment(url)
                    url_map[url].append(child_key)
            _traverse(entry.children, child_key, url)
            if url != parent_url or child_key in global_toc_keys:
                global_toc_keys.add(child_key)
                global_toc_keys.add(parent_key)

    _traverse(toc, (), None)
    return url_map, global_toc_keys


_FAKE_DOCNAME = "fakedoc"


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
        env = app.env
        assert env is not None
        builder = app.builder
        assert isinstance(builder, StandaloneHTMLBuilder)
        global_toc_node = sphinx.environment.adapters.toctree.TocTree(
            env
        ).get_toctree_for(
            _FAKE_DOCNAME,
            builder,
            collapse=False,
            maxdepth=-1,
            titles_only=False,
        )
        global_toc = _get_mkdocs_toc(global_toc_node, builder)
        _add_domain_info_to_toc(app, global_toc, _FAKE_DOCNAME)
        self.entries = global_toc
        self.url_map, self.global_toc_keys = _build_toc_index(global_toc)


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
    builder = app.builder
    assert isinstance(builder, StandaloneHTMLBuilder)
    fake_page_url = builder.get_target_uri(_FAKE_DOCNAME)
    fake_relative_url = sphinx.util.osutil.relative_uri(
        fake_page_url, builder.get_target_uri(pagename)
    )
    keys = set(cached_data.url_map[fake_relative_url])
    global_toc_keys = cached_data.global_toc_keys
    ancestors = _get_ancestor_keys(keys)
    real_page_url = builder.get_target_uri(pagename)

    def _make_toc_for_page(key: TocEntryKey, children: List[MkdocsNavEntry]):
        page_is_current = key in keys
        new_children: List[MkdocsNavEntry] = []
        for i, child in enumerate(children):
            child_key = key + (i,)
            in_ancestors = child_key in ancestors
            child_active = in_ancestors
            child_current = in_ancestors and child_key in keys
            if (
                not child_active
                and not page_is_current
                and child_key not in global_toc_keys
            ):
                continue
            child = copy.copy(child)
            new_children.append(child)
            if child.url is not None:
                root_relative_url = urllib.parse.urljoin(fake_page_url, child.url)
                uri = urllib.parse.urlparse(root_relative_url)
                if not uri.netloc:
                    child.url = sphinx.util.osutil.relative_uri(
                        real_page_url, root_relative_url
                    )
                    if uri.fragment or child.url == "":
                        child.url += f"#{uri.fragment}"
            child.active = child_active and not page_is_current
            child.current = child_current and not page_is_current
            child.active_or_section_within_active = child_active
            if in_ancestors or child.caption_only or not collapse:
                child.children = _make_toc_for_page(child_key, child.children)
            else:
                child.children = []
        return new_children

    return _make_toc_for_page((), cached_data.entries)


def _get_mkdocs_tocs(
    app: sphinx.application.Sphinx,
    pagename: str,
    duplicate_local_toc: bool,
    toc_integrate: bool,
) -> Tuple[List[MkdocsNavEntry], List[MkdocsNavEntry], List[MkdocsNavEntry]]:
    """Generates the global and local TOCs for a document.

    :param app: The sphinx application object.
    :param pagename: The name of the document for which to generate the tocs.
    :param duplicate_local_toc: Duplicate the local toc in the global toc.
    :param toc_integrate: Indicates if the `toc.integrate` feature is enabled.
    :returns: A tuple `(global_toc, local_toc, integrated_local_toc)`.
    """
    theme_options = app.config["html_theme_options"]
    global_toc = _get_global_toc(
        app=app,
        pagename=pagename,
        collapse=theme_options.get("globaltoc_collapse", False),
    )
    local_toc: List[MkdocsNavEntry] = []
    integrated_local_toc: List[MkdocsNavEntry] = []
    env = app.env
    assert env is not None
    builder = app.builder
    assert isinstance(builder, StandaloneHTMLBuilder)
    if pagename != env.config.master_doc:
        # Extract entry from `global_toc` corresponding to the current page.
        current_page_toc_entry = _get_current_page_in_toc(global_toc)
        if current_page_toc_entry is not None:
            integrated_local_toc = [copy.copy(current_page_toc_entry)]
            integrated_local_toc[0].children = list(integrated_local_toc[0].children)
            if not toc_integrate:
                local_toc = cast(
                    List[MkdocsNavEntry],
                    [_prune_toc_by_active(current_page_toc_entry, active=True)],
                )
            if toc_integrate:
                current_page_toc_entry.children = []
            elif not duplicate_local_toc:
                current_page_toc_entry.children = [
                    child
                    for child in [
                        _prune_toc_by_active(child, active=False)
                        for child in current_page_toc_entry.children
                    ]
                    if child is not None
                ]
    else:
        # Every page is a child of the root page.  We still want a full TOC
        # tree, though.
        local_toc_node = sphinx.environment.adapters.toctree.TocTree(env).get_toc_for(
            pagename,
            builder,
        )
        local_toc = _get_mkdocs_toc(local_toc_node, builder)
        _add_domain_info_to_toc(app, local_toc, pagename)

    if len(local_toc) == 1 and len(local_toc[0].children) == 0:
        local_toc = []

    if len(integrated_local_toc) == 1 and len(integrated_local_toc[0].children) == 0:
        integrated_local_toc = []

    return global_toc, local_toc, integrated_local_toc


def _html_page_context(
    app: sphinx.application.Sphinx,
    pagename: str,
    templatename: str,
    context: dict,
    doctree: docutils.nodes.Node,
) -> None:
    env = app.env
    assert env is not None

    theme_options: dict = app.config["html_theme_options"]
    features = theme_options.get("features", ())
    assert isinstance(features, collections.abc.Sequence)
    page_title = markupsafe.Markup.escape(
        markupsafe.Markup(context.get("title")).striptags()
    )
    meta = context.get("meta")
    if meta is None:
        meta = {}
    global_toc, local_toc, integrated_local_toc = _get_mkdocs_tocs(
        app,
        pagename,
        duplicate_local_toc=isinstance(meta.get("duplicate-local-toc"), str),
        toc_integrate="toc.integrate" in features,
    )
    context.update(nav=_NavContextObject(global_toc))
    context["nav"].homepage = {
        "url": context["pathto"](context["master_doc"]),
    }

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
            "extra": {"consent": theme_options.get("consent")},
        }
    )

    if len(local_toc) == 1:
        # If there is a single top-level heading, it is treated as the page
        # heading, and it would be redundant to also include it as an entry in
        # the local toc.
        local_toc = local_toc[0].children

    if len(integrated_local_toc) == 1:
        # If there is a single top-level heading, it is treated as the page
        # heading, and it would be redundant to also include it as an entry in
        # the local toc.
        integrated_local_toc = integrated_local_toc[0].children

    # Add other context values in mkdocs/mkdocs-material format.
    page = {
        "title": page_title,
        "is_homepage": (pagename == context["master_doc"]),
        "toc": local_toc,
        "integrated_local_toc": integrated_local_toc,
        "meta": {"hide": [], "revision_date": context.get("last_updated"), "meta": []},
        "content": context.get("body"),
    }
    if doctree is not None:
        # extract meta nodes from document node only (not descendants)
        meta_tags = [
            doc_node
            for doc_node in doctree.document.children
            if isinstance(doc_node, meta_node_types)
        ]
        for tag in meta_tags:
            assert isinstance(tag, docutils.nodes.Element)
            # feed them into the mkdocs template context
            attrs = {key: value for key, value in tag.attributes.items() if value}
            page["meta"]["meta"].append(attrs)
    if meta.get("tocdepth") == 0 or "hide-toc" in meta:
        page["meta"]["hide"].append("toc")
    if "hide-navigation" in meta:
        page["meta"]["hide"].append("navigation")
    if "hide-footer" in meta:
        page["meta"]["hide"].append("footer")
    if "hide-feedback" in meta:
        page["meta"]["hide"].append("feedback")
    if "show-comments" in meta:
        page["meta"]["comments"] = True
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
    if repo_url and edit_uri and "hide-edit-link" not in meta:
        page["edit_url"] = "/".join(
            [
                repo_url.rstrip("/"),
                edit_uri.strip("/"),
                str(env.doc2path(pagename, False)),
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
