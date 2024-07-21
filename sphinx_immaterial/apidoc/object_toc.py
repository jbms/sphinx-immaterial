"""Adds all Sphinx "objects" to the table of contents."""

from typing import cast, Optional, Union, Any, List
import docutils.nodes
import sphinx.addnodes
import sphinx.application
import sphinx.directives
from sphinx.environment.collectors.toctree import TocTreeCollector
from sphinx.locale import _

from . import object_description_options
from .. import html_translator_mixin


def _monkey_patch_toc_tree_process_doc():
    """Enables support for also finding Sphinx domain objects."""

    # Apply the monkey patch
    orig_process_doc = TocTreeCollector.process_doc

    def _make_section_from_desc(
        app: sphinx.application.Sphinx,
        source: sphinx.addnodes.desc,
    ) -> Optional[docutils.nodes.section]:
        env = app.env
        assert env is not None
        options = object_description_options.get_object_description_options(
            env, source["domain"], source["objtype"]
        )
        if not options["include_in_toc"]:
            return None

        signature: sphinx.addnodes.desc_signature
        for child in source.children:
            if not isinstance(child, sphinx.addnodes.desc_signature):
                continue
            signature = child
            break
        else:
            # No signature found
            return None
        ids = signature["ids"]
        if not ids:
            # Not indexed.
            return None
        section = docutils.nodes.section()
        section["ids"] = ids

        # Extract title from signature
        title = signature.get("toc_title", None)
        if not title:
            title = ""
            for child in signature.findall():
                if isinstance(
                    child, (sphinx.addnodes.desc_name, sphinx.addnodes.desc_addname)
                ):
                    child = cast(
                        Union[sphinx.addnodes.desc_name, sphinx.addnodes.desc_addname],
                        child,
                    )
                    if "sig-name-nonprimary" in child["classes"]:
                        continue
                    title += child.astext()
        if not title:
            # No name found
            return None
        # Sphinx uses the first child of the section node as the title.
        titlenode = docutils.nodes.comment(title, title)
        section += titlenode
        return section

    def _make_section_from_field(
        source: docutils.nodes.field,
    ) -> Optional[docutils.nodes.section]:
        fieldname = cast(docutils.nodes.field_name, source[0])
        ids = fieldname["ids"]
        if not ids:
            # Not indexed
            return None
        section = docutils.nodes.section()
        section["ids"] = ids
        title = fieldname.astext()
        # Sphinx uses the first child of the section node as the title.
        titlenode = docutils.nodes.comment(title, title)
        section += titlenode
        return section

    def _make_section_from_rubric(
        source: docutils.nodes.rubric,
    ) -> Optional[docutils.nodes.section]:
        rubric = cast(docutils.nodes.rubric, source)
        ids = rubric["ids"]
        if not ids:
            # Not indexed
            return None
        section = docutils.nodes.section()
        section["ids"] = ids
        title = rubric.astext()
        # Sphinx uses the first child of the section node as the title.
        titlenode = docutils.nodes.comment(title, title)
        section += titlenode
        return section

    def _make_section_from_term(
        source: docutils.nodes.term,
    ) -> Optional[docutils.nodes.section]:
        ids = source["ids"]
        if not ids:
            # Not indexed
            return None
        section = docutils.nodes.section()
        section["ids"] = ids
        title = source["toc_title"]
        titlenode = docutils.nodes.comment(title, title)
        section += titlenode
        return section

    def _patched_process_doc(
        self: TocTreeCollector,
        app: sphinx.application.Sphinx,
        doctree: docutils.nodes.document,
    ) -> None:
        new_document = doctree.copy()  # Shallow copy

        def _collect(
            source: docutils.nodes.Node, target: docutils.nodes.Element
        ) -> None:
            if not isinstance(source, docutils.nodes.Element):
                return
            children = iter(source.children)
            new_node: Any
            if isinstance(source, docutils.nodes.section):
                new_node = source.copy()
                # Also copy first child, which sphinx interprets as the title
                new_node += next(children).deepcopy()
                target += new_node
                target = new_node
            elif isinstance(source, sphinx.addnodes.only):
                # Retain "only" nodes since they affect toc generation.
                new_node = source.copy()
                target += new_node
                target = new_node
            elif isinstance(source, sphinx.addnodes.toctree):
                # Deep copy entire toctree
                new_node = source.deepcopy()
                target += new_node
                return
            elif isinstance(source, sphinx.addnodes.desc):
                # Object description.  Try to create synthetic section.
                new_node = _make_section_from_desc(app, source)
                if new_node is not None:
                    target += new_node
                    target = new_node
            elif isinstance(source, docutils.nodes.field):
                # Field.  Try to create synthetic section.
                new_node = _make_section_from_field(source)
                if new_node is not None:
                    target += new_node
                    target = new_node
            elif isinstance(source, docutils.nodes.rubric):
                # Rubric.  Try to create synthetic section.
                new_node = _make_section_from_rubric(source)
                if new_node is not None:
                    target += new_node
                # Rubrics cannot contain sub-sections
                return
            elif isinstance(source, docutils.nodes.term) and source.get("toc_title"):
                # Term with toc title.  Try to create synthetic section.
                new_node = _make_section_from_term(source)
                if new_node is not None:
                    target += new_node
                # Parameters cannot contain sub-sections
                return

            for child in children:
                _collect(child, target)

        _collect(doctree, new_document)
        return orig_process_doc(self, app, new_document)

    TocTreeCollector.process_doc = _patched_process_doc  # type: ignore


