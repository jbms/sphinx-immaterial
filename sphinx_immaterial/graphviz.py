"""Extensions to the sphinx.ext.graphviz module."""

import html
import io
import os
import pathlib
import re
import subprocess
import tempfile
from typing import Optional, Any, Tuple, Dict, Type, Sequence, NamedTuple, Union
import xml.etree.ElementTree as ET

import docutils.nodes
import sphinx.application
import sphinx.ext.graphviz
import sphinx.util.docutils
import sphinx.util.logging
from sphinx.writers.html import HTMLTranslator
from sphinx.writers.html5 import HTML5Translator

from . import google_fonts
from . import sphinx_utils

logger = sphinx.util.logging.getLogger(__name__)


def _replace_resolved_xrefs(node: sphinx.ext.graphviz.graphviz, code: str) -> str:
    """Extracts any resolved references, and uses them to replace `xref`
    attributes in the DOT code.
    """
    ref_replacements = {}

    for child in node.children:
        if not isinstance(child, docutils.nodes.container):
            continue
        xref_id = child.get("xref_id")
        if xref_id is None:
            continue
        text = child.astext()
        ref_nodes = list(child.findall(condition=docutils.nodes.reference))

        title = None
        url = None
        target = None
        replacement_text = f"label=<{html.escape(text)}>"
        if ref_nodes:
            ref_node = ref_nodes[-1]
            refuri = ref_node.get("refuri")
            if refuri is not None:
                url = refuri or "#"
            else:
                url = "#" + ref_node["refid"]
            title = ref_node.get("reftitle")
            replacement_text += f' href="{url}"'
            if title is not None:
                replacement_text += f" tooltip=<{html.escape(title)}>"
            target = ref_node.get("target")
            if target is not None:
                replacement_text += f' target="{target}"'

        ref_replacements[xref_id] = replacement_text

    if ref_replacements:
        ref_pattern = "|".join(ref_replacements.keys())
        code = re.sub(ref_pattern, lambda m: ref_replacements[m.group(0)], code)
    return code


class GraphvizConfigInfo(NamedTuple):
    """Adjusted graphviz configuration.

    This extension configures Graphviz to use use the same font (from Google
    Fonts) that is used for other document text.

    Note that when generating SVG output, Graphviz uses the font just to compute
    the size of labels.  The web browser is still responsible for loading the
    font and rendering the text.  Therefore, the font needs to be available both
    to Graphviz and the web browser.

    Since the font already needs to be available to the web browser for other
    document text, there is no added complication there.  But making the font
    available to Graphviz is non-trivial:

    - Graphviz supports several mechanisms for text layout:

      - LibGD, always available on Linux, sometimes on Windows, and allows TTF
        font paths to be specified directly;

      - Pango and/or GDI+ (Windows only), relies on systems-specific font paths
        and does not allow paths to TTF fonts to be specified directly.

      Therefore, LibGD must be used, but unfortunately, depending on how
      Graphviz is built, Pango and/or GDI+ is normally used by default.

    - Graphviz does not provide any command-line options for controlling which
      plugins are loaded.  Instead, plugins can only be loaded through a config
      file.

    Therefore, to ensure LibGD is used for fonts, it is necessary to locate the
    original config file, parse it and remove the section that loads Pango, if
    present, and write it to a new temporary directory.

    """

    orig_config_path: str
    """Path to original config file."""

    new_config: bytes
    """New config content with pango excluded."""


def get_adjusted_graphviz_config(
    app: sphinx.application.Sphinx, dot_command: str
) -> Optional[GraphvizConfigInfo]:
    """Returns the graphviz configuration info for a given `dot_command`.

    The returned config file must be written to a temporary directory with a
    symlink "plugins" to the `orig_config_path`.
    """
    key = "_sphinx_immaterial_graphviz_adjusted_configs"
    configs = getattr(app, key, None)
    if configs is None:
        configs = {}
        setattr(app, key, configs)
    config = configs.get(dot_command, False)
    if config is False:
        config = _make_adjusted_graphviz_config(app, dot_command)
        configs[dot_command] = config
    return config


def _get_orig_config_path(dot_command: str) -> Optional[str]:
    result = subprocess.run(
        [dot_command, "-v"], input="", text=True, capture_output=True, check=True
    )

    m = re.search(
        r"^The plugin configuration file:\s+(.*)$\s+was successfully loaded\.$",
        result.stderr,
        re.MULTILINE,
    )
    if m is None:
        logger.error(
            "Failed to determine graphviz config path from stderr: %r", result.stderr
        )
        return None

    return m.group(1)


