"""Adds support for obtaining property types from docstring signatures, and
improves formatting by PyProperty of type annotations."""

import re
from typing import Tuple, Optional, Any

import sphinx
import sphinx.addnodes
import sphinx.domains
import sphinx.domains.python
import sphinx.ext.autodoc
import sphinx.util.inspect
import sphinx.util.typing

if sphinx.version_info >= (6, 1):
    stringify_annotation = sphinx.util.typing.stringify_annotation
else:
    stringify_annotation = sphinx.util.typing.stringify  # type: ignore[attr-defined]

PropertyDocumenter = sphinx.ext.autodoc.PropertyDocumenter


property_sig_re = re.compile("^(\\(.*)\\)\\s*->\\s*(.*)$")


def _get_property_getter(obj: Any) -> Any:
    # property
    func = sphinx.util.inspect.safe_getattr(obj, "fget", None)
    if func is None:
        # cached_property
        func = sphinx.util.inspect.safe_getattr(obj, "func", None)
    return func


def _get_return_type_from_fget_doc(obj: Any) -> Optional[str]:
    fget = _get_property_getter(obj)
    if fget is None:
        return None
    doc = sphinx.util.inspect.safe_getattr(fget, "__doc__", None)
    if doc is None:
        return None
    line = doc.splitlines()[0]
    line = line.rstrip("\\").strip()
    match = property_sig_re.match(line)
    if not match:
        return None
    _, retann = match.groups()
    return retann


def apply_property_documenter_type_annotation_fix():
    # Modify PropertyDocumenter to support obtaining signature from docstring.

    orig_import_object = PropertyDocumenter.import_object

    def import_object(self: PropertyDocumenter, raiseerror: bool = False) -> bool:
        result = orig_import_object(self, raiseerror)
        if not result:
            return False

        func = _get_property_getter(self.object)

        if func is not None:
            try:
                signature = sphinx.util.inspect.signature(
                    func, type_aliases=self.config.autodoc_type_aliases
                )
                if (
                    signature.return_annotation
                    is not sphinx.util.inspect.Parameter.empty
                ):
                    self.retann = stringify_annotation(signature.return_annotation)
                return True
            except Exception:
                pass

        if not self.retann:
            new_retann = _get_return_type_from_fget_doc(self.object)
            if new_retann is not None:
                self.retann = new_retann
        return True

    PropertyDocumenter.import_object = import_object  # type: ignore[assignment]

    old_add_directive_header = PropertyDocumenter.add_directive_header

    def add_directive_header(self, sig: str) -> None:
        start_line = len(self.directive.result.data)
        old_add_directive_header(self, sig)

        # Check for return annotation
        retann = self.retann or _get_return_type_from_fget_doc(self.object)
        if retann is None:
            return

        # Check if type annotation has already been added.
        type_line_prefix = self.indent + "   :type: "
        for line in self.directive.result.data[start_line:]:
            if line.startswith(type_line_prefix):
                return

        # Type annotation not already added.
        self.add_line("   :type: " + retann, self.get_sourcename())

    PropertyDocumenter.add_directive_header = add_directive_header  # type: ignore[assignment]

    # Modify PyProperty to improve formatting of :type: option
    PyProperty = sphinx.domains.python.PyProperty

    def handle_signature(
        self, sig: str, signode: sphinx.addnodes.desc_signature
    ) -> Tuple[str, str]:
        fullname, prefix = super(PyProperty, self).handle_signature(sig, signode)

        typ = self.options.get("type")
        if typ:
            signode += sphinx.addnodes.desc_sig_punctuation("", " : ")
            if sphinx.version_info >= (7, 3):
                signode += sphinx.domains.python._annotations._parse_annotation(
                    typ, self.env
                )
            else:
                signode += sphinx.domains.python._parse_annotation(typ, self.env)

        return fullname, prefix

    PyProperty.handle_signature = handle_signature  # type: ignore[assignment]


apply_property_documenter_type_annotation_fix()
