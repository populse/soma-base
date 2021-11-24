# -*- coding: utf-8 -*-

from soma.controller import (
    parse_type_str, 
    subtypes,
    field_type,
    field_type_str,
    is_output,
)
from soma.qt_gui.qt_backend import Qt
from soma.undefined import undefined


class ScrollableWidgetsGrid(Qt.QScrollArea):
    """
    A widget that is used for Controller main windows (i.e.
    top level widget).
    It has a 2 colums grid layout aligned ont the top of the
    window. It allows to add many inner_widgets rows. Each
    row contains either 1 or 2 widgets. A single widget uses
    the two colums of the row.
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

    def add_widget_row(self, first_widget, second_widget=None):
        row = self.content_layout.rowCount()
        if second_widget is None:
            self.content_layout.addWidget(first_widget, row, 0, 1, 2)
        else:
            self.content_layout.addWidget(first_widget, row, 0, 1, 1)
            self.content_layout.addWidget(second_widget, row, 1, 1, 1)

    def remove_widget_row(self):
        row = self.content_layout.rowCount()-1
        for column in range(self.content_layout.columnCount()):
            self.content_layout.removeItem(self.content_layout.itemAtPosition(row, column))

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
  

    def add_widget_row(self, first_widget, second_widget=None):
        row = self.content_layout.rowCount()
        if second_widget is None:
            self.content_layout.addWidget(first_widget, row, 0, 1, 2)
        else:
            self.content_layout.addWidget(first_widget, row, 0, 1, 1)
            self.content_layout.addWidget(second_widget, row, 1, 1, 1)

    def remove_widget_row(self):
        row = self.content_layout.rowCount()-1
        for column in range(self.content_layout.columnCount()):
            self.content_layout.removeItem(self.content_layout.itemAtPosition(row, column))


class GroupWidget(Qt.QFrame):
    def __init__(self, label, expanded=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        Qt.QVBoxLayout(self)
        self.label = label
        self.setFrameStyle(self.StyledPanel | self.Raised)
        self.toggle_button = Qt.QToolButton(self)
        self.toggle_button.setCheckable(True)
        self.toggle_button.setStyleSheet('QToolButton { border: none; }')
        self.toggle_expand(expanded)
        self.toggle_button.resize(self.toggle_button.sizeHint())
        self.toggle_button.move(-2,-2)
        self.setContentsMargins(3,3,3,3)
        self.toggle_button.clicked.connect(self.toggle_expand)
    
    def toggle_expand(self, expanded):
        arrow = ('▼' if expanded else '▶')
        self.toggle_button.setText(f'{self.label}  {arrow}')
        self.toggle_button.setChecked(expanded)
        for i in range(self.layout().count()):
            widget = self.layout().itemAt(i).widget()
            if widget:
                if expanded:
                   widget.show()
                else:
                    widget.hide()

class WidgetFactory:
    valid_style_sheet = ''
    warning_style_sheet = 'background: #FFFFC8;'
    invalid_style_sheet = 'background: #FFDCDC;'
    
    def __init__(self, controller_widget, parent_interaction):
        super().__init__()
        self.controller_widget = controller_widget
        self.parent_interaction = parent_interaction


    @classmethod
    def find_factory(cls, type_str, default=None):
        subtypes = []
        factory_finder = cls.widget_factory_types.get(type_str)
        if factory_finder is None:
            type_str, subtypes = parse_type_str(type_str)
            factory_finder = cls.widget_factory_types.get(type_str)
        if factory_finder is not None:
            if isinstance(factory_finder, type) and issubclass(factory_finder, WidgetFactory):
                return factory_finder
            else:
                factory_class = factory_finder(type_str, subtypes)
                if factory_class is not None:
                    return factory_class
        return default


class ControllerFieldInteraction:
    def __init__(self, controller, field, depth):
        self.controller = controller
        self.field = field
        self.type = field_type(field)
        self.type_str = field_type_str(field)
        self.depth = depth
    
    @property
    def is_output(self):
        return is_output(self.field)
    
    def get_value(self, default=undefined):
        return getattr(self.controller, self.field.name, default)

    def set_value(self, value):
        setattr(self.controller, self.field.name, value)
    
    def get_label(self):
        return self.controller.metadata(self.field, 'label', self.field.name)
    
    def on_change_add(self, callback):
        self.controller.on_attribute_change.add(callback, self.field.name)

    def on_change_remove(self, callback):
        self.controller.on_attribute_change.remove(callback, self.field.name)

    def set_protected(self, protected):
        self.controller.set_metadata(self.field, 'protected', protected)

    def inner_item_changed(self, index):
        value = self.get_value()
        self.controller.on_attribute_change.fire(self.field.name, value, value, self.controller, index)

    def is_optional(self):
        return self.controller.is_optional(self.field)


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
        return self.parent_interaction.is_output()

    def get_value(self, default=undefined):
        values = self.parent_interaction.get_value()
        if values is not undefined:
            return values[self.index]
        return default

    def set_value(self, value):
        self.parent_interaction.get_value()[self.index] = value
    
    def get_label(self):
        return f'{self.parent_interaction.get_label()}[{self.index}]'
    
    def on_change_add(self, callback):
        pass

    def on_change_remove(self, callback):
        pass

    def set_protected(self, protected):
        pass

    def inner_item_changed(self, index):
        self.parent_interaction.inner_item_changed(index)

    def is_optional(self):
        return False

 

class DefaultWidgetFactory(WidgetFactory):
    def create_widgets(self):
        self.text_widget = Qt.QLineEdit(parent=self.controller_widget)
        self.text_widget.setStyleSheet('QLineEdit { color: red; }')
        self.text_widget.setReadOnly(True)
        self.text_widget.setToolTip(f'No graphical editor found for type {self.parent_interaction.type_str}')

        self.parent_interaction.on_change_add(self.update_gui)
        self.update_gui()

        label = self.parent_interaction.get_label()
        self.label_widget = Qt.QLabel(label, parent=self.controller_widget)
        self.controller_widget.add_widget_row(self.label_widget, self.text_widget)

    def remove_widgets(self):
        self.parent_interaction.on_change_remove(self.update_gui)
        self.controller_widget.remove_widget_row()
        self.label_widget.deleteLater()
        self.text_widget.deleteLater()
    
    def update_gui(self):
        value = self.parent_interaction.get_value()
        self.text_widget.setText(f'{value}')

from .str import StrWidgetFactory
from .list import (ListStrWidgetFactory,
                   ListIntWidgetFactory,
                   ListFloatWidgetFactory,
                   find_generic_list_factory)
from .set import (SetStrWidgetFactory,
                  SetIntWidgetFactory,
                  SetFloatWidgetFactory,
                  find_generic_set_factory)
from .controller import ControllerWidgetFactory, ControllerWidget
from .path import FileWidgetFactory, DirectoryWidgetFactory

WidgetFactory.widget_factory_types = {
    'str': StrWidgetFactory,
    'int': StrWidgetFactory,
    'float': StrWidgetFactory,
    'list[str]': ListStrWidgetFactory,
    'list[int]': ListIntWidgetFactory,
    'list[float]': ListFloatWidgetFactory,
    'list': find_generic_list_factory,
    'set[str]': SetStrWidgetFactory,
    'set[int]': SetIntWidgetFactory,
    'set[float]': SetFloatWidgetFactory,
    'set': find_generic_set_factory,
    'controller': ControllerWidgetFactory,
    'file': FileWidgetFactory,
    'directory': DirectoryWidgetFactory,
}
