# -*- coding: utf-8 -*-

from functools import partial

from pydantic import ValidationError

from ..qt_backend import Qt, QtCore
from . import WidgetFactory
from ..collapsable import CollapsableWidget
from ..timered_widgets import TimeredQLineEdit
from soma.undefined import undefined
from soma.controller import (field_type_str,
                             parse_type_str,
                             type_str_default_value)


class ListStrWidget(CollapsableWidget):
    ROW_SIZE = 10
    item_modification = QtCore.Signal(int)

    def __init__(self, label: str, *args, **kwargs):
        self.grid_widget = Qt.QWidget()
        self.layout = Qt.QGridLayout(self.grid_widget)
        self.inner_widgets = []
        super().__init__(self.grid_widget, label, *args, **kwargs)
        self.grid_widget.setContentsMargins(self.toggle_button.sizeHint().height(),0,0,0)

    def set_values(self, values):
        # Remove item widgets if new list is shorter than current one
        while len(values) < self.layout.count():
            index = self.layout.count() - 1
            item = self.layout.takeAt(index)
            if item.widget():
                item.widget().userModification.disconnect()
                self.layout.removeWidget(item.widget())
                self.inner_widgets = self.inner_widgets[:-1]
                item.widget().deleteLater()
        # Add item widgets if new list is longer than current one
        while len(values) > self.layout.count():
            pos = self.layout.count()
            column = pos % self.ROW_SIZE
            row = int(pos / self.ROW_SIZE) 
            widget = TimeredQLineEdit(parent=self.grid_widget)
            widget.setMinimumWidth(10)
            widget.setSizePolicy(Qt.QSizePolicy.Ignored, Qt.QSizePolicy.Fixed)
            self.inner_widgets.append(widget)
            self.layout.addWidget(widget, row, column)
            widget.userModification.connect(partial(self.item_widget_modification, pos))
        # Set values
        for index, value in enumerate(values):
            self.set_value(value, index)

    def get_values(self):
        return [self.get_value(i) for i in range(len(self.inner_widgets))]

    def set_value(self, value, index):
        widget = self.inner_widgets[index]
        if value is undefined:
            widget.setStyleSheet(WidgetFactory.invalid_style_sheet)
        else:
            widget.setStyleSheet(WidgetFactory.valid_style_sheet)
            widget.setText(f'{value}')

    def get_value(self, index):
        return self.inner_widgets[index].text()

    def item_widget_modification(self, index):
        self.item_modification.emit(index)


# class ListAnyWidget(CollapsableWidget):
#     def __init__(self, widget_class : type, values: list, label: str, *args, **kwargs):
#         inner_widget = Qt.QWidget()
#         layout = Qt.QVBoxLayout(inner_widget)
#         self.inner_widgets = []
#         for i in range(len(values)):
#             widget = widget_class(values[i], f'{label}[{i}]', parent=inner_widget)
#             self.inner_widgets.append(widget)
#             layout.addWidget(widget)
#         super().__init__(inner_widget, label, *args, **kwargs)


class ListStrWidgetFactory(WidgetFactory):
    list_widget_class = ListStrWidget

    def create_widgets(self):
        label = self.controller.metadata(self.field.name, 'label', self.field.name)
        self.widget = self.list_widget_class(label=label, expanded=True, 
            buttons_label=['+', '-'], parent=self.controller_widget)

        values = getattr(self.controller, self.field.name, undefined)
        self.update_gui(values, undefined, self.field.name, self.controller, None)
        self.controller.on_attribute_change.add(self.update_gui, self.field.name)

        self.widget.item_modification.connect(self.update_controller_item)
        self.widget.buttons[0].clicked.connect(self.add_item)
        self.widget.buttons[1].clicked.connect(self.remove_item)
        
        self.controller_widget.add_widget_row(self.widget)

    def update_gui(self, new_value, old_value, attribute_name, controller, index):
        if new_value is undefined:
            self.widget.set_values([])
        else:
            if index is None:
                self.widget.set_values(new_value)
            else:
                self.widget.set_value(new_value[index], index)

    def update_controller(self):
        try:
            setattr(self.controller, self.field.name, self.widget.get_values())
        except ValidationError:
            pass
        else:
            self.controller.set_metadata(self.field, 'protected', False)
    
    def update_controller_item(self, index):
        values = getattr(self.controller, self.field.name, undefined)
        if values is not undefined:
            new_value = self.widget.get_value(index)
            self.widget.inner_widgets[index].setStyleSheet(self.valid_style_sheet)
            old_value = values[index]
            if new_value != old_value:
                values[index] = new_value
                self.controller.on_attribute_change.fire(self.field.name, values, values, self.controller, index)
    
    def add_item(self):
        values = getattr(self.controller, self.field.name, [])
        type_str = field_type_str(self.field)
        type, subtypes = parse_type_str(type_str)
        new_value = type_str_default_value(subtypes[0])
        values = values +[new_value]
        setattr(self.controller, self.field.name, values)

    def remove_item(self):
        values = getattr(self.controller, self.field.name, undefined)
        if values is not undefined and values:
            values = values[:-1]
            setattr(self.controller, self.field.name, values)


class ListIntWidget(ListStrWidget):
    def get_value(self, index):
        try:
            return int(self.inner_widgets[index].text())
        except ValueError:
            return undefined

class ListIntWidgetFactory(ListStrWidgetFactory):
    list_widget_class = ListIntWidget


class ListFloatWidget(ListStrWidget):
    def get_value(self, index):
        try:
            return float(self.inner_widgets[index].text())
        except ValueError:
            return undefined

class ListFloatWidgetFactory(ListStrWidgetFactory):
    list_widget_class = ListFloatWidget
