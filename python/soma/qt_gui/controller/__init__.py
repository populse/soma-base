import html
import weakref
from functools import partial

from soma.controller import OpenKeyController, parse_type_str, type_default_value
from soma.controller.field import subtypes, type_str
from soma.qt_gui.qt_backend import Qt, QtCore
from soma.undefined import undefined
from soma.utils.weak_proxy import get_ref, proxy_method

from ..collapsible import CollapsibleWidget


class EditableLabel(Qt.QWidget):
    def __init__(self, label):
        super().__init__()
        layout = Qt.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.label = label
        layout.addWidget(label)
        self.buttons = Qt.QWidget()
        blayout = Qt.QHBoxLayout()
        blayout.setContentsMargins(0, 0, 0, 0)
        blayout.setSpacing(0)
        self.buttons.setLayout(blayout)
        edit = Qt.QToolButton(self.buttons)
        edit.setText("✎")
        blayout.addWidget(edit)
        delete = Qt.QToolButton(self.buttons)
        delete.setText("✖")
        blayout.addWidget(delete)
        hide = Qt.QToolButton(self.buttons)
        hide.setText("↸")
        blayout.addWidget(hide)
        sz = self.label.sizeHint()
        sh = self.buttons.minimumSizeHint()
        mw = sz.width()
        mh = sz.height()
        bw = sh.width()
        bh = sh.height()
        bw = min(bw, 30)  # arbitrary max width
        mw = max(mw, bw)
        bh = min(mh, bh)
        if mw != sz.width():
            self.label.setMinimumWidth(mw)

        # self.buttons.setGeometry(mw - bw, 0, bw, bh)
        self.buttons.setGeometry(0, 0, bw, bh)
        self.buttons.setParent(self)
        self.buttons.hide()

        self.edit_button = edit
        self.del_button = delete
        self.hide_button = hide

        self.hide_button.clicked.connect(self.buttons.hide)

        # self.setFixedSize(mw, mh)

    def enterEvent(self, event):
        self.buttons.show()
        event.accept()

    def leaveEvent(self, event):
        self.buttons.hide()
        event.accept()

    # def resizeEvent(self, event):
    # sz = self.label.size()
    # sh = self.buttons.size()
    ##self.buttons.setGeometry(sz.width() - sh.width(), 0,
    ##sh.width(), sh.height())
    # self.buttons.setGeometry(0, 0,
    # sh.width(), sh.height())
    # super().resizeEvent(event)


class ScrollableWidgetsGrid(Qt.QScrollArea):
    """
    A widget that is used for Controller main windows (i.e.
    top level widget).
    It has a 2 columns grid layout aligned ont the top of the
    window. It allows to add many inner_widgets rows. Each
    row contains either 1 or 2 widgets. A single widget uses
    the two columns of the row.
    """

    def __init__(self, depth=0, *args, **kwargs):
        self.depth = depth
        super().__init__(*args, **kwargs)
        self.content_widget = Qt.QWidget(self)
        hlayout = Qt.QVBoxLayout()
        self.content_layout = Qt.QGridLayout()
        hlayout.addLayout(self.content_layout)
        hlayout.addStretch(1)
        self.content_widget.setLayout(hlayout)
        self.setWidget(self.content_widget)
        self.setWidgetResizable(True)
        # QGridLayout.rowCount() is never decreasing, apparently: we need to
        self._rowcount = 0

    def add_widget_row(
        self, first_widget, second_widget=None, label_index=None, field_name=None
    ):
        """
        Add one or two widgets in a row

        If the widget is not in read-only mode, and if it is marked as
        editable, one of the widgets can be considered to be the label, and
        will get edit/close buttons.

        If label_index is not None, then it tells which of the widgets is the
        "label" widget. If negative, then no widget will be the label. If None
        (the default) and two widgets are passed, then the first one is the
        label.

        If a label widget is considered, then the associated field name (for
        callbacks) is given by the field_name parameter. If not given, then the
        label widget is supposed to be a QLabel and its text() will be used as
        field name.

        If such a label with buttons is created, it is returned by the
        function.
        """
        # row = self.content_layout.rowCount()
        row = self._rowcount
        result = None

        if label_index is None and second_widget is not None:
            label_index = 0
        label_widget = None
        if label_index == 0:
            label_widget = first_widget
        elif label_widget == 1 and second_widget is not None:
            label_widget = second_widget

        if (
            label_widget
            and not getattr(self, "readonly", False)
            and getattr(self, "editable", False)
        ):
            label = EditableLabel(label_widget)
            if field_name is None:
                if hasattr(label_widget, "text"):
                    field_name = label_widget.text()
                else:
                    print("no text in first widget")
                    field_name = None
            label.edit_button.clicked.connect(
                partial(proxy_method(self.edit_field_name), field_name)
            )
            label.del_button.clicked.connect(
                partial(proxy_method(self.remove_field), field_name)
            )
            result = label
        else:
            label = first_widget

        if second_widget is None:
            self.content_layout.addWidget(label, row, 0, 1, 2)
        else:
            self.content_layout.addWidget(label, row, 0, 1, 1)
            self.content_layout.addWidget(second_widget, row, 1, 1, 1)

        self._rowcount += 1
        return result  # return the new label widget if one is created

    def remove_widget_row(self):
        # row = self.content_layout.rowCount()-1
        row = self._rowcount
        for column in range(self.content_layout.columnCount()):
            item = self.content_layout.itemAtPosition(row, column)
            self.content_layout.removeItem(item)
            if item is not None and item.widget() is not None:
                item.widget().deleteLater()
        self._rowcount -= 1


