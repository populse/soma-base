# -*- coding: utf-8 -*-

from pydantic import ValidationError

from soma.qt_gui.qt_backend import Qt
from . import WidgetFactory
from soma.qt_gui.timered_widgets import TimeredQLineEdit
from soma.undefined import undefined


class BoolWidgetFactory(WidgetFactory):
    def create_widgets(self):
        label = self.parent_interaction.get_label()
        self.label_widget = Qt.QLabel(label, parent=self.controller_widget)
        self.widget = Qt.QCheckBox(parent=self.controller_widget)
        self.widget.setSizePolicy(Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Fixed)

        self.parent_interaction.on_change_add(self.update_gui)
        self.update_gui()

        self.widget.stateChanged.connect(self.update_controller)

        self.controller_widget.add_widget_row(self.label_widget, self.widget)

    def delete_widgets(self):
        self.controller_widget.remove_widget_row()
        self.widget.stateChanged.disconnect(self.update_controller)
        self.parent_interaction.on_change_remove(self.update_gui)
        self.widget.deleteLater()
        self.label_widget.deleteLater()

    def update_gui(self):
        value = self.parent_interaction.get_value()
        if value is undefined:
            if self.parent_interaction.is_optional():
                self.widget.setStyleSheet(self.warning_style_sheet)
            else:
                self.widget.setStyleSheet(self.invalid_style_sheet)
        else:
            self.widget.setStyleSheet(self.valid_style_sheet)
            self.widget.setChecked(value)

    def update_controller(self):
        try:
            self.parent_interaction.set_value(self.widget.isChecked())
        except ValidationError:
            self.widget.setStyleSheet(self.invalid_style_sheet)
        else:
            self.parent_interaction.set_protected(False)
            self.widget.setStyleSheet(self.valid_style_sheet)
