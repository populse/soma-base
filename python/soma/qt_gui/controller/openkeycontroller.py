from soma.undefined import undefined
from soma.utils.weak_proxy import proxy_method

from ..collapsible import CollapsibleWidget
from . import ControllerSubwidget, ControllerWidgetFactory


class OpenKeyControllerWidgetFactory(ControllerWidgetFactory):
    def create_widgets(self):
        controller = self.parent_interaction.get_value()
        if controller is undefined:
            controller = self.parent_interaction.field.type()
        self.inner_widget = ControllerSubwidget(
            controller, readonly=self.readonly, depth=self.controller_widget.depth + 1
        )
        label = self.parent_interaction.get_label()
        if not self.readonly:
            buttons = ["+"]
        else:
            buttons = []
        self.widget = CollapsibleWidget(
            self.inner_widget,
            label=label,
            expanded=(self.parent_interaction.depth == 0),
            buttons_label=buttons,
            parent=self.controller_widget,
        )
        self.widget.setToolTip(self.parent_interaction.get_doc())
        self.inner_widget.setContentsMargins(
            self.widget.toggle_button.sizeHint().height(), 0, 0, 0
        )

        if not self.readonly:
            self.widget.buttons[0].clicked.connect(
                proxy_method(self, "inner_widget.add_item")
            )

        self.controller_widget.add_widget_row(
            self.widget, label_index=0, field_name=self.parent_interaction.field.name
        )
        self.parent_interaction.on_change_add(proxy_method(self, "update_gui"))

    def set_visible(self, on):
        self.widget.setVisible(on)