class WidgetsGrid(Qt.QFrame):
    """
    A widget that is used for Controller inside another
    controller widget.
    It has the same properties as VSCrollableWindow but
    not the same layout.
    """

    def __init__(self, depth=0, *args, **kwargs):
        self.depth = depth
        super().__init__(*args, **kwargs)
        self.content_layout = Qt.QGridLayout(self)
        self.content_layout.setContentsMargins(0, 0, 0, 0)

    def add_widget_row(
        self, first_widget, second_widget=None, label_index=None, field_name=None
    ):
        """
        Add one or two widgets in a row

        If the widget is not in read-only mode, and if it is marked as
        editable, one of the widgets can be considered to be the label, and
        will get edit/close buttons.

        If label_index is not None, then it tells which of the widgets is the
        "label" widget. If negative, then no widget will be the label. If None
        (the default) and two widgets are passed, then the first one is the
        label.

        If a label widget is considered, then the associated field name (for
        callbacks) is given by the field_name parameter. If not given, then the
        label widget is supposed to be a QLabel and its text() will be used as
        field name.

        If such a label with buttons is created, it is returned by the
        function.
        """
        row = self.content_layout.rowCount()
        result = None

        if label_index is None and second_widget is not None:
            label_index = 0
        label_widget = None
        if label_index == 0:
            label_widget = first_widget
        elif label_widget == 1 and second_widget is not None:
            label_widget = second_widget

        if (
            label_widget
            and not getattr(self, "readonly", False)
            and getattr(self, "editable", False)
        ):
            label = EditableLabel(label_widget)
            if field_name is None:
                if hasattr(label_widget, "text"):
                    field_name = label_widget.text()
                else:
                    print("no text in first widget")
                    field_name = None
            label.edit_button.clicked.connect(partial(self.edit_field_name, field_name))
            label.del_button.clicked.connect(partial(self.remove_field, field_name))
            result = label
        else:
            label = first_widget

        if second_widget is None:
            self.content_layout.addWidget(label, row, 0, 1, 2)
        else:
            self.content_layout.addWidget(label, row, 0, 1, 1)
            self.content_layout.addWidget(second_widget, row, 1, 1, 1)

        return result  # return the new label widget if one is created

    def remove_widget_row(self):
        row = self.content_layout.rowCount() - 1
        for column in range(self.content_layout.columnCount()):
            item = self.content_layout.itemAtPosition(row, column)
            self.content_layout.removeItem(item)
            if item is not None and item.widget() is not None:
                item.widget().deleteLater()