def _make_adjusted_graphviz_config(
    app: sphinx.application.Sphinx, dot_command: str
) -> Optional[GraphvizConfigInfo]:
    """Determines the graphviz libdir and generates an adjusted config.

    This is called by `get_adjusted_graphviz_config`.
    """

    orig_config_path = _get_orig_config_path(dot_command)
    if orig_config_path is None:
        return None

    config_content = pathlib.Path(orig_config_path).read_bytes()

    # Strip comments
    config_content = re.sub(b"#[^\n]*", b"", config_content)

    new_config = io.BytesIO()

    prev_index = 0

    def parse_error():
        logger.error(
            "Failed to parse graphviz config file %r, starting at: %r",
            orig_config_path,
            config_content[prev_index:],
        )

    found_gd = False

    # Match plugins
    for m in re.finditer(
        rb"\s*([^\s{}]+)\s+([^\s{}]+)\s*(\{\s*(?:[^{}\s]+\s*\{[^{}]*\}\s*)*\s*\})\s*",
        config_content,
    ):
        if m.start() != prev_index:
            parse_error()
            return None
        prev_index = m.end()
        plugin_path = m.group(1)
        plugin_name = m.group(2)
        plugin_config = m.group(3)
        if plugin_name == b"gd":
            found_gd = True
        else:
            plugin_config = re.sub(rb"\btextlayout\s*\{[^}]*\}", b"", plugin_config)
        if not os.path.isabs(plugin_path):
            plugin_path = os.path.join(b"plugins", plugin_path)
        new_config.write(plugin_path)
        new_config.write(b" ")
        new_config.write(plugin_name)
        new_config.write(b" ")
        new_config.write(plugin_config)

    if prev_index != len(config_content):
        parse_error()
        return None

    if not found_gd:
        if not app.config.graphviz_ignore_incorrect_font_metrics:
            logger.warning(
                "Incorrect font metrics will be used because "
                "graphviz binary %r does not have LibGD support.  This warning is expected on x86_64 Windows "
                "(https://gitlab.com/graphviz/graphviz/-/issues/2267). "
                "Set `graphviz_ignore_incorrect_font_metrics = True` in `conf.py` "
                "to silence this warning.",
                dot_command,
            )
        return None

    return GraphvizConfigInfo(
        orig_config_path=orig_config_path, new_config=new_config.getvalue()
    )


