"""A custom directive that allows using mermaid diagrams"""

from pathlib import Path
import shutil
from typing import List
from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util.docutils import SphinxDirective
from sphinx.application import Sphinx
from sphinx.environment import BuildEnvironment

# name of a flag to track if the mermaid dist is needed in the docs build
_COPY_MERMAID_DIST_ENV_KEY = "sphinx_immaterial_copy_mermaid_dist"


class mermaid_node(nodes.General, nodes.Element):
    pass


class MermaidDirective(SphinxDirective):
    """a special directive"""

    has_content = True
    option_spec = {
        "name": directives.unchanged,
        "class": directives.class_option,
    }

    def run(self) -> List[nodes.Node]:
        """Run the directive."""
        self.assert_has_content()
        content = "\n".join(self.content)
        diagram = mermaid_node("", classes=["mermaid"], content=content)
        diagram += nodes.literal("", content, format="html")
        diagram_div = nodes.container(
            "",
            is_div=True,
            classes=["mermaid-diagram"] + self.options.get("class", []),
        )
        if self.options.get("name", ""):
            self.add_name(diagram_div)
        diagram_div += diagram
        self.set_source_info(diagram_div)
        setattr(self.env, _COPY_MERMAID_DIST_ENV_KEY, True)
        return [diagram_div]


def visit_mermaid_node_html(self, node: mermaid_node):
    attributes = {"class": "mermaid"}
    self.body.append(self.starttag(node, "pre", **attributes))


def depart_mermaid_node_html(self, node: mermaid_node):
    self.body.append("</pre>")


def visit_mermaid_node_latex(self, node: mermaid_node):
    self.body.append("\n\\begin{sphinxVerbatim}[commandchars=\\\\\\{\\}]\n")


def depart_mermaid_node_latex(self, node: mermaid_node):
    self.body.append("\n\\end{sphinxVerbatim}\n")


def on_builder_init(app: Sphinx):
    """Init the copy-mermaid-dist flag to False"""
    setattr(app.env, _COPY_MERMAID_DIST_ENV_KEY, False)


def copy_mermaid_dist(app: Sphinx, env: BuildEnvironment):
    if app.builder.name not in ("html", "dirhtml"):
        return  # mermaid src is only used in HTML output
    if getattr(app.env, _COPY_MERMAID_DIST_ENV_KEY, False) is True:
        # copy the mermaid dist file (if not already done)
        dst = Path(app.outdir, "_static", "mermaid")
        if dst.exists():
            return
        shutil.copytree(str(Path(__file__).parent / "bundles" / "mermaid"), dst)


def _merge_env_key(
    app: Sphinx, env: BuildEnvironment, docnames: List[str], other: BuildEnvironment
) -> None:
    val = getattr(env, _COPY_MERMAID_DIST_ENV_KEY, False)
    setattr(
        env,
        _COPY_MERMAID_DIST_ENV_KEY,
        val or getattr(other, _COPY_MERMAID_DIST_ENV_KEY),
    )


def setup(app: Sphinx):
    app.connect("env-merge-info", _merge_env_key)
    app.add_directive("md-mermaid", MermaidDirective)
    app.add_node(
        mermaid_node,
        html=(visit_mermaid_node_html, depart_mermaid_node_html),
        latex=(visit_mermaid_node_latex, depart_mermaid_node_latex),
    )
    app.connect("builder-inited", on_builder_init)
    app.connect("env-check-consistency", copy_mermaid_dist)
    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
