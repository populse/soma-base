# -*- coding: utf-8 -*-

from . import ControllerWidgetFactory, ControllerSubwidget
from ..collapsable import CollapsableWidget
from soma.undefined import undefined
from soma.qt_gui.qt_backend import Qt
from functools import partial


class EngineConfigurationWidgetFactory(ControllerWidgetFactory):
    def create_widgets(self):
        controller = self.parent_interaction.get_value()
        if controller is undefined:
            controller = self.parent_interaction.field.type()
        self.inner_widget = ControllerSubwidget(
            controller, readonly=self.readonly,
            depth=self.controller_widget.depth + 1)
        label = self.parent_interaction.get_label()
        if not self.readonly:
            buttons = ['+']
        else:
            buttons = []
        self.widget = CollapsableWidget(
            self.inner_widget, label=label,
            expanded=(self.parent_interaction.depth==0),
            buttons_label=buttons,
            parent=self.controller_widget)
        self.inner_widget.setContentsMargins(
            self.widget.toggle_button.sizeHint().height(),0,0,0)

        if not self.readonly:
            button = self.widget.buttons[0]
            button.setPopupMode(button.InstantPopup)
            menu = Qt.QMenu()
            custom = menu.addAction('add custom module')
            custom.triggered.connect(self.add_custom_module)
            available_modules = ['spm', 'fsl']
            for module in available_modules:
                action = menu.addAction(module)
                action.triggered.connect(partial(self.add_module, module))
            button.setMenu(menu)

        self.controller_widget.add_widget_row(
            self.widget, label_index=0,
            field_name=self.parent_interaction.field.name)
        self.parent_interaction.on_change_add(self.update_gui)

    def add_module(self, module):
        controller = self.parent_interaction.get_value()
        controller.add_module(module)

    def add_custom_module(self):
        module = self.inner_widget.ask_new_key_name()
        if module:
            controller = self.parent_interaction.get_value()
            controller.add_module(module)
