import functools
import weakref

from soma.controller import type_str, literal_values
from soma.qt_gui.qt_backend import Qt, QtCore
from soma.qt_gui.timered_widgets import TimeredQLineEdit
from soma.qt_gui.collapsible import CollapsibleWidget


class ReadOnlyCheckBox(Qt.QCheckBox):
    def __init__(self, label="", parent=None):
        super().__init__(label, parent)

    def mousePressEvent(self, event):
        event.ignore()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Space, Qt.Key_Return, Qt.Key_Enter):
            event.ignore()
        else:
            super().keyPressEvent(event)


class QtLink:
    def __init__(self, container_qt_link, field, list_index, container_widget):
        self.container_qt_link = container_qt_link
        self.field = field
        self.list_index = list_index
        self.controller = self.container_qt_link.controller
        self.create_qt_link(container_widget)

    def get_label(self):
        label = getattr(self.field, "label", self.field.name)
        if self.list_index is not None:
            label += f"[{self.list_index}]"
        return label

    def create_label_widget(self, container_widget):
        label = self.get_label()
        label_widget = Qt.QLabel(label, parent=container_widget)
        doc = getattr(self.field, "doc", None)
        if doc:
            label_widget.setToolTip(doc)
        return label_widget

    def get_controller_value(self):
        value = getattr(self.controller, self.field.name, None)
        if self.list_index is not None:
            value = value[self.list_index]
        return value

    def set_controller_value(self, value):
        if self.list_index is None:
            setattr(self.controller, self.field.name, value)
        else:
            getattr(self.controller, self.field.name)[self.list_index] = value

    @classmethod
    def get_qt_link_class(cls, type):
        qt_link_class = cls._field_to_widget_methods.get(type)
        if qt_link_class is None:
            full_type = type_str(type)
            main_type = full_type.split("[", 1)[0]
            qt_link_class = cls._field_to_widget_methods.get(main_type)
        return qt_link_class

    @property
    def read_only(self):
        return self.container_qt_link.read_only


class StrQtLink(QtLink):
    valid_style_sheet = ""
    warning_style_sheet = "background: #FFFFC8;"
    invalid_style_sheet = "background: #FFDCDC;"

    def create_qt_link(self, container_widget):
        self.label_widget = self.create_label_widget(container_widget)
        self.text_widget = TimeredQLineEdit(parent=container_widget)
        self.text_widget.ignore_update = False
        if self.read_only:
            self.text_widget.setReadOnly(True)
        row = container_widget.controller_layout.rowCount()
        container_widget.controller_layout.addWidget(self.label_widget, row, 0, 1, 1)
        container_widget.controller_layout.addWidget(self.text_widget, row, 1, 1, 1)

        self.update_widget()

        if self.list_index is None:
            self.container_qt_link.controller.on_attribute_change.add(
                self.update_widget,
                self.field.name,
            )
        if not self.read_only:
            self.text_widget.userModification.connect(self.update_controller)

    def get_widget_value(self):
        return self.from_str(self.text_widget.text())

    def set_widget_value(self, value):
        self.text_widget.setText(self.to_str(value))

    def from_str(self, text):
        if self.list_index is None:
            return self.field.type(text)
        else:
            return self.field.subtypes()[0](text)

    def to_str(self, value):
        return str(value)

    def update_widget(self):
        if not self.text_widget.ignore_update:
            self.set_widget_value(self.get_controller_value())

    def update_controller(self):
        try:
            self.text_widget.ignore_update = True
            try:
                self.set_controller_value(self.get_widget_value())
            finally:
                self.text_widget.ignore_update = False
            self.text_widget.setStyleSheet(self.valid_style_sheet)
        except Exception:
            self.text_widget.setStyleSheet(self.invalid_style_sheet)


class ListNumberQtLink(StrQtLink):
    def from_str(self, text):
        type = self.field.subtypes()[0]
        return [type(i) for i in text.split()]

    def to_str(self, value):
        return " ".join(str(i) for i in value)