def render_dot_html(
    self: Union[HTMLTranslator, HTML5Translator],
    node: sphinx.ext.graphviz.graphviz,
    code: str,
    options: dict,
    prefix: str = "graphviz",
    imgcls: Optional[str] = None,
    alt: Optional[str] = None,
    filename: Optional[str] = None,
) -> Tuple[str, str]:
    theme_options = self.builder.config["html_theme_options"]
    font: Optional[str] = None
    if isinstance(theme_options["font"], dict) and "text" in theme_options["font"]:
        # using a google font; otherwise
        font = theme_options["font"]["text"]

    ttf_font_paths = google_fonts.get_ttf_font_paths(self.builder.app)
    ttf_font: Optional[str] = None
    if ttf_font_paths and font is not None:
        try:
            # can only support the chosen font if cache exists and a Google font is used
            ttf_font = ttf_font_paths[(font, "400")]
        except KeyError as exc:
            # weight `400` might not exist for the specified font
            all_font_keys = [i for i in ttf_font_paths.keys() if i[0] == font]
            if not all_font_keys:
                raise FileNotFoundError(
                    f"Font file for {font} could not be found in cache"
                ) from exc
            # just use first weight for the specified font
            ttf_font = ttf_font_paths[all_font_keys[0]]

    if ttf_font is not None and os.sep != "/":
        ttf_font = ttf_font.replace(os.sep, "/")

    code = _replace_resolved_xrefs(node, code)

    var_replacements: Dict[str, str] = {}
    replacement_to_var: Dict[str, str] = {}

    def replace_var(var_text: str) -> str:
        replacement_color = var_replacements.setdefault(
            var_text, "#%06x" % (0x123456 + len(var_replacements))
        )
        replacement_to_var.setdefault(replacement_color, var_text)
        return replacement_color

    def replace_var_in_code(m: re.Match) -> str:
        var_text = m.group(1)
        replacement_color = replace_var(var_text)
        return f'"{replacement_color}"'

    fontcolor = replace_var("var(--md-code-fg-color)")
    fontsize = "12"

    graphviz_dot = options.get("graphviz_dot", self.builder.config.graphviz_dot)
    config_info = get_adjusted_graphviz_config(self.builder.app, graphviz_dot)

    if config_info is None:
        ttf_font = font

    command_line_options = [
        "-Ncolor=" + replace_var("var(--md-graphviz-node-fg-color)"),
        "-Nstyle=solid,filled",
        "-Nfillcolor=" + replace_var("var(--md-graphviz-node-bg-color)"),
        "-Nfontcolor=" + fontcolor,
        "-Nfontsize=" + fontsize,
        "-Ecolor=" + replace_var("var(--md-graphviz-edge-color)"),
        "-Efontcolor=" + fontcolor,
        "-Efontsize=" + fontsize,
        "-Gbgcolor=transparent",
        "-Gcolor=" + replace_var("var(--md-graphviz-node-fg-color)"),
        "-Gfontcolor=" + fontcolor,
        "-Gfontsize=" + fontsize,
    ]
    if ttf_font is not None:
        command_line_options.extend(
            [
                "-Nfontname=" + ttf_font,
                "-Efontname=" + ttf_font,
                "-Gfontname=" + ttf_font,
            ]
        )

    code = re.sub(r'"((?:var|calc)\s*\(.*?\))"', replace_var_in_code, code)

    dot_cmd = [graphviz_dot]
    dot_cmd.extend(command_line_options)
    dot_cmd.extend(self.builder.config.graphviz_dot_args)
    dot_cmd.append("-Tsvg")

    with tempfile.TemporaryDirectory() as tempdir:
        env = os.environ.copy()
        if config_info is not None and ttf_font is not None:
            orig_lib_path = pathlib.Path(config_info.orig_config_path)
            new_lib_dir = pathlib.Path(tempdir, "plugins")
            pathlib.Path(tempdir, orig_lib_path.name).write_bytes(
                config_info.new_config
            )

            env["GVBINDIR"] = tempdir
            new_lib_dir.symlink_to(orig_lib_path.parent, target_is_directory=True)
            cwd = str(orig_lib_path.parent)
        else:
            cwd = None
        dot_result = subprocess.run(
            dot_cmd,
            input=code,
            encoding="utf-8",
            check=False,
            env=env,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        svg_output = dot_result.stdout
        errors = dot_result.stderr.strip()
        if config_info is None:
            # Filter warnings about fonts
            errors = re.sub(r"^.*couldn\'t load font .*$", "", errors, re.MULTILINE)
        errors = errors.strip()
        if errors or dot_result.returncode != 0:
            error_func = logger.warning if dot_result.returncode == 0 else logger.error
            error_func(  # type: ignore[operator]
                "Error running %r with env %r: %s", dot_cmd, env, errors, location=node
            )
            if dot_result.returncode != 0:
                raise docutils.nodes.SkipNode

    ET.register_namespace("", "http://www.w3.org/2000/svg")
    root = ET.fromstring(svg_output)
    xlink_href_key = "{http://www.w3.org/1999/xlink}href"
    xlink_title_key = "{http://www.w3.org/1999/xlink}title"
    a_tag = "{http://www.w3.org/2000/svg}a"
    text_tag = "{http://www.w3.org/2000/svg}text"

    for element in root.iter():
        style = ""
        attrib = element.attrib
        for attr in ("fill", "stroke"):
            attrib_val = attrib.get(attr)
            if attrib_val is None:
                continue
            var_val = replacement_to_var.get(attrib_val)
            if var_val is not None:
                del attrib[attr]
                style += f"{attr}: {var_val};"
        font_family = attrib.get("font-family")
        if font is not None and font_family == ttf_font:  # using a cached google font
            attrib["font-family"] = font
        elif font is None and font_family is not None:  # using a system font (via CSS)
            attrib.pop("font-family")
            style += "font-family: var(--md-text-font-family);"
        href = attrib.pop(xlink_href_key, None)
        if href is not None:
            attrib["href"] = href
        title = attrib.pop(xlink_title_key, None)
        if title is not None:
            title_element = ET.Element("title")
            title_element.text = title
            element.append(title_element)
        if element.tag == a_tag:
            for child in element:
                if child.tag == text_tag:
                    child.attrib["within_a"] = "true"
        within_a = attrib.pop("within_a", None)
        if within_a:
            style += "--md-graphviz-hover-color: var(--md-graphviz-a-hover-color);"
        if style:
            attrib["style"] = style

    classes = [imgcls, "graphviz"] + node.get("classes", [])
    imgcls = " ".join(filter(None, classes))
    root.attrib["class"] = (root.attrib.get("class", "") + " " + imgcls).strip()

    base_scale = 0.75

    def convert_width_or_height(s: str):
        assert s.endswith("pt")
        val_pt = float(s[:-2])
        val_px = val_pt / 0.75
        val_rem = val_px / 16 * base_scale
        return f"{val_rem}rem"

    root_style = ""
    for attr in ("width", "height"):
        attrib_val = root.attrib.pop(attr, None)
        if attrib_val is not None:
            root_style += f"{attr}: {convert_width_or_height(attrib_val)};"
    if root_style:
        root.attrib["style"] = root_style

    svg_output = ET.tostring(root, encoding="unicode")

    if alt is None:
        alt = node.get("alt", self.encode(code).strip())
    if "align" in node:
        self.body.append(
            '<div align="%s" class="align-%s">' % (node["align"], node["align"])
        )
    self.body.append(svg_output)
    if "align" in node:
        self.body.append("</div>\n")

    raise docutils.nodes.SkipNode


def _replace_var_refs_with_defaults(code: str) -> str:
    code = re.sub(r'"var\s*\(.*?,\s*(.*)\)"', lambda m: f'"{m.group(1)}"', code)
    return code


def on_build_finished(*args, **kwargs) -> None:
    # Suppress inclusion of the graphviz.css file supplied by
    # `sphinx.ext.graphviz`.  This theme provides its own style rules.
    pass


sphinx.ext.graphviz.on_config_inited = on_build_finished  # type: ignore[attr-defined]
sphinx.ext.graphviz.on_build_finished = on_build_finished  # type: ignore[attr-defined]


def _preprocess_graphviz_node(
    directive: sphinx.util.docutils.SphinxDirective,
    node: sphinx.ext.graphviz.graphviz,
    line_offset: int,
) -> None:
    code = node["code"]

    xrefs: Dict[str, Tuple[str, int]] = {}

    def replace_xref(m: re.Match) -> str:
        line_index = code.count("\n", 0, m.start())
        xref_text = m.group(1).replace(r"\"", '"')
        xref_index = len(xrefs)
        xref_id = f"__SPHINX_IMMATERIAL_XREF_{xref_index}__"
        xref_id, _ = xrefs.setdefault(xref_text, (xref_id, line_index - line_offset))
        return xref_id

    code = re.sub(r'\bxref\s*=\s*"((?:[^\\"]*|(?:\\.|"))*)"', replace_xref, code)

    node["code"] = code

    filename = node.get("filename")

    for xref_text, (xref_id, line_index) in xrefs.items():
        container = docutils.nodes.container()
        container["xref_id"] = xref_id

        # Determine source location
        if filename is None:
            source_path, source_offset = directive.content.items[line_index]
        else:
            source_path = os.path.join(directive.env.app.srcdir, filename)
            source_offset = line_index

        nodes = sphinx_utils.parse_rst(
            state=directive.state,
            text=xref_text,
            source_path=source_path,
            source_line=source_offset,
        )
        container += nodes
        node += container


def _monkey_patch_graphviz_directive(
    directive: Type[sphinx.util.docutils.SphinxDirective], line_offset: int
):
    orig_run = directive.run

    def run(
        self: sphinx.util.docutils.SphinxDirective,
    ) -> Sequence[docutils.nodes.Node]:
        nodes = orig_run(self)
        for node in nodes:
            for graphviz_node in node.findall(condition=sphinx.ext.graphviz.graphviz):
                _preprocess_graphviz_node(self, graphviz_node, line_offset)
        return nodes

    directive.run = run  # type: ignore[assignment]


_monkey_patch_graphviz_directive(sphinx.ext.graphviz.Graphviz, line_offset=0)
_monkey_patch_graphviz_directive(sphinx.ext.graphviz.GraphvizSimple, line_offset=2)


def _monkey_patch_render_dot(name: str) -> None:
    orig_render = getattr(sphinx.ext.graphviz, name)

    def render_dot(
        self, node: sphinx.ext.graphviz.graphviz, code: str, options: Dict, **kwargs
    ):
        code = _replace_resolved_xrefs(node, code)
        code = _replace_var_refs_with_defaults(code)
        return orig_render(self, node, code, options, **kwargs)

    setattr(sphinx.ext.graphviz, name, render_dot)


sphinx.ext.graphviz.render_dot_html = render_dot_html
_monkey_patch_render_dot("render_dot_texinfo")
_monkey_patch_render_dot("render_dot_latex")


def setup(app: sphinx.application.Sphinx) -> Dict[str, Any]:
    app.setup_extension("sphinx.ext.graphviz")
    app.add_config_value(
        "graphviz_ignore_incorrect_font_metrics",
        types=(bool,),
        default=False,
        rebuild="env",
    )
    sphinx_utils.remove_css_file(app, "graphviz.css")
    return {"parallel_read_safe": True, "parallel_write_safe": True}
