from functools import partial

from soma.undefined import undefined

from . import WidgetFactory
from .list import (
    ListAnyWidgetFactory,
    ListFloatWidgetFactory,
    ListIntWidgetFactory,
    ListStrWidgetFactory,
)


class SetStrWidgetFactory(ListStrWidgetFactory):
    convert_from_list = set
    convert_to_list = staticmethod(
        lambda x: list(x) if x not in (None, undefined) else []
    )


class SetIntWidgetFactory(ListIntWidgetFactory):
    convert_from_list = set
    convert_to_list = staticmethod(
        lambda x: list(x) if x not in (None, undefined) else []
    )


class SetFloatWidgetFactory(ListFloatWidgetFactory):
    convert_from_list = set
    convert_to_list = staticmethod(
        lambda x: list(x) if x not in (None, undefined) else []
    )


class SetAnyWidgetFactory(ListAnyWidgetFactory):
    convert_from_list = set
    convert_to_list = staticmethod(
        lambda x: list(x) if x not in (None, undefined) else []
    )


def find_generic_set_factory(type, subtypes):
    if subtypes:
        item_type = subtypes[0]
        widget_factory = WidgetFactory.find_factory(item_type, default=None)
        if widget_factory is not None:
            return partial(SetAnyWidgetFactory, item_factory_class=widget_factory)
    return None
