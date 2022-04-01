from typing import List, Tuple
from docutils import nodes
from sphinx.application import Sphinx
from sphinx.config import Config
from sphinx.writers.html import HTMLTranslator
from sphinx.util.logging import getLogger

LOGGER = getLogger(__name__)

try:
    import pymdownx.keymap_db as keys_db
except ImportError:
    LOGGER.info(
        "Could not import `keymap_db` module from `pymdownx` package.\n    "
        "Please ensure `pymdown-extensions` is installed.\n    "
        "The `:keys:` role has no default key map."
    )
    keys_db = None


class spanNode(nodes.container):
    pass


def visit_span(self: HTMLTranslator, node: spanNode):
    self.body.append("<span")
    if "classes" in node and node.get("classes"):
        self.body.append(
            f' class="{" ".join([self.attval(cls) for cls in node["classes"]])}"'
        )
    if "text" in node:
        self.body.append(">" + node["text"])
    else:
        self.body.append(">")


def depart_span(self: HTMLTranslator, node: spanNode):
    self.body.append("</span>")


class kbdNode(nodes.container):
    pass


def visit_kbd(self, node):
    self.body.append(
        '<kbd class="' + f'{" ".join([self.attval(cls) for cls in node["classes"]])}'
    )
    if "text" in node:
        self.body.append('">' + node["text"])
    else:
        self.body.append('">')


def depart_kbd(self, node):
    self.body.append("</kbd>")


def keys_role(
    role, rawtext, text, lineno, inliner, options={}, content=[]
) -> Tuple[List[nodes.Node], List[str]]:
    keys = text.split(KEYS_OPTS["keys_sep"])
    keys_div = spanNode("", classes=[KEYS_OPTS["keys_class"]])
    if KEYS_OPTS["keys_strict"]:
        keys_div = kbdNode("", classes=[KEYS_OPTS["keys_class"]])
    keys_out = []

    def map_filter(key: str) -> Tuple[str, str]:
        display = key.title()
        cls = key.replace("_", "-").replace(" ", "-").lower()
        if key in KEYS_OPTS["keys_map"].keys():
            display = KEYS_OPTS["keys_map"][key]
        if keys_db is not None:
            if key in keys_db.aliases.keys():
                display = keys_db.keymap[keys_db.aliases[key]]
                cls = keys_db.aliases[key]
        return (cls, display)

    for i, key in enumerate(keys):
        key_cls, key_display = map_filter(key.strip().lower())
        keys_key = kbdNode("", classes=["key-" + key_cls])
        keys_key["text"] = key_display
        keys_out.append(keys_key)
        if i + 1 != len(keys):
            keys_sep = spanNode("", classes=[])
            keys_sep["text"] = KEYS_OPTS["keys_sep"]
            keys_out.append(keys_sep)
    keys_div += keys_out
    return [keys_div], []


KEYS_OPTS = {"keys_map": ({} if keys_db is None else keys_db.keymap.copy())}


def _config_inited(app: Sphinx, config: Config) -> None:
    """Set defaults for `key` role options based on conf.py vars."""
    KEYS_OPTS["keys_class"] = app.config["keys_class"]
    KEYS_OPTS["keys_sep"] = app.config["keys_separator"]
    KEYS_OPTS["keys_strict"] = app.config["keys_strict"]
    if app.config["keys_map"].keys():
        KEYS_OPTS["keys_map"].update(**app.config["keys_map"])


def setup(app: Sphinx):
    app.add_config_value("keys_class", "keys", rebuild=True, types=str)
    app.add_config_value("keys_strict", False, rebuild=True, types=bool)
    app.add_config_value("keys_separator", "+", rebuild=True, types=str)
    app.add_config_value("keys_map", {}, rebuild=True, types=dict)
    app.add_role("keys", keys_role)
    app.connect("config-inited", _config_inited)
    app.add_node(spanNode, html=(visit_span, depart_span))
    app.add_node(kbdNode, html=(visit_kbd, depart_kbd))
