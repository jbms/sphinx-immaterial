"""Monkey patches a fix for https://github.com/sphinx-doc/sphinx/pull/11147."""

import inspect

import sphinx.directives
import sphinx.util.nodes
import sphinx.util.docutils


def _monkey_patch_nested_parse_with_titles():
    orig_nested_parse_with_titles = sphinx.util.nodes.nested_parse_with_titles

    if list(inspect.signature(orig_nested_parse_with_titles).parameters.keys()) != [
        "state",
        "content",
        "node",
    ]:
        # Assume https://github.com/sphinx-doc/sphinx/pull/11147 has been merged.
        return

    # Note that this is different from the fix in
    # https://github.com/sphinx-doc/sphinx/pull/11147, since it is not practical
    # to monkey patch all callers to pass in the `content_offset`.  Instead, we
    # use `switch_source_input`, which makes it unnecessary to pass in
    # `content_offset`.
    def nested_parse_with_titles(state, content, node):
        with sphinx.util.docutils.switch_source_input(state, content):
            return orig_nested_parse_with_titles(state, content, node)

    sphinx.util.nodes.nested_parse_with_titles = nested_parse_with_titles  # type: ignore[assignment]
    sphinx.directives.nested_parse_with_titles = nested_parse_with_titles  # type: ignore[assignment,attr-defined]


_monkey_patch_nested_parse_with_titles()
