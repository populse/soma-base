from soma.qt_gui.qt_backend import Qt, QtCore


class CollapsibleWidget(Qt.QWidget):
    """
    A widget able to show or hide another widget. It has a grid layout
    with first row containing a clickable label and second row containing
    an inner widget given at initialization time. Clicking on label allow
    to show/hide the inner widget.
    """

    def __init__(
        self,
        inner_widget: Qt.QWidget,
        label: str,
        expanded=False,
        buttons_label=(),
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.label = label
        self.toggle_button = Qt.QPushButton(parent=self)
        self.toggle_button.setStyleSheet("QPushButton { border: none; }")
        self.toggle_button.setCheckable(True)

        bar = Qt.QWidget(parent=self)
        hlayout = Qt.QHBoxLayout(bar)
        header_line = Qt.QFrame(parent=self)
        header_line.setFrameShape(Qt.QFrame.HLine)
        header_line.setFrameShadow(Qt.QFrame.Sunken)
        header_line.setSizePolicy(Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Maximum)
        header_line.setContentsMargins(0, 0, 0, 0)
        hlayout.addWidget(header_line)
        hlayout.setContentsMargins(0, 0, 0, 0)
        self.buttons = []
        for icon in buttons_label:
            button = Qt.QToolButton(parent=bar)
            button.setText(icon)
            hlayout.addWidget(button)
            self.buttons.append(button)

        # don't waste space
        self.main_layout = Qt.QGridLayout()
        self.main_layout.setVerticalSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.toggle_button, 0, 0, 1, 1, QtCore.Qt.AlignLeft)
        self.main_layout.addWidget(bar, 0, 2, 1, 1)
        self.setLayout(self.main_layout)
        self.setSizePolicy(Qt.QSizePolicy.MinimumExpanding, Qt.QSizePolicy.Minimum)
        self.toggle_button.clicked.connect(self.toggle_expand)

        self.inner_widget = inner_widget

        self.main_layout.addWidget(self.inner_widget, 1, 0, 1, 3)
        self.toggle_expand(expanded)

    def toggle_expand(self, expanded):
        arrow = "▼" if expanded else "▶"
        self.toggle_button.setText(f"{self.label}  {arrow}")
        self.toggle_button.setChecked(expanded)
        if expanded:
            for button in self.buttons:
                button.show()
            self.inner_widget.show()
        else:
            for button in self.buttons:
                button.hide()
            self.inner_widget.hide()
