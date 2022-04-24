"""Utilities for use with Sphinx."""

from typing import Literal

import docutils.nodes


def summarize_element_text(
    node: docutils.nodes.Element,
    mode: Literal["first_paragraph", "first_sentence"] = "first_paragraph",
) -> str:
    """Extracts a short text synopsis, e.g. for use as a tooltip."""

    # Recurisvely extract first paragraph
    while True:
        for p in node.traverse(condition=docutils.nodes.paragraph):
            if p is node:
                continue
            node = p
            break
        else:
            break

    text = node.astext()
    if mode == "first_sentence":
        sentence_end = text.find(". ")
        if sentence_end != -1:
            text = text[: sentence_end + 1]
    text = text.replace("\n", " ")
    return text.strip()
