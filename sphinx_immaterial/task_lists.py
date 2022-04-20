"""A custom directive that allows using checkboxes for lists"""
from typing import List
from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util.docutils import SphinxDirective
from sphinx.application import Sphinx
from sphinx.writers.html import HTMLTranslator


def visit_checkbox_label(self: HTMLTranslator, node: nodes.Node):
    attributes = {}
    if node["custom"]:
        attributes = {"class": "task-list-control"}
    self.body.append(self.starttag(node, "label", **attributes))
    self.body.append('<input type="checkbox"')
    if node["disabled"]:
        self.body.append(" disabled ")
    if node["checked"]:
        self.body.append(" checked ")
    self.body.append(">")
    if node["custom"]:
        self.body.append('<span class="task-list-indicator"></span>')


def depart_checkbox_label(self: HTMLTranslator, node: nodes.Node):
    self.body.append("</label>")


class checkbox_label(nodes.container):
    pass


class TaskListDirective(SphinxDirective):
    """a special directive"""

    has_content = True
    optional_arguments = 4
    option_spec = {
        "name": directives.unchanged,
        "class": directives.class_option,
        "custom": directives.flag,
        "clickable": directives.flag,
    }

    def run(self) -> List[nodes.Node]:
        """Run the directive."""
        self.assert_has_content()
        task_list = nodes.container(
            "", is_div=True, classes=self.options.get("class", [])
        )
        if self.options.get("name", ""):
            self.add_name(task_list)
        clickable = "clickable" in self.options or self.config["clickable_checkbox"]
        custom = "custom" in self.options or self.config["custom_checkbox"]
        self.state.nested_parse(self.content, self.content_offset, task_list)
        self.set_source_info(task_list)

        def first_matching(obj, cls_t):
            return obj.first_child_matching_class(cls_t)

        for child in task_list.children:
            if isinstance(child, nodes.list_item):
                child["classes"] = ["task-list"]

            for li_ in child.children:
                if isinstance(li_, nodes.list_item):
                    if li_.astext().startswith("["):
                        li_["classes"] = ["task-list-item"]
                        checked = li_.astext().lower().startswith("[x]")
                        first_para = first_matching(li_, nodes.paragraph)
                        if first_para is not None:
                            first_text = first_matching(li_[first_para], nodes.Text)
                            li_[first_para][first_text] = li_[first_para][
                                first_text
                            ].lstrip("[x] ")
                            li_[first_para][first_text] = li_[first_para][
                                first_text
                            ].lstrip("[ ] ")
                        checkbox = checkbox_label(
                            "",
                            custom=custom,
                            disabled=not clickable,
                            checked=checked,
                        )
                        li_.insert(0, checkbox)

        return [task_list]


def setup(app: Sphinx):
    """Setup the extension."""
    app.add_directive("task-list", TaskListDirective)
    app.add_node(checkbox_label, html=(visit_checkbox_label, depart_checkbox_label))
    app.add_config_value("custom_checkbox", False, rebuild="html", types=bool)
    app.add_config_value("clickable_checkbox", False, rebuild="html", types=bool)
    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