class BoolQtLink(QtLink):
    def create_qt_link(self, container_widget):
        label = self.get_label()
        if self.read_only:
            self.widget = ReadOnlyCheckBox(label, parent=container_widget)
        else:
            self.widget = Qt.QCheckBox(label, parent=container_widget)
        self.widget.setSizePolicy(Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Fixed)
        doc = getattr(self.field, "doc", None)
        if doc:
            self.widget.setToolTip(doc)
        row = container_widget.controller_layout.rowCount()
        container_widget.controller_layout.addWidget(self.widget, row, 1, 1, 2)

        self.update_widget()

        if self.list_index is None:
            self.container_qt_link.controller.on_attribute_change.add(
                self.update_widget,
                self.field.name,
            )

        if not self.read_only:
            self.widget.stateChanged.connect(self.update_controller)

    def get_widget_value(self):
        return self.widget.isChecked()

    def set_widget_value(self, value):
        self.widget.setChecked(value)

    def update_widget(self):
        self.set_widget_value(self.get_controller_value())

    def update_controller(self):
        self.set_controller_value(self.get_widget_value())


class LiteralQtLink(QtLink):
    def create_qt_link(self, container_widget):
        self.label_widget = self.create_label_widget(container_widget)
        if self.read_only:
            self.widget = Qt.QLabel("")
        else:
            self.widget = Qt.QComboBox(container_widget)
            if self.list_index is None:
                type = self.field.type
            else:
                type = self.field.subtypes()[0]
            for v in literal_values(type):
                self.widget.addItem(str(v))
        self.widget.setSizePolicy(Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Fixed)
        row = container_widget.controller_layout.rowCount()
        container_widget.controller_layout.addWidget(self.label_widget, row, 0, 1, 1)
        container_widget.controller_layout.addWidget(self.widget, row, 1, 1, 1)

        self.update_widget()

        if self.list_index is None:
            self.container_qt_link.controller.on_attribute_change.add(
                self.update_widget,
                self.field.name,
            )

        if not self.read_only:
            self.widget.currentTextChanged.connect(self.update_controller)

    def get_widget_value(self):
        if self.read_only:
            return self.widget.text()
        else:
            return self.widget.currentText()

    def set_widget_value(self, value):
        if self.read_only:
            self.widget.setText(value)
        else:
            self.widget.setCurrentText(value)

    def update_widget(self):
        self.set_widget_value(self.get_controller_value())

    def update_controller(self):
        self.set_controller_value(self.get_widget_value())


class PathQtLink(QtLink):
    def create_qt_link(self, container_widget):
        self.label_widget = self.create_label_widget(container_widget)
        self.widget = Qt.QWidget(parent=container_widget)
        layout = Qt.QHBoxLayout(self.widget)
        layout.setContentsMargins(0, 0, 0, 0)
        self.text_widget = TimeredQLineEdit(parent=self.widget)
        layout.addWidget(self.text_widget)
        if not self.read_only:
            self.button = Qt.QToolButton(self.widget)
            self.button.setText("📂")
            self.button.setFont(Qt.QFont("Noto Color Emoji"))
            self.button.setSizePolicy(Qt.QSizePolicy.Minimum, Qt.QSizePolicy.Minimum)
            self.button.setFocusPolicy(QtCore.Qt.NoFocus)
            self.button.setFocusProxy(self.text_widget)
            layout.addWidget(self.button)
            self.button.clicked.connect(self.path_dialog)
        else:
            self.text_widget.setReadOnly(True)

        row = container_widget.controller_layout.rowCount()
        container_widget.controller_layout.addWidget(self.label_widget, row, 0, 1, 1)
        container_widget.controller_layout.addWidget(self.widget, row, 1, 1, 1)

        self.update_widget()

        if self.list_index is None:
            self.container_qt_link.controller.on_attribute_change.add(
                self.update_widget,
                self.field.name,
            )

        if not self.read_only:
            self.text_widget.userModification.connect(self.update_controller)

    def get_widget_value(self):
        return self.text_widget.text()

    def set_widget_value(self, value):
        self.text_widget.setText(value)

    def update_widget(self):
        self.set_widget_value(self.get_controller_value())

    def update_controller(self):
        self.set_controller_value(self.get_widget_value())

    def path_dialog(self):
        if self.field.output:
            result = Qt.QFileDialog.getSaveFileName(
                parent=self.widget,
                caption=("Select directory" if self.field.is_directory() else "Select file"),
                options=Qt.QFileDialog.DontUseNativeDialog,
            )[0]
        else:
            if self.field.is_directory():
                result = Qt.QFileDialog.getExistingDirectory(
                    parent=self.widget,
                    caption="Select directory",
                    options=Qt.QFileDialog.DontUseNativeDialog,
                )
            else:
                result = Qt.QFileDialog.getOpenFileName(
                    parent=self.widget,
                    caption="Select file",
                    options=Qt.QFileDialog.DontUseNativeDialog,
                )[0]
        self.text_widget.setText(result)


