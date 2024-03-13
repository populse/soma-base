from functools import partial

try:
    from pydantic.v1 import ValidationError
except ImportError:
    from pydantic import ValidationError

from soma.undefined import undefined
from soma.utils.weak_proxy import proxy_method

from ...controller import WidgetFactory, subtypes, type_default_value


class ListStrWidgetFactory(WidgetFactory):
    ROW_SIZE = 10
    convert_from_list = staticmethod(lambda x: x)
    convert_to_list = staticmethod(lambda x: x if x not in (None, undefined) else [])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.allow_update_gui = True

    def create_widgets(self):
        label = self.parent_interaction.get_label()
        self.grid_widget = Qt.QWidget()
        self.layout = Qt.QGridLayout(self.grid_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.inner_widgets = []
        self.widget = CollapsibleWidget(
            self.grid_widget,
            label=label,
            expanded=(self.parent_interaction.depth == 0),
            buttons_label=["+", "-"],
            parent=self.controller_widget,
        )
        self.grid_widget.setContentsMargins(
            self.widget.toggle_button.sizeHint().height(), 0, 0, 0
        )

        self.update_gui()
        self.parent_interaction.on_change_add(proxy_method(self, "update_gui"))

        self.widget.buttons[0].clicked.connect(proxy_method(self, "add_item"))
        self.widget.buttons[1].clicked.connect(proxy_method(self, "remove_item"))

        self.controller_widget.add_widget_row(self.widget)

    def delete_widgets(self):
        self.controller_widget.remove_widget_row()
        self.widget.buttons[0].clicked.disconnect(proxy_method(self, "add_item"))
        self.widget.buttons[1].clicked.disconnect(proxy_method(self, "remove_item"))
        self.parent_interaction.on_change_remove(proxy_method(self, "update_gui"))
        self.widget.deleteLater()
        for w in self.inner_widgets:
            w.deleteLater()
        self.grid_widget.deleteLater()

    def update_gui(self):
        if self.allow_update_gui:
            self.allow_update_gui = False
            values = self.parent_interaction.get_value(default=[])
            values = self.convert_to_list(values)
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
                widget.userModification.connect(partial(self.inner_widget_changed, pos))
            # Set values without sending modification signal
            for widget in self.inner_widgets:
                widget.startInternalModification()
            for index, value in enumerate(values):
                self.set_value(value, index)
            for widget in self.inner_widgets:
                widget.stopInternalModification()
            self.allow_update_gui = True

    def inner_widget_changed(self, index):
        new_value = self.get_value(index)
        self.parent_interaction.set_inner_value(new_value, index)
        self.update_inner_gui([index])

    def update_inner_gui(self, indices):
        if self.allow_update_gui:
            self.allow_update_gui = False
            index = indices[0]
            self.set_value(
                self.convert_to_list(self.parent_interaction.get_value())[index], index
            )
            self.allow_update_gui = True

    def update_controller(self):
        try:
            values = [self.get_value(i) for i in range(len(self.inner_widgets))]
            self.parent_interaction.set_value(self.convert_from_list(values))
        except ValidationError:
            pass
        else:
            self.parent_interaction.set_protected(False)

    def set_value(self, value, index):
        try:
            widget = self.inner_widgets[index]
        except IndexError:
            return
        if value is undefined:
            widget.setStyleSheet(WidgetFactory.invalid_style_sheet)
        else:
            widget.setStyleSheet(WidgetFactory.valid_style_sheet)
            current_text = widget.text()
            new_text = f"{value}"
            if new_text != current_text:
                widget.startInternalModification()
                widget.setText(new_text)
                widget.stopInternalModification()

    def get_value(self, index):
        try:
            return self.inner_widgets[index].text()
        except IndexError:
            return undefined

    # def update_controller_item(self, index):
    #     values = self.parent_interaction.get_value()
    #     if values is not undefined:
    #         values = self.convert_to_list(values)
    #         new_value = self.get_value(index)
    #         if new_value is undefined:
    #             self.inner_widgets[index].setStyleSheet(self.invalid_style_sheet)
    #         else:
    #             self.inner_widgets[index].setStyleSheet(self.valid_style_sheet)
    #         old_value = values[index]
    #         if new_value != old_value:
    #             values[index] = new_value

    def add_item(self):
        values = self.convert_to_list(self.parent_interaction.get_value(default=[]))
        item_type = subtypes(self.parent_interaction.type)[0]
        new_value = type_default_value(item_type)
        values = values + [new_value]
        self.parent_interaction.set_value(self.convert_from_list(values))
        self.update_gui()

    def remove_item(self):
        values = self.convert_to_list(self.parent_interaction.get_value())
        if values is not undefined and values:
            values = values[:-1]
            self.parent_interaction.set_value(self.convert_from_list(values))
            self.update_gui()

    def expanded_items(self):
        return self.widget.toggle_button.isChecked()

    def set_expanded_items(self, exp_values, silent=False):
        self.widget.toggle_expand(bool(exp_values))

    def set_visible(self, on):
        self.widget.setVisible(on)


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
        widget_factory = WidgetFactory.find_factory(
            item_type, default=DefaultWidgetFactory
        )
        if widget_factory is not None:
            return partial(ListAnyWidgetFactory, item_factory_class=widget_factory)
    return None


class ListAnyWidgetFactory(WidgetFactory):
    convert_from_list = staticmethod(lambda x: x)
    convert_to_list = staticmethod(lambda x: x if x not in (None, undefined) else [])

    def __init__(self, item_factory_class, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.item_factory_class = item_factory_class
        self.allow_update_gui = True

    def create_widgets(self):
        self.items_widget = WidgetsGrid(self.parent_interaction.depth)
        label = self.parent_interaction.get_label()
        self.widget = CollapsibleWidget(
            self.items_widget,
            label=label,
            expanded=(self.items_widget.depth == 0),
            buttons_label=["+", "-"],
            parent=self.controller_widget,
        )
        self.widget.setContentsMargins(0, 0, 0, 0)
        self.widget.setToolTip(self.parent_interaction.get_doc())
        self.items_widget.setContentsMargins(
            self.widget.toggle_button.sizeHint().height(), 0, 0, 0
        )
        self.item_factories = []

        self.update_gui()
        self.parent_interaction.on_change_add(proxy_method(self, "update_gui"))

        self.widget.buttons[0].clicked.connect(proxy_method(self, "add_item"))
        self.widget.buttons[1].clicked.connect(proxy_method(self, "remove_item"))

        self.controller_widget.add_widget_row(self.widget)

    def delete_widgets(self):
        self.controller_widget.remove_widget_row()
        self.widget.buttons[0].clicked.disconnect(proxy_method(self, "add_item"))
        self.widget.buttons[1].clicked.disconnect(proxy_method(self, "remove_item"))
        self.parent_interaction.on_change_remove(proxy_method(self, "update_gui"))
        self.widget.deleteLater()
        self.items_widget.deleteLater()

    def update_gui(self):
        if self.allow_update_gui:
            self.allow_update_gui = False
            values = self.convert_to_list(self.parent_interaction.get_value(default=[]))
            # Remove item widgets if new list is shorter than current one
            while len(values) < len(self.item_factories):
                item_factory = self.item_factories.pop(-1)
                item_factory.delete_widgets()

            # Add item widgets if new list is longer than current one
            while len(values) > len(self.item_factories):
                index = len(self.item_factories)
                item_factory = self.item_factory_class(
                    controller_widget=self.items_widget,
                    parent_interaction=ListItemInteraction(
                        self.parent_interaction, index=index
                    ),
                )
                self.item_factories.append(item_factory)
                item_factory.create_widgets()
            self.allow_update_gui = True

    def update_inner_gui(self, indices):
        if self.allow_update_gui:
            self.allow_update_gui = False
            index = indices[0]
            factory = self.item_factories[index]
            indices = indices[1:]
            if indices:
                factory.update_inner_gui(indices)
            else:
                factory.update_gui()
            self.allow_update_gui = True

    def add_item(self):
        values = self.convert_to_list(self.parent_interaction.get_value(default=[]))
        item_type = subtypes(self.parent_interaction.type)[0]
        new_value = type_default_value(item_type)
        values = values + [new_value]
        self.parent_interaction.set_value(self.convert_from_list(values))
        self.update_gui()

    def remove_item(self):
        values = self.convert_to_list(self.parent_interaction.get_value())
        if values is not undefined and values:
            values = values[:-1]
            self.parent_interaction.set_value(self.convert_from_list(values))
            self.update_gui()

    def expanded_items(self):
        return self.widget.toggle_button.isChecked()

    def set_expanded_items(self, exp_values, silent=False):
        self.widget.toggle_expand(bool(exp_values))

    def set_visible(self, on):
        self.widget.setVisible(on)
