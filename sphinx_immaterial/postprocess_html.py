import multiprocessing
from typing import cast, Any

from xml.etree import ElementTree

import docutils.nodes
import sphinx.application
import sphinx.util.console


def add_html_link(
    app: sphinx.application.Sphinx,
    pagename: str,
    templatename: str,
    context: dict,
    doctree: docutils.nodes.Node,
):
    """As each page is built, collect page names for the sitemap"""
    base_url = app.config["html_theme_options"].get("site_url", "")
    if base_url:
        if not base_url.endswith("/"):
            base_url += "/"
        full_url = base_url + app.builder.get_target_uri(pagename)
        cast(Any, app).sitemap_links.append(full_url)


def create_sitemap(app: sphinx.application.Sphinx, exception):
    """Generates the sitemap.xml from the collected HTML page links"""
    sitemap_links = cast(Any, app).sitemap_links

    if (
        not app.config["html_theme_options"].get("site_url", "")
        or exception is not None
        or not sitemap_links
    ):
        return

    filename = app.outdir + "/sitemap.xml"
    print(
        "Generating sitemap for {0} pages in "
        "{1}".format(len(sitemap_links), sphinx.util.console.colorize("blue", filename))
    )

    root = ElementTree.Element("urlset")
    root.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")

    for link in sitemap_links:
        url = ElementTree.SubElement(root, "url")
        ElementTree.SubElement(url, "loc").text = link
    sitemap_links[:] = []

    ElementTree.ElementTree(root).write(filename)


def setup(app: sphinx.application.Sphinx):
    app.connect("html-page-context", add_html_link)
    app.connect("build-finished", create_sitemap)
    manager = multiprocessing.Manager()
    cast(Any, app).sitemap_links = manager.list()
    app.multiprocess_manager = manager
    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