class GroupWidget(Qt.QFrame):
    def __init__(self, label, expanded=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        Qt.QVBoxLayout(self)
        self.label = label
        self.setFrameStyle(self.StyledPanel | self.Raised)
        self.toggle_button = Qt.QToolButton(self)
        self.toggle_button.setCheckable(True)
        self.toggle_button.setStyleSheet("QToolButton { border: none; }")
        self.toggle_expand(expanded)
        self.toggle_button.resize(self.toggle_button.sizeHint())
        self.toggle_button.move(-2, -2)
        self.setContentsMargins(3, 3, 3, 3)
        self.toggle_button.clicked.connect(self.toggle_expand)
        self.setSizePolicy(Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Expanding)

    def toggle_expand(self, expanded):
        arrow = "▼" if expanded else "▶"
        self.toggle_button.setText(f"{self.label}  {arrow}")
        self.toggle_button.setChecked(expanded)
        for i in range(self.layout().count()):
            widget = self.layout().itemAt(i).widget()
            if widget:
                if expanded:
                    widget.show()
                else:
                    widget.hide()


class WidgetFactory(Qt.QObject):
    valid_style_sheet = ""
    warning_style_sheet = "background: #FFFFC8;"
    invalid_style_sheet = "background: #FFDCDC;"

    inner_item_changed = QtCore.Signal(int)

    def __init__(self, controller_widget, parent_interaction, readonly=False):
        super().__init__()
        self.readonly = readonly
        self._controller_widget = weakref.proxy(controller_widget)
        self.parent_interaction = parent_interaction

    @property
    def controller_widget(self):
        return get_ref(self._controller_widget)

    @classmethod
    def find_factory(cls, type_id, default=None):
        todo = [type_id]
        factory_finder = None
        # find a factory for the type or one of its parent types
        while factory_finder is None and todo:
            type_id = todo.pop(0)
            if isinstance(type_id, str):
                type_s = type_id
            else:
                type_s = type_str(type_id)
            subtypes = []
            factory_finder = cls.widget_factory_types.get(type_s)
            if factory_finder is None:
                type_s, subtypes = parse_type_str(type_s)
                factory_finder = cls.widget_factory_types.get(type_s)
            if factory_finder is None and isinstance(type_id, type):
                todo += list(type_id.__bases__)

        if factory_finder is not None:
            if isinstance(factory_finder, type) and issubclass(
                factory_finder, WidgetFactory
            ):
                return factory_finder
            else:
                factory_class = factory_finder(type_s, subtypes)
                if factory_class is not None:
                    return factory_class
        return default

    def expanded_items(self):
        return False

    def set_expanded_items(self, exp_value, silent=False):
        pass


class ControllerFieldInteraction:
    def __init__(self, controller, field, depth):
        self.controller = controller
        self.field = field
        self.type = field.type
        self.type_str = field.type_str()
        self.depth = depth

    @property
    def is_output(self):
        return self.field.is_output()

    def get_value(self, default=undefined):
        return getattr(self.controller, self.field.name, default)

    def set_value(self, value):
        setattr(self.controller, self.field.name, value)

    def set_inner_value(self, value, index):
        all_values = self.get_value()
        container = type(all_values)
        if container is list:
            old_value = all_values[index]
        else:
            old_value = list(all_values)[index]
        if old_value != value:
            if container is list:
                all_values[index] = value
            else:
                new_values = list(all_values)
                new_values[index] = value
                all_values.clear()
                all_values.update(new_values)
            self.inner_value_changed([index])

    def get_label(self):
        return self.field.metadata("label", self.field.name)

    def on_change_add(self, callback):
        self.controller.on_attribute_change.add(callback, self.field.name)

    def on_change_remove(self, callback):
        self.controller.on_attribute_change.remove(callback, self.field.name)

    def set_protected(self, protected):
        if getattr(self.field, "protected", None) != protected:
            self.field = self.controller.writable_field(self.field.name)
            self.field.protected = protected

    def is_optional(self):
        return self.field.optional

    def inner_value_changed(self, indices):
        self.controller.on_inner_value_change.fire([self.field] + indices)

    def get_doc(self):
        doc = f"<b>type:</b> {str(self.type_str)}"
        field_doc = getattr(self.field, "doc", None)
        if field_doc:
            doc += f"<br/>{html.escape(field_doc)}"
        return doc


class ListItemInteraction:
    def __init__(self, parent_interaction, index):
        self.parent_interaction = parent_interaction
        self.index = index
        self.type = subtypes(self.parent_interaction.type)[0]
        _, subtypes_str = parse_type_str(parent_interaction.type_str)
        self.type_str = subtypes_str[0]
        self.depth = self.parent_interaction.depth + 1

    @property
    def is_output(self):
        return self.parent_interaction.is_output

    def get_value(self, default=undefined):
        values = self.parent_interaction.get_value()
        if values is not undefined:
            return values[self.index]
        return default

    def set_value(self, value):
        self.parent_interaction.get_value()[self.index] = value
        self.parent_interaction.inner_value_changed([self.index])

    def set_inner_value(self, value, index):
        all_values = self.get_value()
        container = type(all_values)
        if container is list:
            old_value = all_values[index]
        else:
            old_value = list(all_values)[index]
        if old_value != value:
            if container is list:
                all_values[index] = value
            else:
                new_values = list(all_values)
                new_values[index] = value
                all_values.clear()
                all_values.update(new_values)
            self.parent_interaction.inner_value_changed([self.index, index])

    def get_label(self):
        return f"{self.parent_interaction.get_label()}[{self.index}]"

    def on_change_add(self, callback):
        pass

    def on_change_remove(self, callback):
        pass

    def set_protected(self, protected):
        pass

    def is_optional(self):
        return False

    def inner_value_changed(self, indices):
        self.parent_interaction.inner_value_changed([self.index] + indices)

    def get_doc(self):
        doc = f"<b>item type:</b> {str(self.type_str)}"
        return doc


class DefaultWidgetFactory(WidgetFactory):
    def create_widgets(self):
        self.text_widget = Qt.QLineEdit(parent=self.controller_widget)
        self.text_widget.setStyleSheet("QLineEdit { color: red; }")
        self.text_widget.setReadOnly(True)
        self.text_widget.setToolTip(
            f"No graphical editor found for type {self.parent_interaction.type_str}"
        )
        if self.readonly:
            self.text_widget.setEnabled(False)

        self.parent_interaction.on_change_add(proxy_method(self.update_gui))
        self.update_gui()

        label = self.parent_interaction.get_label()
        self.label_widget = Qt.QLabel(label, parent=self.controller_widget)
        self.controller_widget.add_widget_row(self.label_widget, self.text_widget)

    def delete_widgets(self):
        self.parent_interaction.on_change_remove(proxy_method(self.update_gui))
        self.controller_widget.remove_widget_row()
        self.label_widget.deleteLater()
        self.text_widget.deleteLater()

    def update_gui(self):
        value = self.parent_interaction.get_value()
        self.text_widget.setText(f"{value}")

    def set_visible(self, on):
        self.text_widget.setVisible(on)
        self.label_widget.setVisible(on)


class BaseControllerWidget:
    def __init__(
        self,
        controller,
        output=None,
        user_level=0,
        readonly=False,
        depth=0,
        *args,
        **kwargs,
    ):
        """...

        If output is None (default), both inputs and outputs are displayed.
        Otherwise only inputs (output=False) or outputs (output=True) are.
        """
        try:
            # we cannot know if another inheritance will need args or not...
            kwargs["depth"] = depth
            super().__init__(*args, **kwargs)
        except TypeError:
            super().__init__()
        self.allow_update_gui = True
        self.depth = depth
        self.controller = controller
        self.output = output
        self.user_level = user_level
        self.readonly = readonly
        if not readonly and isinstance(controller, OpenKeyController):
            self.editable = True
        self.build()
        controller.on_inner_value_change.add(proxy_method(self.update_inner_gui))
        controller.on_fields_change.add(proxy_method(self.update_fields))

    def __del__(self):
        self.disconnect()

    def build(self):
        controller = self.controller

        self.factories = {}
        if (
            not self.readonly
            and isinstance(controller, OpenKeyController)
            and not isinstance(self, WidgetsGrid)
        ):
            self.keys_widget = Qt.QWidget()
            l = Qt.QHBoxLayout()
            l.setContentsMargins(0, 0, 0, 0)
            l.addStretch(1)
            plus = Qt.QToolButton(self.keys_widget)
            plus.setText("+")
            # plus.setSizePolicy(Qt.QSizePolicy.Fixed, Qt.QSizePolicy.Fixed)
            l.addWidget(plus)
            self.keys_widget.setLayout(l)
            self.add_widget_row(self.keys_widget)
            plus.clicked.connect(self.add_item)

            class ButtonFactory(WidgetFactory):
                def delete_widgets(self):
                    self.controller_widget.remove_widget_row()
                    del self.controller_widget.keys_widget

            factory = ButtonFactory(self, None, readonly=False)
            self.factories["button"] = factory

        # Select and sort fields
        fields = []
        for field in controller.fields():
            if (
                self.output is None
                or (not self.output and not field.is_output())
                or (self.output and field.is_output())
            ) and (
                self.user_level is None
                or self.user_level >= field.metadata("user_level", 0)
            ):
                fields.append(field)
        self.fields = sorted(fields, key=lambda f: f.metadata("order"))
        self.groups = {
            None: self,
        }
        for field in self.fields:
            group = field.metadata("group", None)
            group_content_widget = self.groups.get(group)
            if group_content_widget is None:
                group_content_widget = WidgetsGrid(depth=self.depth)
                self.group_widget = GroupWidget(group)

                self.group_widget.layout().addWidget(group_content_widget)
                self.add_widget_row(self.group_widget)
                self.groups[group] = group_content_widget

            type_id = field.type
            factory_type = WidgetFactory.find_factory(type_id, DefaultWidgetFactory)
            factory = factory_type(
                controller_widget=group_content_widget,
                parent_interaction=ControllerFieldInteraction(
                    controller, field, self.depth
                ),
                readonly=self.readonly,
            )
            self.factories[field._dataclass_field] = factory
            factory.create_widgets()

    def update_inner_gui(self, indices):
        if self.allow_update_gui:
            self.allow_update_gui = False
            field = indices[0]
            indices = indices[1:]
            if indices:
                factory = self.factories.get(field._dataclass_field)
                if factory is not None:
                    factory.update_inner_gui(indices)
            self.allow_update_gui = True

    def update_fields(self):
        if self.allow_update_gui:
            self.allow_update_gui = False
            expanded = self.expanded_items()
            self.clear()
            self.build()
            self.set_expanded_items(expanded, silent=True)
            self.allow_update_gui = True

    def clear(self):
        for factory in self.factories.values():
            factory.delete_widgets()
        self.factories = {}
        self.groups = {}
        if hasattr(self, "group_widget"):
            del self.group_widget
        self.fields = []

    def disconnect(self):
        if hasattr(self, "controller"):
            self.controller.on_inner_value_change.remove(
                proxy_method(self.update_inner_gui)
            )
            self.controller.on_fields_change.remove(proxy_method(self.update_fields))
            # if called from __del__(), proxy_methods are already dead refs,
            # and they cannot be identified to self any longer. So let's do a
            # full gc.
            self.controller.gc_callbacks()

    def ask_new_key_name(self, init_text=None):
        dialog = Qt.QDialog()
        layout = Qt.QVBoxLayout()
        dialog.setLayout(layout)

        layout.addWidget(Qt.QLabel("field:"))
        le = Qt.QLineEdit()
        if init_text:
            le.setText(init_text)
        layout.addWidget(le)

        blay = Qt.QHBoxLayout()
        layout.addLayout(blay)
        ok = Qt.QPushButton("OK")
        blay.addWidget(ok)
        cancel = Qt.QPushButton("Cancel")
        blay.addWidget(cancel)
        ok.clicked.connect(dialog.accept)
        cancel.clicked.connect(dialog.reject)
        ok.setDefault(True)

        res = dialog.exec_()
        if res == Qt.QDialog.Accepted:
            name = le.text()
            if (
                name == ""
                or "." in name
                or "/" in name
                or "-" in name
                or " " in name
                or name[0] in "0123456789"
            ):
                print("invalid name", name)
                return None
            if self.controller.field(name) is not None:
                print("field", name, "already exists.")
                return None
            return name
        return None

    def ask_existing_key_name(self):
        dialog = Qt.QDialog()
        layout = Qt.QVBoxLayout()
        dialog.setLayout(layout)

        layout.addWidget(Qt.QLabel("field:"))
        le = Qt.QLineEdit()
        layout.addWidget(le)

        blay = Qt.QHBoxLayout()
        layout.addLayout(blay)
        ok = Qt.QPushButton("OK")
        blay.addWidget(ok)
        cancel = Qt.QPushButton("Cancel")
        blay.addWidget(cancel)
        ok.clicked.connect(dialog.accept)
        cancel.clicked.connect(dialog.reject)
        ok.setDefault(True)

        res = dialog.exec_()
        if res == Qt.QDialog.Accepted:
            name = le.text()
            if self.controller.field(name) is None:
                print("field", name, "does not exist.")
                return None
            return name
        return None

    def add_item(self):
        new_key = self.ask_new_key_name()
        if not new_key:
            return
        controller = self.controller
        item_type = controller._value_type
        new_value = type_default_value(item_type)
        setattr(controller, new_key, new_value)
        self.set_expanded_items({new_key: "all"})

    def remove_item(self):
        key = self.ask_existing_key_name()
        if not key:
            return
        value = getattr(self.controller, key, undefined)
        if value is not undefined and value:
            delattr(self.controller, key)

    def edit_field_name(self, field):
        new_field_name = self.ask_new_key_name(field)
        if new_field_name:
            old_field = self.controller.field(field)
            value = getattr(self.controller, field, undefined)
            self.controller.remove_field(field)
            self.controller.add_field(new_field_name, old_field)
            exp = self.expanded_items().get(field, "all")
            setattr(self.controller, new_field_name, value)
            self.set_expanded_items({new_field_name: exp})

    def remove_field(self, field):
        self.controller.remove_field(field)

    def expanded_items(self):
        """Get expanded items and sub-items, recursively as a dict

        The returned dict keys are fields names. Values are either True
        (expanded), False (collapsed), or a dict with expanded stated of sub-
        fields.
        """
        expanded = {}
        for field, factory in self.factories.items():
            # test if the field is still in the controller: it may have been
            # removed, and the GUI in the process of updating
            if self.controller.field(field.name):
                expanded[field.name] = factory.expanded_items()
        return expanded

    def set_expanded_items(self, expanded, silent=False):
        """Set items and sub-items expanded states

        Parameters
        ----------
        expanded: dict, 'all', or None
            {field_name: state} dict. A state items may be either:

            * a bool (True or False), meaning that the field is expanded or
            not, and does not assign sub-items state;
            * a dict, meaning that the field item is expanded, and specifies
            sub-items states when the field has items.
            * the string 'all', meaning that all sub_items should be expanded
            recursively.
            * None, meaning that the field itself may be expanded, but all
            children will be collapsed.
        silent: bool
            if silent, missing fields (items in the expanded dict which do not
            exist in the controller) will be ignored silently.
        """
        if expanded == "all":
            for factory in self.factories.values():
                factory.set_expanded_items("all")
        elif expanded is None:
            for factory in self.factories.values():
                factory.set_expanded_items(None)
        else:
            for key, exp_value in expanded.items():
                item_field = self.controller.field(key)
                if item_field is None:
                    if not silent:
                        print("no field", key)
                    continue
                factory = self.factories.get(item_field._dataclass_field)
                if factory is None:
                    if not silent:
                        print("no factory for field", key)
                    continue
                factory.set_expanded_items(exp_value, silent=silent)

    def set_visible(self, fields, on=True):
        for fname in fields:
            item_field = self.controller.field(fname)
            factory = self.factories.get(item_field._dataclass_field)
            if factory is not None:
                factory.set_visible(on)


class ControllerWidget(BaseControllerWidget, ScrollableWidgetsGrid):
    pass


class ControllerSubwidget(BaseControllerWidget, WidgetsGrid):
    pass


class ControllerWidgetFactory(WidgetFactory):
    def create_widgets(self):
        controller = self.parent_interaction.get_value()
        if controller is undefined:
            if hasattr(self.parent_interaction, "field"):
                controller = self.parent_interaction.field.type()
            # else ?
        self.inner_widget = ControllerSubwidget(
            controller, depth=self.controller_widget.depth + 1, readonly=self.readonly
        )
        label = self.parent_interaction.get_label()
        self.widget = CollapsibleWidget(
            self.inner_widget,
            label=label,
            expanded=(self.parent_interaction.depth == 0),
            parent=self.controller_widget,
        )
        self.widget.setToolTip(self.parent_interaction.get_doc())
        self.inner_widget.setContentsMargins(
            self.widget.toggle_button.sizeHint().height(), 0, 0, 0
        )

        field_name = None
        if hasattr(self.parent_interaction, "field"):
            field_name = self.parent_interaction.field.name
        self.controller_widget.add_widget_row(
            self.widget, label_index=0, field_name=field_name
        )
        self.parent_interaction.on_change_add(proxy_method(self.update_gui))

    def delete_widgets(self):
        self.parent_interaction.on_change_remove(proxy_method(self.update_gui))
        self.controller_widget.remove_widget_row()
        self.inner_widget.clear()
        self.inner_widget.disconnect()
        self.widget.deleteLater()
        self.inner_widget.deleteLater()

    def update_gui(self):
        self.delete_widgets()
        self.create_widgets()

    def set_expanded_items(self, exp_value, silent=False):
        if isinstance(exp_value, dict) or exp_value == "all":
            self.widget.toggle_expand(True)
            self.inner_widget.set_expanded_items(exp_value, silent=silent)
        else:
            expanded = bool(exp_value)
            self.widget.toggle_expand(exp_value)

    def expanded_items(self):
        expanded = {}
        if not self.widget.toggle_button.isChecked():
            expanded = False
        else:
            expanded = self.inner_widget.expanded_items()
        return expanded

    def set_visible(self, on):
        self.widget.setVisible(on)


from .bool import BoolWidgetFactory
from .list import (
    ListFloatWidgetFactory,
    ListIntWidgetFactory,
    ListStrWidgetFactory,
    find_generic_list_factory,
)
from .literal import LiteralWidgetFactory
from .openkeycontroller import OpenKeyControllerWidgetFactory

# from .dict import DictWidgetFactory
from .path import DirectoryWidgetFactory, FileWidgetFactory
from .set import (
    SetFloatWidgetFactory,
    SetIntWidgetFactory,
    SetStrWidgetFactory,
    find_generic_set_factory,
)
from .str import StrWidgetFactory

# Above imports also import the module. This hides
# the corresponding builtins => remove them
del str, bool, literal, list, set, path  # , dict

WidgetFactory.widget_factory_types = {
    "str": StrWidgetFactory,
    "int": StrWidgetFactory,
    "float": StrWidgetFactory,
    "bool": BoolWidgetFactory,
    "Literal": LiteralWidgetFactory,
    "list[str]": ListStrWidgetFactory,
    "list[int]": ListIntWidgetFactory,
    "list[float]": ListFloatWidgetFactory,
    "list": find_generic_list_factory,
    "List[str]": ListStrWidgetFactory,
    "List[int]": ListIntWidgetFactory,
    "List[float]": ListFloatWidgetFactory,
    "List": find_generic_list_factory,
    "set[str]": SetStrWidgetFactory,
    "set[int]": SetIntWidgetFactory,
    "set[float]": SetFloatWidgetFactory,
    "set": find_generic_set_factory,
    #'dict': DictWidgetFactory,
    #'dict[str, str]': DictWidgetFactory,
    "Controller": ControllerWidgetFactory,
    "File": FileWidgetFactory,
    "Directory": DirectoryWidgetFactory,
    "OpenKeyController": OpenKeyControllerWidgetFactory,
    "OpenKeyController[str]": OpenKeyControllerWidgetFactory,
    "OpenKeyDictController": OpenKeyControllerWidgetFactory,
    "OpenKeyDictController[str]": OpenKeyControllerWidgetFactory,
    "pydantic.conlist": find_generic_list_factory,
}
