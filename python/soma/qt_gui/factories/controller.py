# -*- coding: utf-8 -*-

from functools import partial

from pydantic import ValidationError

from . import (
    WidgetFactory,
    WidgetsGrid,
    DefaultWidgetFactory,
    GroupWidget,
    ControllerFieldInteraction,
    ScrollableWidgetsGrid,
)
from ..collapsable import CollapsableWidget
from soma.undefined import undefined
from soma.controller import field_type, field_type_str

class BaseControllerWidget:
    def __init__(self, controller, output=False, user_level=None, depth=0, *args, **kwargs):
        super().__init__(depth=depth, *args, **kwargs)
        self.depth = depth
        # Select and sort fields
        fields = []
        for field in controller.fields():
            if (
                (output or not controller.metadata(field, 'output', False))
                and (user_level is None or user_level >= controller.metadata(field, 'user_level', 0))
            ):
                fields.append(field)
        self.fields = sorted(fields, key=lambda f: f.metadata.get('order'))
        self.groups = {
            None: self,
        }
        self.factories = {}
        for field in self.fields:
            group = controller.metadata(field, 'group', None)
            group_content_widget = self.groups.get(group)
            if group_content_widget is None:
                group_content_widget = WidgetsGrid(depth=self.depth)
                self.group_widget = GroupWidget(group)
                
                self.group_widget.layout().addWidget(group_content_widget)
                self.add_widget_row(self.group_widget)
                self.groups[group] = group_content_widget

            type_str = field_type_str(field)
            factory_type = WidgetFactory.find_factory(type_str, DefaultWidgetFactory)
            factory = factory_type(controller_widget=group_content_widget, 
                                   parent_interaction=ControllerFieldInteraction(controller, field, self.depth))
            self.factories[field] = factory
            factory.create_widgets()


class ControllerWidget(BaseControllerWidget, ScrollableWidgetsGrid):
    pass

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
