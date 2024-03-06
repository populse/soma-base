import os

from soma.qt_gui.qt_backend import (
    Qt,
    QtCore,
    getExistingDirectory,
    getOpenFileName,
    getSaveFileName,
)
from soma.qt_gui.timered_widgets import TimeredQLineEdit
from soma.utils.weak_proxy import proxy_method

from .str import StrWidgetFactory


class FileWidgetFactory(StrWidgetFactory):
    def create_widgets(self):
        label = self.parent_interaction.get_label()
        self.label_widget = Qt.QLabel(label, parent=self.controller_widget)
        self.label_widget.setToolTip(self.parent_interaction.get_doc())
        self.widget = Qt.QWidget(parent=self.controller_widget)
        self.layout = Qt.QHBoxLayout(self.widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.text_widget = TimeredQLineEdit(parent=self.controller_widget)
        self.layout.addWidget(self.text_widget)
        self.button = Qt.QToolButton(self.widget)
        self.button.setText("📂")
        self.button.setSizePolicy(Qt.QSizePolicy.Minimum, Qt.QSizePolicy.Minimum)
        self.button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.button.setFocusProxy(self.text_widget)
        self.layout.addWidget(self.button)
        # self.button.hide()
        # self.text_widget.focusChange.connect(self.update_selection_button)
        self.parent_interaction.on_change_add(proxy_method(self, "update_gui"))
        self.update_gui()

        self.text_widget.userModification.connect(
            proxy_method(self, "update_controller")
        )
        self.button.clicked.connect(proxy_method(self, "select_path_dialog"))

        self.controller_widget.add_widget_row(self.label_widget, self.widget)

    def delete_widgets(self):
        self.controller_widget.remove_widget_row()
        self.button.clicked.disconnect(proxy_method(self, "select_path_dialog"))
        self.text_widget.userModification.disconnect(
            proxy_method(self, "update_controller")
        )
        # self.text_widget.focusChange.disconnect(self.update_selection_button)
        self.parent_interaction.on_change_remove(proxy_method(self, "update_gui"))
        self.button.deleteLater()
        self.text_widget.deleteLater()
        self.layout.deleteLater()
        self.label_widget.deleteLater()

    # def update_selection_button(self, has_focus):
    #     if has_focus:
    #         self.button.show()
    #     else:
    #         self.button.hide()

    def select_path_dialog(self):
        ext = []
        # TODO: manage extensions via formats
        # field = control_instance.field
        # if trait.allowed_extensions:
        #     ext = trait.allowed_extensions
        # if trait.extensions:
        #     ext = trait.extensions
        ext = " ".join(f"*{e}" for e in ext)
        if ext:
            ext += ";; All files (*)"
        # Create a dialog to select a file
        value = self.parent_interaction.get_value(os.getcwd())
        if self.parent_interaction.is_output:
            fname = getSaveFileName(
                self.controller_widget,
                "Output file",
                value,
                ext,
                None,
                Qt.QFileDialog.DontUseNativeDialog,
            )
        else:
            fname = getOpenFileName(
                self.controller_widget,
                "Select file",
                value,
                ext,
                None,
                Qt.QFileDialog.DontUseNativeDialog,
            )
        self.parent_interaction.set_value(fname)

    def set_visible(self, on):
        self.widget.setVisible(on)
        self.label_widget.setVisible(on)


class DirectoryWidgetFactory(FileWidgetFactory):
    def select_path_dialog(self):
        # Create a dialog to select a directory
        value = self.parent_interaction.get_value(
            os.path.dirname(os.path.abspath(os.getcwd()))
        )
        # Create a dialog to select a directory
        folder = getExistingDirectory(
            self.controller_widget,
            "Open directory",
            value,
            Qt.QFileDialog.ShowDirsOnly | Qt.QFileDialog.DontUseNativeDialog,
        )
        self.parent_interaction.set_value(folder)
