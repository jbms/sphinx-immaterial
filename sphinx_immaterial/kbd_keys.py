from typing import List, Tuple
from docutils import nodes
from sphinx.application import Sphinx
from sphinx.config import Config
from sphinx.writers.html import HTMLTranslator
from sphinx.util.logging import getLogger

LOGGER = getLogger(__name__)

try:
    import pymdownx.keymap_db as keys_db  # pytype: disable=import-error

    HAS_DB = True
except ImportError:
    LOGGER.info(
        "Could not import `keymap_db` module from `pymdownx` package.\n    "
        "Please ensure `pymdown-extensions` is installed.\n    "
        "The `:keys:` role has no default key map."
    )
    HAS_DB = True


class kbd_node(nodes.TextElement):
    pass


def map_filter(key: str, user_map: dict) -> Tuple[str, str]:
    display = key.title()
    cls = key.replace("_", "-").replace(" ", "-").lower()
    if key in user_map.keys():
        display = user_map[key]
    if HAS_DB:
        if key in keys_db.aliases:
            display = keys_db.keymap[keys_db.aliases[key]]
            cls = keys_db.aliases[key]
    return (cls, display)


def visit_kbd(self: HTMLTranslator, node: kbd_node):
    tag = "kbd" if self.builder.config["keys_strict"] else "span"
    self.body.append(f'<{tag} class="' + f'{self.builder.config["keys_class"]}"')
    keys = node.rawsource.split(self.builder.config["keys_separator"])

    keys_out = ">"
    for i, key in enumerate(keys):
        cls, text = map_filter(key.strip().lower(), self.builder.config["keys_map"])
        keys_out += f'<kbd class="key-{cls}">{text}</kbd>'
        if i + 1 != len(keys):
            keys_out += f'<span>{self.builder.config["keys_separator"]}</span>'
    self.body.append(keys_out)


def depart_kbd(self, node):
    tag = "kbd" if self.builder.config["keys_strict"] else "span"
    self.body.append(f"</{tag}>")


def visit_kbd_latex(self, node):
    keys = node.rawsource.split(self.builder.config["keys_separator"])
    for i, key in enumerate(keys):
        _, text = map_filter(key.strip().lower(), self.builder.config["keys_map"])
        self.body.append(text)
        if i + 1 < len(keys):
            self.body.append(f' {self.builder.config["keys_separator"]} ')


def depart_kbd_latex(self, node):
    pass


def keys_role(
    role, rawtext, text, lineno, inliner, options={}, content=[]
) -> Tuple[List[nodes.Node], List[str]]:
    keys_div = kbd_node(text)
    return [keys_div], []


def _config_inited(app: Sphinx, config: Config) -> None:
    """Merge default `keys_db.keymap` with user-specified `keys_map` role option."""
    if HAS_DB and app.config["keys_map"].keys():
        keys_db.keymap.update(**app.config["keys_map"])
        app.config["keys_map"] = keys_db.keymap


def setup(app: Sphinx):
    app.add_config_value("keys_class", "keys", rebuild="env", types=str)
    app.add_config_value("keys_strict", False, rebuild="env", types=bool)
    app.add_config_value("keys_separator", "+", rebuild="env", types=str)
    app.add_config_value("keys_map", {}, rebuild="env", types=dict)
    app.add_role("keys", keys_role)
    app.connect("config-inited", _config_inited)
    app.add_node(
        kbd_node,
        html=(visit_kbd, depart_kbd),
        latex=(visit_kbd_latex, depart_kbd_latex),
    )
    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
