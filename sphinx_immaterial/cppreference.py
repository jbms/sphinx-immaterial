"""Support for cross-referencing C and C++ symbols to cppreference.com."""

import importlib.resources
import os
import pathlib
import re
import typing
import urllib.parse

import xml.etree.ElementTree as ET
import sphinx.application

from . import external_cpp_references


def _join_links(a: str, b: typing.Optional[str]):
    if b is None or b == ".":
        return a
    return os.path.join(a, b)


def _join_names(a: str, b: str):
    if not a:
        return b
    return f"{a}::{b}"


def _get_last_name(s: str) -> str:
    return re.sub(".*::", "", s)


class CppReferenceXmlParser:
    def __init__(
        self,
        cpp_objects: typing.Dict[str, external_cpp_references.ObjectInfo],
        base_url: str,
    ):
        self.cpp_objects = cpp_objects
        self.base_url = base_url
        self.name_prefix = ""
        self.link_prefix = ""
        self.since = ""

    def add_file(self, content: bytes, since: str):
        content = content.replace(b"<>", b"&lt;&gt;")
        root = ET.fromstring(content)
        self.since = since
        for child in root:
            self.add_element(child)

    def add_url(self, name: str, typ: str, url: str, since: str):
        self.cpp_objects[name] = external_cpp_references.ObjectInfo(
            url=url,
            desc=f"{name} ({since.upper()} standard {typ})",
            object_type=typ,
        )

    def add(self, name: str, typ: str, link: str, since: str):
        self.add_url(
            name=name,
            typ=typ,
            url=urllib.parse.urljoin(self.base_url, link),
            since=since,
        )

    def add_simple(self, element: ET.Element, typ: str):
        name = element.get("name")
        since = element.get("since", self.since)
        self.add(
            name=_join_names(self.name_prefix, name),
            typ=typ,
            link=_join_links(self.link_prefix, element.get("link", name)),
            since=since,
        )

    def add_element(self, element: ET.Element):
        add_function = getattr(self, f"_add_from_{element.tag}", None)
        if not add_function:
            return
        add_function(element)

    def _add_from_typedef(self, element: ET.Element):
        alias = element.get("alias")
        name = element.get("name")
        if alias is not None:
            existing_obj = self.cpp_objects[alias]
            full_name = _join_names(self.name_prefix, name)
            self.add_url(
                name=full_name,
                url=existing_obj.url,
                since=element.get("since", self.since),
                typ="type alias",
            )
            return
        self.add_simple(element, "type alias")

    def _add_from_class(self, element: ET.Element):
        name = element.get("name")
        prev_name_prefix = self.name_prefix
        prev_link_prefix = self.link_prefix
        prev_since = self.since

        self.name_prefix = _join_names(self.name_prefix, name)
        self.link_prefix = _join_links(self.link_prefix, element.get("link", name))
        self.since = element.get("since", self.since)
        self.add(
            name=self.name_prefix, typ="class", link=self.link_prefix, since=self.since
        )
        for child in element:
            self.add_element(child)
        self.name_prefix = prev_name_prefix
        self.link_prefix = prev_link_prefix
        self.since = prev_since

    def _add_from_const(self, element: ET.Element):
        self.add_simple(element, "var")

    def _add_from_enum(self, element: ET.Element):
        self.add_simple(element, "enum")

    def _add_from_function(self, element: ET.Element):
        self.add_simple(element, "function")

    def _add_from_overload(self, element: ET.Element):
        # Skip hidden friends for now
        pass

    def _add_from_variable(self, element: ET.Element):
        self.add_simple(element, "var")

    def _add_from_constructor(self, element: ET.Element):
        name = _get_last_name(self.name_prefix)
        self.add(
            name=_join_names(self.name_prefix, name),
            typ="function",
            link=_join_links(self.link_prefix, element.get("link")),
            since=element.get("since", self.since),
        )

    def _add_from_destructor(self, element: ET.Element):
        name = _get_last_name(self.name_prefix)
        self.add(
            name=_join_names(self.name_prefix, "~" + name),
            typ="function",
            link=_join_links(self.link_prefix, element.get("link")),
            since=element.get("since", self.since),
        )


def load_mappings(app: sphinx.application.Sphinx):
    parser = CppReferenceXmlParser(
        external_cpp_references.get_mappings(app),
        base_url="https://en.cppreference.com/w/",
    )
    xml_files = app.config.cppreference_xml_files
    if xml_files is not None:
        # Use user-specified XML files.
        xml_content = [
            (standard, pathlib.Path(os.path.join(app.srcdir, filename)).read_bytes())
            for standard, filename in app.config.cppreference_xml_files
        ]
    else:
        # Use default XML files included with extension.
        xml_content = [
            (
                "C",
                importlib.resources.read_binary(
                    "sphinx_immaterial.cppreference_data", "index-functions-c.xml"
                ),
            ),
            (
                "C++",
                importlib.resources.read_binary(
                    "sphinx_immaterial.cppreference_data", "index-functions-cpp.xml"
                ),
            ),
        ]
    for standard, content in xml_content:
        parser.add_file(content, since=standard)


def setup(app: sphinx.application.Sphinx):
    app.setup_extension("sphinx_immaterial.external_cpp_references")
    app.connect("builder-inited", load_mappings)
    app.add_config_value(
        name="cppreference_xml_files",
        default=None,
        types=(typing.Optional[typing.List[typing.Tuple[str, str]]],),
        rebuild="env",
    )
    return {"parallel_read_safe": True, "parallel_write_safe": True}
