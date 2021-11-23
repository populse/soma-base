# -*- coding: utf-8 -*-

from functools import partial

from pydantic import ValidationError

from . import WidgetFactory
from ..controller_widget import BaseControllerWidget, WidgetsGrid
from ..collapsable import CollapsableWidget
from soma.undefined import undefined
from soma.controller import field_type

class ControllerSubwidget(BaseControllerWidget, WidgetsGrid):
    pass

class ControllerWidgetFactory(WidgetFactory):
    def create_widgets(self):
        controller = self.parent_interaction.get_value()
        if controller is undefined:
            controller = field_type(self.parent_interaction.field)()
        self.inner_widget = ControllerSubwidget(controller, depth=self.controller_widget.depth + 1)
        label = self.parent_interaction.get_label()
        self.widget = CollapsableWidget(self.inner_widget, label=label, expanded=(self.parent_interaction.depth==0), 
                                        parent=self.controller_widget)
        self.inner_widget.setContentsMargins(self.widget.toggle_button.sizeHint().height(),0,0,0)
      
        self.controller_widget.add_widget_row(self.widget)

    def delete_widgets(self):
        self.controller_widget.remove_widget_row()
        self.widget.deleteLater()
        self.inner_widget.deleteLater()
