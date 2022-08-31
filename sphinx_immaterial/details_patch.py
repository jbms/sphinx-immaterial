from typing import List
from docutils import nodes

try:
    from sphinxcontrib.details.directive import (  # pytype: disable=import-error
        DetailsDirective,
    )

    IS_INSTALLED = True
except ImportError:
    IS_INSTALLED = False


def monkey_patch_details_run():
    """Patch the details directive to respect the class option.
    This solution is a temporary fix pending response from
    https://github.com/tk0miya/sphinxcontrib-details-directive/issues/4
    """

    def run(self) -> List[nodes.container]:
        admonition = nodes.container(
            "",
            classes=self.options.get("class", []) + self.options.get("classes", []),
            opened="open" in self.options,
            type="details",
        )
        textnodes, messages = self.state.inline_text(self.arguments[0], self.lineno)
        admonition += nodes.paragraph(self.arguments[0], "", *textnodes)
        admonition += messages
        self.state.nested_parse(self.content, self.content_offset, admonition)
        self.add_name(admonition)
        return [admonition]

    DetailsDirective.run = run


if IS_INSTALLED:
    monkey_patch_details_run()
