# -*- coding: utf-8 -*-

from functools import partial

from pydantic import ValidationError

from ..qt_backend import Qt
from . import WidgetFactory, ListItemInteraction
from ..controller_widget import WidgetsGrid
from ..collapsable import CollapsableWidget
from ..timered_widgets import TimeredQLineEdit
from soma.undefined import undefined
from soma.controller import (parse_type_str,
                             type_str_default_value)


class ListStrWidgetFactory(WidgetFactory):
    ROW_SIZE = 10

    def create_widgets(self):
        label = self.parent_interaction.get_label()
        self.grid_widget = Qt.QWidget()
        self.layout = Qt.QGridLayout(self.grid_widget)
        self.inner_widgets = []
        self.widget = CollapsableWidget(self.grid_widget, label=label, expanded=True, 
            buttons_label=['+', '-'], parent=self.controller_widget)
        self.grid_widget.setContentsMargins(self.widget.toggle_button.sizeHint().height(),0,0,0)

        self.update_gui()
        self.parent_interaction.on_change_add(self.update_gui)

        self.widget.buttons[0].clicked.connect(self.add_item)
        self.widget.buttons[1].clicked.connect(self.remove_item)
        
        self.controller_widget.add_widget_row(self.widget)

    def delete_widgets(self):
        self.controller_widget.remove_widget_row()
        self.widget.buttons[0].clicked.disconnect(self.add_item)
        self.widget.buttons[1].clicked.disconnect(self.remove_item)
        self.parent_interaction.on_change_remove(self.update_gui)
        self.widget.deleteLater()
        for w in self.inner_widgets:
            self.inner_widgets.deleteLater()
        self.grid_widget.deleteLater()

    def update_gui(self):
        values = self.parent_interaction.get_value(default=[])
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
            widget.userModification.connect(partial(self.update_controller_item, pos))
        # Set values
        for index, value in enumerate(values):
            self.set_value(value, index)

    def update_controller(self):
        try:
            values = [self.get_value(i) for i in range(len(self.inner_widgets))]
            self.parent_interaction.set_value(values)
        except ValidationError:
            pass
        else:
            self.parent_interaction.set_protected(False)

    def set_value(self, value, index):
        widget = self.inner_widgets[index]
        if value is undefined:
            widget.setStyleSheet(WidgetFactory.invalid_style_sheet)
        else:
            widget.setStyleSheet(WidgetFactory.valid_style_sheet)
            widget.setText(f'{value}')

    def get_value(self, index):
        return self.inner_widgets[index].text()

    def update_controller_item(self, index):
        values = self.parent_interaction.get_value()
        if values is not undefined:
            new_value = self.get_value(index)
            if new_value is undefined:
                self.inner_widgets[index].setStyleSheet(self.invalid_style_sheet)
            else:
                self.inner_widgets[index].setStyleSheet(self.valid_style_sheet)
            old_value = values[index]
            if new_value != old_value:
                values[index] = new_value
                self.parent_interaction.inner_item_changed(index)
    
    def add_item(self):
        values = self.parent_interaction.get_value(default=[])
        type_str = self.parent_interaction.type_str()
        type, subtypes = parse_type_str(type_str)
        new_value = type_str_default_value(subtypes[0])
        values = values + [new_value]
        self.parent_interaction.set_value(values)
        self.update_gui()

    def remove_item(self):
        values = self.parent_interaction.get_value()
        if values is not undefined and values:
            values = values[:-1]
            self.parent_interaction.set_value(values)
            self.update_gui()



class ListIntWidgetFactory(ListStrWidgetFactory):
    def get_value(self, index):
        try:
            return int(self.inner_widgets[index].text())
        except ValueError:
            return undefined


class ListFloatWidgetFactory(ListStrWidgetFactory):
    def get_value(self, index):
        try:
            return float(self.inner_widgets[index].text())
        except ValueError:
            return undefined


def find_generic_list_factory(type, subtypes):
    if subtypes:
        item_type = subtypes[0]
        widget_factory = WidgetFactory.find_factory(item_type, default=None)
        if widget_factory is not None:
            return partial(ListAnyWidgetFactory, item_factory_class=widget_factory)
    return None
    


class ListAnyWidgetFactory(WidgetFactory):
    def __init__(self, item_factory_class, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.item_factory_class = item_factory_class

    def create_widgets(self):
        self.items_widget = WidgetsGrid()
        label = self.parent_interaction.get_label()
        self.widget = CollapsableWidget(self.items_widget, label=label, expanded=True, 
            buttons_label=['+', '-'], parent=self.controller_widget)
        self.items_widget.setContentsMargins(self.widget.toggle_button.sizeHint().height(),0,0,0)
        self.item_factories = []

        self.update_gui()
        self.parent_interaction.on_change_add(self.update_gui)

        self.widget.buttons[0].clicked.connect(self.add_item)
        self.widget.buttons[1].clicked.connect(self.remove_item)
        
        self.controller_widget.add_widget_row(self.widget)

    def delete_widgets(self):
        self.controller_widget.remove_widget_row()
        self.widget.buttons[0].clicked.disconnect(self.add_item)
        self.widget.buttons[1].clicked.disconnect(self.remove_item)
        self.parent_interaction.on_change_remove(self.update_gui)
        self.widget.deleteLater()
        self.items_widget.deleteLater()
        

    def update_gui(self):
        values = self.parent_interaction.get_value(default=[])
        # Remove item widgets if new list is shorter than current one
        while len(values) < len(self.item_factories):
            item_factory = self.item_factories.pop(-1)
            item_factory.delete_widgets()

        # Add item widgets if new list is longer than current one
        while len(values) > len(self.item_factories):
            index = len(self.item_factories)
            item_factory = self.item_factory_class(self.items_widget, 
                ListItemInteraction(self.parent_interaction, index))
            self.item_factories.append(item_factory)
            item_factory.create_widgets()


    def add_item(self):
        values = self.parent_interaction.get_value(default=[])
        type_str = self.parent_interaction.type_str()
        type, subtypes = parse_type_str(type_str)
        new_value = type_str_default_value(subtypes[0])
        values = values + [new_value]
        self.parent_interaction.set_value(values)
        self.update_gui()

    def remove_item(self):
        values = self.parent_interaction.get_value()
        if values is not undefined and values:
            values = values[:-1]
            self.parent_interaction.set_value(values)
            self.update_gui()
