# -*- coding: utf-8 -*-

from pydantic import ValidationError

from soma.qt_gui.qt_backend import Qt
from soma.qt_gui.factories import WidgetFactory
from soma.qt_gui.timered_widgets import TimeredQLineEdit
from soma.undefined import undefined

class StrWidgetFactory(WidgetFactory):
    def create_widgets(self):
        label = self.controller.metadata(self.field.name, 'label', self.field.name)
        self.label_widget = Qt.QLabel(label, parent=self.controller_widget)
        self.text_widget = TimeredQLineEdit(parent=self.controller_widget)

        self.controller.on_attribute_change.add(self.update_gui, self.field.name)
        self.update_gui(getattr(self.controller, self.field.name, undefined))

        self.text_widget.userModification.connect(self.update_controller)

        return self.label_widget, self.text_widget

    def update_gui(self, value):
        if value is undefined:
            self.text_widget.setText('')
            if self.controller.is_optional(self.field):
                self.text_widget.setStyleSheet(self.warning_style_sheet)
            else:
                self.text_widget.setStyleSheet(self.invalid_style_sheet)
        else:
            self.text_widget.setStyleSheet(self.valid_style_sheet)
            self.text_widget.setText(f'{value}')

    def update_controller(self):
        try:
            setattr(self.controller, self.field.name, self.text_widget.text())
        except ValidationError:
            self.text_widget.setStyleSheet(self.invalid_style_sheet)
        else:
            self.controller.set_metadata(self.field, 'protected', False)
            self.text_widget.setStyleSheet(self.valid_style_sheet)
