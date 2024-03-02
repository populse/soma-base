from soma.controller.field import parse_type_str, subtypes, type_str
from soma.qt_gui.qt_backend import Qt
from soma.utils.weak_proxy import proxy_method

from ..collapsible import CollapsibleWidget


class DictWidgetFactory(WidgetFactory):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.allow_update_gui = True
        self.factories = {}
        self._rowcount = 0

    def create_widgets(self):
        label = self.parent_interaction.get_label()
        self.inner_widget = Qt.QWidget()
        layout = Qt.QGridLayout()
        self.inner_widget.setLayout(layout)

        self.widget = CollapsibleWidget(
            self.inner_widget,
            label=label,
            expanded=(self.parent_interaction.depth == 0),
            parent=self.controller_widget,
        )
        self.inner_widget.setContentsMargins(
            self.widget.toggle_button.sizeHint().height(), 0, 0, 0
        )

        self.controller_widget.add_widget_row(
            self.widget, label_index=0, field_name=self.parent_interaction.field.name
        )

        self.parent_interaction.on_change_add(proxy_method(self, "update_gui"))
        self.update_gui()

    def delete_widgets(self):
        self.parent_interaction.on_change_remove(proxy_method(self, "update_gui"))
        layout = self.inner_widget.layout()
        for i in range(len(self.factories)):
            row = self._rowcount - 1
            for column in range(self.content_layout.columnCount()):
                item = layout.itemAtPosition(row, column)
                self.content_layout.removeItem(item)
                if item is not None and item.widget() is not None:
                    item.widget().deleteLater()
        # self.inner_widget.clear()
        # self.inner_widget.disconnect()
        # self.inner_widget.deleteLater()
        self._rowcount = 0
        self.facrtories = {}

    def update_gui(self):
        if self.allow_update_gui:
            self.allow_update_gui = False
            self.delete_widgets()
            self.factories = {}
            values = self.parent_interaction.get_value(default={})
            for key, value in values.items():
                type_id = type(value)
                factory_type = self.find_factory(type_id, default=None)
                factory = factory_type(
                    controller_widget=self.widget,
                    parent_interaction=DictFieldInteraction(
                        self.parent_interaction, key, self.controller_widget.depth
                    ),
                    readonly=self.readonly,
                )
                self.factories[key] = factory
                factory.create_widgets()
                self._rowcount += 1

            self.allow_update_gui = True

    def set_visible(self, on):
        self.widget.setVisible(on)


class DictFieldInteraction:
    def __init__(self, parent_interaction, key, depth):
        self.parent_interaction = parent_interaction
        self.key = key
        self.type = subtypes(self.parent_interaction.type)[0]
        _, subtypes_str = parse_type_str(type_str(self.type))
        self.key_type = subtypes_str[0]
        self.type_str = subtypes_str[1]
        self.depth = depth

    # @property
    # def is_output(self):
    # return self.parent_interaction.is_output

    # def get_value(self, default=undefined):
    # values = self.parent_interaction.get_value()
    # if values is not undefined:
    # return values.get(self.key, default)
    # return default

    # def set_value(self, value):
    # self.parent_interaction.get_value()[self.key] = value
    # self.parent_interaction.inner_value_changed([self.key])

    # def set_inner_value(self, value, key):
    # all_values = self.get_value()
    # container = type(all_values)
    # if issubclass(container, dict):
    # old_value = all_values[key]
    # else:
    # old_value = dict(all_values)[key]
    # if old_value != value:
    # if issubclass(container, dict):
    # all_values[key] = value
    # else:
    # new_values = dict(all_values)
    # new_values[key] = value
    # all_values.clear()
    # all_values.update(new_values)
    # self.parent_interaction.inner_value_changed([self.key, key])

    # def get_label(self):
    # return f'{self.parent_interaction.get_label()}[{self.key}]'

    # def on_change_add(self, callback):
    # pass

    # def on_change_remove(self, callback):
    # pass

    # def set_protected(self, protected):
    # pass

    # def is_optional(self):
    # return False

    # def inner_value_changed(self, keys):
    # self.parent_interaction.inner_value_changed([self.key] + keys)
