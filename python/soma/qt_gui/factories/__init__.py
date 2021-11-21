# -*- coding: utf-8 -*-

from soma.controller.field import field_type_str
from soma.qt_gui.qt_backend import Qt
from soma.undefined import undefined

class WidgetFactory:
    valid_style_sheet = ''
    warning_style_sheet = 'background: #FFFFC8;'
    invalid_style_sheet = 'background: #FFDCDC;'
    
    def __init__(self, controller_widget, controller, field, subtypes):
        super().__init__()
        self.controller_widget = controller_widget
        self. controller = controller
        self.field = field
        self.subtypes = subtypes

    def create_widgets(self):
        label = self.controller.metadata(self.field.name, 'label', self.field.name)
        self.label_widget = Qt.QLabel(label, parent=self.controller_widget)
        self.text_widget = Qt.QLineEdit(parent=self.controller_widget)
        self.text_widget.setStyleSheet('color: red;')
        self.text_widget.setReadOnly(True)
        self.text_widget.setToolTip(f'No graphical editor found for type {field_type_str(self.field)}')

        self.controller.on_attribute_change.add(self.update_gui, self.field.name)
        self.update_gui(getattr(self.controller, self.field.name, undefined))

        self.controller_widget.add_widget_row(self.label_widget, self.text_widget)

    def update_gui(self, value):
        self.text_widget.setText(f'{value}')