_monkey_patch_toc_tree_process_doc()


@html_translator_mixin.override
def depart_field_name(
    self,
    node: docutils.nodes.field_name,
    super_func: html_translator_mixin.BaseVisitCallback[docutils.nodes.field_name],
) -> None:
    super_func(self, node)
    last_part = self.body[-1]
    end_tag_index = last_part.index("</dt>")
    self.body[-1] = last_part[:end_tag_index]
    self.add_permalink_ref(node, _("Permalink to this headline"))
    self.body.append(last_part[end_tag_index:])


def _monkey_patch_object_description_to_include_fields_in_toc():
    orig_run = sphinx.directives.ObjectDescription.run

    def run(self: sphinx.directives.ObjectDescription) -> List[docutils.nodes.Node]:
        nodes = orig_run(self)

        options = object_description_options.get_object_description_options(
            self.env, self.domain, self.objtype
        )
        if not options["include_fields_in_toc"]:
            return nodes

        obj_desc = nodes[-1]
        assert isinstance(obj_desc, sphinx.addnodes.desc)

        obj_id = None
        for sig in obj_desc[:-1]:
            assert isinstance(sig, sphinx.addnodes.desc_signature)
            ids = sig["ids"]
            if ids and ids[0]:
                obj_id = ids[0]
                break

        obj_content = obj_desc[-1]
        assert isinstance(obj_content, sphinx.addnodes.desc_content)
        for child in obj_content:
            if not isinstance(child, docutils.nodes.field_list):
                continue
            for field in child:
                assert isinstance(field, docutils.nodes.field)
                field_name = cast(docutils.nodes.field_name, field[0])
                if field_name["ids"]:
                    continue
                field_id = docutils.nodes.make_id(field_name.astext())
                if obj_id:
                    field_id = f"{obj_id}-{field_id}"
                field_name["ids"].append(field_id)

        return nodes

    sphinx.directives.ObjectDescription.run = run  # type: ignore[assignment]


_monkey_patch_object_description_to_include_fields_in_toc()


@html_translator_mixin.override
def depart_rubric(
    self,
    node: docutils.nodes.rubric,
    super_func: html_translator_mixin.BaseVisitCallback[docutils.nodes.rubric],
) -> None:
    self.add_permalink_ref(node, _("Permalink to this headline"))
    super_func(self, node)


def _monkey_patch_object_description_to_include_rubrics_in_toc():
    orig_run = sphinx.directives.ObjectDescription.run

    def run(self: sphinx.directives.ObjectDescription) -> List[docutils.nodes.Node]:
        nodes = orig_run(self)

        options = object_description_options.get_object_description_options(
            self.env, self.domain, self.objtype
        )
        if not options["include_rubrics_in_toc"]:
            return nodes

        obj_desc = nodes[-1]
        assert isinstance(obj_desc, sphinx.addnodes.desc)
        obj_content = obj_desc[-1]
        assert isinstance(obj_content, sphinx.addnodes.desc_content)
        for child in obj_content:
            if not isinstance(child, docutils.nodes.rubric):
                continue
            rubric = cast(docutils.nodes.rubric, child)
            if rubric["ids"]:
                continue
            rubric_id = docutils.nodes.make_id(rubric.astext())
            rubric["ids"].append(rubric_id)

        return nodes

    sphinx.directives.ObjectDescription.run = run  # type: ignore[assignment]


_monkey_patch_object_description_to_include_rubrics_in_toc()


@html_translator_mixin.override
def depart_term(
    self: html_translator_mixin.HTMLTranslatorMixin,
    node: docutils.nodes.term,
    super_func: html_translator_mixin.BaseVisitCallback[docutils.nodes.term],
) -> None:
    next_node: docutils.nodes.Element = node.next_node(descend=False, siblings=True)
    if not isinstance(next_node, docutils.nodes.classifier) and not (
        node.parent is not None
        and node.parent.parent is not None
        and isinstance(node.parent.parent.parent, sphinx.addnodes.glossary)
    ):
        self.add_permalink_ref(node, _("Permalink to this definition"))
    super_func(self, node)


def setup(app: sphinx.application.Sphinx):
    app.setup_extension("sphinx_immaterial.apidoc.object_description_options")
    object_description_options.add_object_description_option(
        app, "include_in_toc", type_constraint=bool, default=True
    )
    object_description_options.add_object_description_option(
        app, "toc_icon_text", type_constraint=Optional[str], default=None
    )
    object_description_options.add_object_description_option(
        app, "toc_icon_class", type_constraint=Optional[str], default=None
    )
    object_description_options.add_object_description_option(
        app, "include_fields_in_toc", type_constraint=bool, default=True
    )
    object_description_options.add_object_description_option(
        app, "include_rubrics_in_toc", type_constraint=bool, default=False
    )

    # TocTreeCollector is registered before our extension is.  In order for the
    # monkey patching to take effect, we need to unregister it and re-register it.
    for read_listener in app.events.listeners["doctree-read"]:
        obj = getattr(read_listener.handler, "__self__", None)
        if obj is not None and isinstance(obj, TocTreeCollector):
            obj.disable(app)
            app.add_env_collector(TocTreeCollector)
            break
    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
