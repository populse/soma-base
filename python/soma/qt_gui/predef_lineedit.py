from soma.qt_gui.qt_backend import Qt

try:
    from traits.api import Undefined
except ImportError:
    Undefined = None
from functools import partial


class QPredefLineEdit(Qt.QLineEdit):
    """
    A QLineEdit variant allowing to select predefined values using a right-
    click popup.

    This allows to handle and distinguish between values such as "", None, and
    traits.Undefined typically, or allow other values.

    The widget also supports None and Undefined values, represented as "<none>"
    and "<undefined>" respectively, when allow_none and/or allow_undefined are
    enabled. These special values can be queried using :meth:`value` instead of
    :meth:`text`.
    """

    def __init__(
        self,
        parent_or_contents=None,
        parent=None,
        predefined_values=None,
        allow_none=False,
        allow_undefined=False,
        *args,
        **kwargs,
    ):
        if parent is not None:
            args = (parent,) + args
        if parent_or_contents is not None:
            args = (parent_or_contents,) + args
        super().__init__(*args, **kwargs)
        if predefined_values is None:
            predefined_values = []
        self.predefined_values = predefined_values
        self.allow_none = (
            allow_none
            or None in predefined_values
            or ("<none>", None) in predefined_values
        )
        self.allow_undefined = (
            allow_undefined
            or Undefined in predefined_values
            or ("<undefined>", Undefined) in predefined_values
        )

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()

        if self.predefined_values:
            menu.addSeparator()
            for value in self.predefined_values:
                if isinstance(value, (tuple, list)):
                    msg, value = value
                else:
                    msg = value
                msg = self.text_repr(msg)
                action = menu.addAction(msg)
                action.value = value
                action.triggered.connect(partial(self.set_value, value))
        menu.exec_(event.globalPos())

    def text_repr(self, value):
        if value is None:
            return "<none>"
        if value is Undefined:
            return "<undefined>"
        if not isinstance(value, (str, bytes)):
            value = str(value)
        if isinstance(value, bytes):
            value = value.decode()
        return value

    def value(self):
        text = self.text()
        if self.allow_none and text == "<none>":
            return None
        if self.allow_undefined and text == "<undefined>":
            return Undefined
        return text

    def set_value(self, value):
        self.setText(self.text_repr(value))
