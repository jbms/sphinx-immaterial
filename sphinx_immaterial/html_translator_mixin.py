"""Defines HTMLTranslatorMixin for overriding HTML translation.

Other extensions included with this theme add methods to the mixin.
"""

from typing import TYPE_CHECKING, TypeVar, Type, Callable, List

import docutils.nodes

import sphinx.writers.html5

if TYPE_CHECKING:
    HTMLTranslatorMixinBase = sphinx.writers.html5.HTML5Translator
else:
    HTMLTranslatorMixinBase = object


class HTMLTranslatorMixin(HTMLTranslatorMixinBase):
    pass


InitCallback = Callable[[HTMLTranslatorMixin], None]

_init_callbacks: List[InitCallback] = []


Element = TypeVar("Element", bound=docutils.nodes.Element)

BaseVisitCallback = Callable[
    [HTMLTranslatorMixin, Element],
    None,
]

VisitCallback = Callable[
    [
        HTMLTranslatorMixin,
        Element,
        BaseVisitCallback[Element],
    ],
    None,
]


def _override_visit_or_depart(method: str, callback: VisitCallback) -> None:
    prev_func = getattr(HTMLTranslatorMixin, method, None)

    def super_func(
        self: sphinx.writers.html5.HTML5Translator, node: docutils.nodes.Element
    ):
        if prev_func is not None:
            prev_func(self, node)
            return
        super_func = getattr(super(HTMLTranslatorMixin, self), method, None)
        if super_func is not None:
            super_func(node)

    def handler(self: HTMLTranslatorMixin, node: docutils.nodes.Element) -> None:
        callback(self, node, super_func)

    setattr(HTMLTranslatorMixin, method, handler)


def override(callback: VisitCallback):
    _override_visit_or_depart(callback.__name__, callback)


def init(callback: Callable[[HTMLTranslatorMixin], None]):
    _init_callbacks.append(callback)


def get_html_translator(
    base_translator: Type[sphinx.writers.html5.HTML5Translator],
) -> Type[sphinx.writers.html5.HTML5Translator]:
    class CustomHTMLTranslator(
        HTMLTranslatorMixin,
        base_translator,  # type: ignore
    ):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            # Ensure all tables are marked as data tables.  The material CSS only
            # applies to tables with this class, in order to leave tables used for
            # layout purposes alone.
            self.settings.table_style = ",".join(
                self.settings.table_style.split(",") + ["data"]
            )

            for callback in _init_callbacks:
                callback(self)

    return CustomHTMLTranslator