class ListQtLink(QtLink):
    def create_qt_link(self, container_widget):
        self.depth = self.container_qt_link.depth + 1
        label = self.get_label()
        self.widget = Qt.QWidget(parent=container_widget)
        self.widget.controller_layout = Qt.QGridLayout(self.widget)
        self.widget.controller_layout.setContentsMargins(0, 0, 0, 0)
        self.collapsible_widget = CollapsibleWidget(
            self.widget,
            label=label,
            expanded=(self.container_qt_link.depth == 0),
            buttons_label=([] if self.read_only else ["+", "-"]),
            parent=container_widget,
        )
        self.widget.setContentsMargins(
            self.collapsible_widget.toggle_button.sizeHint().height(), 0, 0, 0
        )
        row = container_widget.controller_layout.rowCount()
        container_widget.controller_layout.addWidget(
            self.collapsible_widget, row, 0, 1, 2
        )

        value = self.get_controller_value()
        self.childs = [self.create_item_qt_link(i) for i in range(len(value))]

    def create_item_qt_link(self, list_index):
        qt_link_class = QtLink.get_qt_link_class(self.field.subtypes()[0])
        if qt_link_class:
            return qt_link_class(self, self.field, list_index, self.widget)
        else:
            print(
                f"{self.field.name}[{list_index}] : {self.field.type} ({self.field.type_str()})"
            )

    def get_widget_value(self):
        return [i.get_widget_value() for i in self.childs()]

    def set_widget_value(self, value):
        for c, v in zip(self.child, value):
            c.set_widget_value(v)


class MainControllerQtLink:
    def __init__(self, controller, read_only, filter, parent_widget):
        self.controller = weakref.proxy(controller)
        self.widget = Qt.QWidget(parent_widget)
        hlayout = Qt.QVBoxLayout()
        self.widget.controller_layout = Qt.QGridLayout()
        hlayout.addLayout(self.widget.controller_layout)
        hlayout.addStretch(1)
        self.widget.setLayout(hlayout)
        self.read_only = bool(read_only)
        self.filter = filter
        self.depth = 0

        self.group_widgets = {}
        self.childs = {
            field.name: self.create_qt_link(field)
            for field in controller.fields()
            if not self.filter or self.filter(field)
        }

    def create_qt_link(self, field):
        group = getattr(field, "group", None)
        if group:
            group_widget = self.group_widgets.get(group)
            if group_widget is None:
                # TODO: create group widget
                group_widget = self.group_widgets[group] = self.widget
            container_widget = group_widget
        else:
            container_widget = self.widget
        qt_link_class = QtLink.get_qt_link_class(field.type)
        if qt_link_class:
            return qt_link_class(self, field, None, container_widget)
        else:
            print(f"{field.name} : {field.type} ({field.type_str()})")


QtLink._field_to_widget_methods = {
    str: StrQtLink,
    int: StrQtLink,
    float: StrQtLink,
    bool: BoolQtLink,
    list[int]: ListNumberQtLink,
    list[float]: ListNumberQtLink,
    "Literal": LiteralQtLink,
    "File": PathQtLink,
    "Directory": PathQtLink,
    "list": ListQtLink,
}


class ControllerWidget(Qt.QScrollArea):

    def __init__(self, controller, read_only=False, filter=None, parent=None):
        super().__init__(parent=parent)
        self.qt_link = MainControllerQtLink(controller, read_only, filter, self)
        self.setWidget(self.qt_link.widget)
        self.setWidgetResizable(True)

