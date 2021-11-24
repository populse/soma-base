from .list import ListStrWidgetFactory, ListIntWidgetFactory, ListFloatWidgetFactory, ListAnyWidgetFactory

class SetStrWidgetFactory(ListStrWidgetFactory):
    convert_from_list = set
    convert_to_list = list


class SetIntWidgetFactory(ListIntWidgetFactory):
    convert_from_list = set
    convert_to_list = list


class SetFloatWidgetFactory(ListFloatWidgetFactory):
    convert_from_list = set
    convert_to_list = list


class SetAnyWidgetFactory(ListAnyWidgetFactory):
    convert_from_list = set
    convert_to_list = list


def find_generic_set_factory(type, subtypes):
    if subtypes:
        item_type = subtypes[0]
        widget_factory = WidgetFactory.find_factory(item_type, default=None)
        if widget_factory is not None:
            return partial(SetAnyWidgetFactory, item_factory_class=widget_factory)
    return None
