# -*- coding: utf-8 -*-

from . import ControllerWidgetFactory, ControllerSubwidget
from ..collapsable import CollapsableWidget
from soma.undefined import undefined
from ...controller import subtypes, type_default_value
from soma.qt_gui.qt_backend import Qt


class OpenKeyControllerWidgetFactory(ControllerWidgetFactory):
    def create_widgets(self):
        controller = self.parent_interaction.get_value()
        if controller is undefined:
            controller = self.parent_interaction.field.type()
        self.inner_widget = ControllerSubwidget(controller, depth=self.controller_widget.depth + 1)
        label = self.parent_interaction.get_label()
        self.widget = CollapsableWidget(
            self.inner_widget, label=label,
            expanded=(self.parent_interaction.depth==0),
            buttons_label=['+', '-'],
            parent=self.controller_widget)
        self.inner_widget.setContentsMargins(
            self.widget.toggle_button.sizeHint().height(),0,0,0)

        self.widget.buttons[0].clicked.connect(self.add_item)
        self.widget.buttons[1].clicked.connect(self.remove_item)

        self.controller_widget.add_widget_row(self.widget)

    def ask_new_key_name(self):
        dialog = Qt.QDialog()
        layout = Qt.QVBoxLayout()
        dialog.setLayout(layout)

        layout.addWidget(Qt.QLabel('field:'))
        le = Qt.QLineEdit()
        layout.addWidget(le)

        blay = Qt.QHBoxLayout()
        layout.addLayout(blay)
        ok = Qt.QPushButton('OK')
        blay.addWidget(ok)
        cancel = Qt.QPushButton('Cancel')
        blay.addWidget(cancel)
        ok.clicked.connect(dialog.accept)
        cancel.clicked.connect(dialog.reject)
        ok.setDefault(True)

        res = dialog.exec_()
        if res == Qt.QDialog.Accepted:
            print('ok')
            name = le.text()
            if name == '' or '.' in name or '/' in name or '-' in name \
                    or ' ' in name or name[0] in '0123456789':
                print('invalid name', name)
                return None
            if self.parent_interaction.get_value().field(name) is not None:
                print('field', name, 'already exists.')
                return None
            return name
        return None

    def ask_existing_key_name(self):
        dialog = Qt.QDialog()
        layout = Qt.QVBoxLayout()
        dialog.setLayout(layout)

        layout.addWidget(Qt.QLabel('field:'))
        le = Qt.QLineEdit()
        layout.addWidget(le)

        blay = Qt.QHBoxLayout()
        layout.addLayout(blay)
        ok = Qt.QPushButton('OK')
        blay.addWidget(ok)
        cancel = Qt.QPushButton('Cancel')
        blay.addWidget(cancel)
        ok.clicked.connect(dialog.accept)
        cancel.clicked.connect(dialog.reject)
        ok.setDefault(True)

        res = dialog.exec_()
        if res == Qt.QDialog.Accepted:
            print('ok')
            name = le.text()
            if self.parent_interaction.get_value().field(name) is None:
                print('field', name, 'does not exist.')
                return None
            return name
        return None

    def add_item(self):
        new_key = self.ask_new_key_name()
        if not new_key:
            return
        controller = self.parent_interaction.get_value()
        item_type = controller._value_type
        new_value = type_default_value(item_type)
        setattr(controller, new_key, new_value)
        print('new value:', controller)
        #self.parent_interaction.set_value(controller)

    def remove_item(self):
        key = self.ask_existing_key_name()
        if not key:
            return
        value = self.parent_interaction.get_value()
        if value is not undefined and value:
            delattr(value, key)
            #self.parent_interaction.set_value(value)
