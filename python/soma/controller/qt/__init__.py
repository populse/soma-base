import typing
import weakref

from soma.qt_gui.qt_backend import Qt, QtCore
from soma.qt_gui.timered_widgets import TimeredQLineEdit


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


class ControllerWidget(Qt.QScrollArea):
    _field_to_widget_methods = {
        str: "add_str_widget",
        int: "add_str_widget",
        float: "add_str_widget",
        bool: "add_bool_widget",
        "Literal": "add_literal_widget",
    }

    valid_style_sheet = ""
    warning_style_sheet = "background: #FFFFC8;"
    invalid_style_sheet = "background: #FFDCDC;"

    def __init__(self, controller, read_only=False, filter=None, parent=None):
        super().__init__(parent=parent)
        self.content_widget = Qt.QWidget(self)
        hlayout = Qt.QVBoxLayout()
        self.content_layout = Qt.QGridLayout()
        hlayout.addLayout(self.content_layout)
        hlayout.addStretch(1)
        self.content_widget.setLayout(hlayout)
        self.setWidget(self.content_widget)
        self.setWidgetResizable(True)

        self.read_only = bool(read_only)
        group_widgets = {}
        row = 0
        for field in controller.fields():
            if filter and not filter(field):
                continue
            group = getattr(field, "group", None)
            if group:
                group_widget = group_widgets.get(group)
                if group_widget is None:
                    # TODO: create group widget
                    group_widget = group_widgets[group] = self
                parent_widget = group_widget
            else:
                parent_widget = self
            method_name = self._field_to_widget_methods.get(field.type)
            if method_name is None:
                full_type = field.type_str()
                main_type = full_type.split("[", 1)[0]
                method_name = self._field_to_widget_methods.get(main_type)
            if method_name:
                getattr(self, method_name)(controller, field, parent_widget, row)
                row += 1
            else:
                print(f"{field.name} : {field.type} ({field.type_str()})")

    def create_label_widget(self, field, parent_widget):
        label = getattr(field, "label", field.name)
        label_widget = Qt.QLabel(label, parent=parent_widget)
        doc = getattr(field, "doc", None)
        if doc:
            label_widget.setToolTiupdap(doc)
        return label_widget

    def add_str_widget(self, controller, field, parent_widget, row):
        label_widget = self.create_label_widget(field, parent_widget)
        text_widget = TimeredQLineEdit(parent=parent_widget)
        text_widget.ignore_update = False
        if self.read_only:
            text_widget.setReadOnly(True)
        parent_widget.content_layout.addWidget(label_widget, row, 0, 1, 1)
        parent_widget.content_layout.addWidget(text_widget, row, 1, 1, 1)
        text_widget_proxy = weakref.proxy(text_widget)

        def update_widget(new_value, text_widget=text_widget_proxy):
            if not text_widget.ignore_update:
                text_widget.setText(f"{new_value}")

        def update_controller(
            text_widget=text_widget_proxy,
            controller=weakref.proxy(controller),
            field=field,
        ):
            try:
                value = text_widget.text()
                if value:
                    value = field.type(value)
                text_widget.ignore_update = True
                try:
                    setattr(controller, field.name, value)
                finally:
                    text_widget.ignore_update = False
                text_widget.setStyleSheet(self.valid_style_sheet)
            except Exception:
                text_widget.setStyleSheet(self.invalid_style_sheet)

        value = getattr(controller, field.name, "")
        text_widget.setText(f"{value}")

        controller.on_attribute_change.add(
            update_widget,
            field.name,
        )
        if not self.read_only:
            text_widget.userModification.connect(update_controller)

    def add_bool_widget(self, controller, field, parent_widget, row):
        label = getattr(field, "label", field.name)
        if self.read_only:
            bool_widget = ReadOnlyCheckBox(label, parent=parent_widget)
        else:
            bool_widget = Qt.QCheckBox(label, parent=parent_widget)
        bool_widget.setSizePolicy(Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Fixed)
        doc = getattr(field, "doc", None)
        if doc:
            bool_widget.setToolTip(doc)
        parent_widget.content_layout.addWidget(bool_widget, row, 1, 1, 2)
        bool_widget_proxy = weakref.proxy(bool_widget)

        def update_widget(new_value, bool_widget=bool_widget_proxy):
            bool_widget.setChecked(new_value)

        def update_controller(
            state,
            bool_widget=bool_widget_proxy,
            controller=weakref.proxy(controller),
            field=field,
        ):
            try:
                value = bool_widget.isChecked()
                setattr(controller, field.name, value)
                bool_widget.setStyleSheet(self.valid_style_sheet)
            except Exception:
                bool_widget.setStyleSheet(self.invalid_style_sheet)

        value = getattr(controller, field.name, False)
        bool_widget.setChecked(value)

        controller.on_attribute_change.add(
            update_widget,
            field.name,
        )
        if not self.read_only:
            bool_widget.stateChanged.connect(update_controller)

    def add_literal_widget(self, controller, field, parent_widget, row):
        label_widget = self.create_label_widget(field, parent_widget)
        if self.read_only:
            literal_widget = Qt.QLabel("")
        else:
            literal_widget = Qt.QComboBox(parent_widget)
            for v in field.literal_values():
                literal_widget.addItem(str(v))
        literal_widget.setSizePolicy(Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Fixed)

        parent_widget.content_layout.addWidget(label_widget, row, 0, 1, 1)
        parent_widget.content_layout.addWidget(literal_widget, row, 1, 1, 1)
        literal_widget_proxy = weakref.proxy(literal_widget)

        def update_widget(new_value, literal_widget=literal_widget_proxy):
            if hasattr(literal_widget, "setText"):
                literal_widget.setText(new_value)
            else:
                literal_widget.setCurrentText(str(new_value))

        def update_controller(
            value,
            literal_widget=literal_widget_proxy,
            controller=weakref.proxy(controller),
            field=field,
        ):
            try:
                try:
                    setattr(controller, field.name, value)
                finally:
                    literal_widget.ignore_update = False
                literal_widget.setStyleSheet(self.valid_style_sheet)
            except Exception:
                literal_widget.setStyleSheet(self.invalid_style_sheet)

        value = getattr(controller, field.name)
        if self.read_only:
            literal_widget.setText(str(value))
        else:
            literal_widget.setCurrentText(str(value))

        controller.on_attribute_change.add(
            update_widget,
            field.name,
        )
        if not self.read_only:
            literal_widget.currentTextChanged.connect(update_controller)
