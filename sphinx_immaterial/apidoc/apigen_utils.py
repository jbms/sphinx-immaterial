"""Common utilities needed by the language-specific apigen modules."""

import glob
import hashlib
import os
import pathlib
import secrets
from typing import Optional, List, Dict, Iterator, Tuple

import sphinx.application
import sphinx.util.logging

logger = sphinx.util.logging.getLogger(__name__)


def _is_case_insensitive_filesystem(path: str, initial_comment: str) -> bool:
    suffix = secrets.token_hex(16)
    temp_path = path + suffix + "a.rst"
    try:
        pathlib.Path(temp_path).write_text(initial_comment, encoding="utf-8")
        return os.path.exists(path + suffix + "A.rst")
    finally:
        os.remove(temp_path)


def _is_generated_file(rst_path: str, initial_comment: str) -> bool:
    try:
        if os.path.islink(rst_path) or not os.path.isfile(rst_path):
            return False
        content = pathlib.Path(rst_path).read_text(encoding="utf-8")
        return content.startswith(initial_comment)
    except:  # pylint: disable=bare-except
        return False


def make_unique_docname(orig_docname: str, case_insensitive_filesystem: bool) -> str:
    if not case_insensitive_filesystem:
        return orig_docname
    name_hash = hashlib.sha256(
        os.path.basename(orig_docname).encode("utf-8")
    ).hexdigest()[:8]
    return f"{orig_docname}-{name_hash}"


class GeneratedDocumentWriter:
    def __init__(
        self,
        app: sphinx.application.Sphinx,
        case_insensitive_filesystem: Optional[bool],
        output_prefixes: List[str],
        generator_module: str,
    ):
        self.app = app
        self._case_insensitive_filesystem = case_insensitive_filesystem
        self.initial_comment = f"..\n  DO NOT EDIT. GENERATED by {generator_module}.\n"
        self.output_prefixes = output_prefixes
        self.all_pages: Dict[str, str] = {}

    def prepare_output_directories(self) -> None:
        seen_output_dirs = set()
        for output_prefix in self.output_prefixes:
            output_dir = os.path.dirname(os.path.join(self.app.srcdir, output_prefix))
            if output_dir in seen_output_dirs:
                continue
            seen_output_dirs.add(output_dir)
            os.makedirs(output_dir, exist_ok=True)
            if self._case_insensitive_filesystem is None:
                if _is_case_insensitive_filesystem(
                    os.path.join(self.app.srcdir, output_prefix), self.initial_comment
                ):
                    self._case_insensitive_filesystem = True
        if self._case_insensitive_filesystem is None:
            self._case_insensitive_filesystem = False

    @property
    def case_insensitive_filesystem(self) -> bool:
        value = self._case_insensitive_filesystem
        assert value is not None
        return value

    def clear_existing_generated_files(self):
        srcdir = self.app.srcdir
        for output_prefix in self.output_prefixes:
            glob_pattern = os.path.join(srcdir, output_prefix)
            for p in glob.glob(
                os.path.join(srcdir, output_prefix + "*.rst"), recursive=True
            ):
                if not _is_generated_file(p, self.initial_comment):
                    continue
                try:
                    os.remove(p)
                except OSError as e:
                    logger.warning("Failed to remove stale generated file %r: %s", p, e)

    def write_file(self, docname: str, object_name: str, entity_content: str):

        rst_path = docname + ".rst"
        if rst_path in self.all_pages:
            logger.error(
                "Both %r and %r map to generated path %r",
                self.all_pages[rst_path],
                object_name,
                rst_path,
            )
            return

        self.all_pages[rst_path] = object_name

        content = self.initial_comment
        # Suppress "Edit this page" link since the page is generated.
        content += "\n\n:hide-edit-link:\n\n"
        content += entity_content
        rst_path = os.path.join(self.app.srcdir, docname + ".rst")
        if os.path.exists(rst_path):
            logger.error(
                "Generated documentation page for %r would overwrite existing source file %r",
                object_name,
                rst_path,
            )
            return
        pathlib.Path(rst_path).write_text(content, encoding="utf-8")

    def write_files(self, entities: Iterator[Tuple[str, str, str]]):
        self.clear_existing_generated_files()
        for docname, object_name, entity_content in entities:
            self.write_file(docname, object_name, entity_content)
