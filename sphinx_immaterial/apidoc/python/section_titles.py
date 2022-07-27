import docutils.nodes
import docutils.statemachine

from sphinx.domains.python import PyObject
import sphinx.util.nodes


def _monkey_patch_python_domain_to_support_titles():
    """Enables support for titles in all Python directive types.

    Normally sphinx only supports titles in `automodule`, but the python_apigen
    extension uses titles to group member summaries.
    """

    orig_before_content = PyObject.before_content

    def before_content(self: PyObject) -> None:
        orig_before_content(self)
        setattr(self, "_saved_content", self.content)
        self.content = docutils.statemachine.StringList()

    orig_transform_content = PyObject.transform_content

    def transform_content(self: PyObject, contentnode: docutils.nodes.Node) -> None:
        sphinx.util.nodes.nested_parse_with_titles(
            self.state,
            getattr(self, "_saved_content"),
            contentnode,
        )
        orig_transform_content(self, contentnode)

    PyObject.before_content = before_content
    PyObject.transform_content = transform_content


_monkey_patch_python_domain_to_support_titles()
