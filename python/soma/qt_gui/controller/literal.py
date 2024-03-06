try:
    from pydantic.v1 import ValidationError
except ImportError:
    from pydantic import ValidationError

from soma.controller import literal_values
from soma.utils.weak_proxy import proxy_method


class LiteralWidgetFactory(WidgetFactory):
    def create_widgets(self):
        label = self.parent_interaction.get_label()
        self.label_widget = Qt.QLabel(label, parent=self.controller_widget)
        self.label_widget.setToolTip(self.parent_interaction.get_doc())
        self.widget = Qt.QComboBox(parent=self.controller_widget)
        for v in literal_values(self.parent_interaction.type):
            self.widget.addItem(str(v))
        self.widget.setSizePolicy(Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Fixed)

        self.parent_interaction.on_change_add(proxy_method(self, "update_gui"))
        self.update_gui()

        self.widget.currentTextChanged.connect(proxy_method(self, "update_controller"))

        self.controller_widget.add_widget_row(self.label_widget, self.widget)

    def delete_widgets(self):
        self.controller_widget.remove_widget_row()
        self.widget.currentTextChanged.disconnect(
            proxy_method(self, "update_controller")
        )
        self.parent_interaction.on_change_remove(proxy_method(self, "update_gui"))
        self.widget.deleteLater()
        self.label_widget.deleteLater()

    def update_gui(self):
        value = self.parent_interaction.get_value()
        if value is undefined:
            if self.parent_interaction.is_optional():
                self.widget.setStyleSheet(self.warning_style_sheet)
            else:
                self.widget.setStyleSheet(self.invalid_style_sheet)
        else:
            self.widget.setStyleSheet(self.valid_style_sheet)
            self.widget.setCurrentText(str(value))

    def update_controller(self):
        try:
            self.parent_interaction.set_value(self.widget.currentText())
        except ValidationError:
            self.widget.setStyleSheet(self.invalid_style_sheet)
        else:
            self.parent_interaction.set_protected(False)
            self.widget.setStyleSheet(self.valid_style_sheet)

    def set_visible(self, on):
        self.widget.setVisible(on)
        self.label_widget.setVisible(on)
