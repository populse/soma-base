# -*- coding: utf-8 -*-

from functools import partial

from soma.controller.field import field_type_str, parse_type_str
from soma.qt_gui.qt_backend import Qt
from soma.undefined import undefined

class WidgetFactory:
    valid_style_sheet = ''
    warning_style_sheet = 'background: #FFFFC8;'
    invalid_style_sheet = 'background: #FFDCDC;'
    
    def __init__(self, controller_widget, parent_interaction):
        super().__init__()
        self.controller_widget = controller_widget
        self.parent_interaction = parent_interaction


    @classmethod
    def find_factory(cls, type_str, default=None):
        subtypes = []
        factory_finder = cls.widget_factory_types.get(type_str)
        if factory_finder is None:
            type_str, subtypes = parse_type_str(type_str)
            factory_finder = cls.widget_factory_types.get(type_str)
        if factory_finder is not None:
            if isinstance(factory_finder, type) and issubclass(factory_finder, WidgetFactory):
                return factory_finder
            else:
                factory_class = factory_finder(type_str, subtypes)
                if factory_class is not None:
                    return factory_class
        return default


class ControllerFieldInteraction:
    def __init__(self, controller, field):
        self.controller = controller
        self.field = field
    
    def get_value(self, default=undefined):
        return getattr(self.controller, self.field.name, default)

    def set_value(self, value):
        setattr(self.controller, self.field.name, value)
    
    def get_label(self):
        return self.controller.metadata(self.field, 'label', self.field.name)
    
    def on_change_add(self, callback):
        self.controller.on_attribute_change.add(callback, self.field.name)

    def on_change_remove(self, callback):
        self.controller.on_attribute_change.remove(callback, self.field.name)

    def set_protected(self, protected):
        self.controller.set_metadata(self.field, 'protected', protected)

    def inner_item_changed(self, index):
        value = self.get_value()
        self.controller.on_attribute_change.fire(self.field.name, value, value, self.controller, index)

    def type_str(self):
        return field_type_str(self.field)
    
    def is_optional(self):
        return self.controller.is_optional(self.field)


class ListItemInteraction:
    def __init__(self, parent_interaction, index):
        self.parent_interaction = parent_interaction
        self.index = index
    
    def get_value(self, default=undefined):
        values = self.parent_interaction.get_value()
        if values is not undefined:
            return values[self.index]
        return default

    def set_value(self, value):
        self.parent_interaction.get_value()[self.index] = value
    
    def get_label(self):
        return f'{self.parent_interaction.get_label()}[{self.index}]'
    
    def on_change_add(self, callback):
        pass

    def on_change_remove(self, callback):
        pass

    def set_protected(self, protected):
        pass

    def inner_item_changed(self, index):
        self.parent_interaction.inner_item_changed(index)

    def type_str(self):
        _, subtypes = parse_type_str(self.parent_interaction.type_str())
        return subtypes[0]
    
    def is_optional(self):
        return False
 

class DefaultWidgetFactory(WidgetFactory):
    def create_widgets(self):
        self.text_widget = Qt.QLineEdit(parent=self.controller_widget)
        self.text_widget.setStyleSheet('color: red;')
        self.text_widget.setReadOnly(True)
        self.text_widget.setToolTip(f'No graphical editor found for type {self.parent_interaction.type_str()}')

        self.parent_interaction.on_change_add(self.update_gui)
        self.update_gui()

        label = self.parent_interaction.get_label()
        self.label_widget = Qt.QLabel(label, parent=self.controller_widget)
        self.controller_widget.add_widget_row(self.label_widget, self.text_widget)

    def remove_widgets(self):
        self.parent_interaction.on_change_remove(self.update_gui)
        self.controller_widget.remove_widget_row()
        self.label_widget.deleteLater()
        self.text_widget.deleteLater()
    
    def update_gui(self):
        value = self.parent_interaction.get_value()
        self.text_widget.setText(f'{value}')

from .str import StrWidgetFactory
from .list import (ListStrWidgetFactory,
                   ListIntWidgetFactory,
                   ListFloatWidgetFactory,
                   find_generic_list_factory)

WidgetFactory.widget_factory_types = {
    'str': StrWidgetFactory,
    'int': StrWidgetFactory,
    'float': StrWidgetFactory,
    'list[str]': ListStrWidgetFactory,
    'list[int]': ListIntWidgetFactory,
    'list[float]': ListFloatWidgetFactory,
    'list': find_generic_list_factory,
}
