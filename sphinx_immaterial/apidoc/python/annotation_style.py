from typing import Optional, List

import docutils.nodes
import sphinx.domains.python
import sphinx.environment


def ensure_wrapped_in_desc_type(
    nodes: List[docutils.nodes.Node],
) -> List[docutils.nodes.Node]:
    if len(nodes) != 1 or not isinstance(nodes[0], sphinx.addnodes.desc_type):
        nodes = [sphinx.addnodes.desc_type("", "", *nodes)]
    return nodes


def _monkey_patch_python_parse_annotation():
    """Ensures that type annotations in signatures are wrapped in `desc_type`.

    This allows them to be distinguished from parameter names in CSS rules.
    """
    orig_parse_annotation = sphinx.domains.python._parse_annotation

    def parse_annotation(
        annotation: str, env: Optional[sphinx.environment.BuildEnvironment] = None
    ) -> List[docutils.nodes.Node]:
        return ensure_wrapped_in_desc_type(orig_parse_annotation(annotation, env))

    sphinx.domains.python._parse_annotation = parse_annotation


_monkey_patch_python_parse_annotation()
