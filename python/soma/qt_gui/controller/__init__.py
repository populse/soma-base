# -*- coding: utf-8 -*-

from soma.controller import (
    parse_type_str, 
    subtypes,
    field_type,
    field_type_str,
    is_output,
)
from soma.qt_gui.qt_backend import Qt, QtCore
from soma.undefined import undefined
from ..collapsable import CollapsableWidget

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
        self.setSizePolicy(Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Expanding)
    
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


class WidgetFactory(Qt.QObject):
    valid_style_sheet = ''
    warning_style_sheet = 'background: #FFFFC8;'
    invalid_style_sheet = 'background: #FFDCDC;'
    
    inner_item_changed = QtCore.Signal(int)

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
        return self.controller.metadata(self.field, 'label', self.field.name)
    
    def on_change_add(self, callback):
        self.controller.on_attribute_change.add(callback, self.field.name)

    def on_change_remove(self, callback):
        self.controller.on_attribute_change.remove(callback, self.field.name)

    def set_protected(self, protected):
        self.controller.set_metadata(self.field, 'protected', protected)

    def is_optional(self):
        return self.controller.is_optional(self.field)

    def inner_value_changed(self, indices):
        self.controller.on_inner_value_change.fire([self.field] + indices)

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
        return f'{self.parent_interaction.get_label()}[{self.index}]'
    
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

    def delete_widgets(self):
        self.parent_interaction.on_change_remove(self.update_gui)
        self.controller_widget.remove_widget_row()
        self.label_widget.deleteLater()
        self.text_widget.deleteLater()
    
    def update_gui(self):
        value = self.parent_interaction.get_value()
        self.text_widget.setText(f'{value}')


class BaseControllerWidget:
    def __init__(self, controller, output=None, user_level=None, depth=0,
                 *args, **kwargs):
        ''' ...

        If output is None (default), both inputs and outputs are displayed.
        Otherwise only inputs (output=False) or outputs (output=True) are.
        '''
        super().__init__(depth=depth, *args, **kwargs)
        self.allow_update_gui = True
        self.depth = depth
        self.controller = controller
        self.output = output
        self.user_level = user_level
        self.build()
        controller.on_inner_value_change.add(self.update_inner_gui)
        controller.on_fields_change.add(self.update_fields)

    def __del__(self):
        # print('del BaseControllerWidget', self)
        self.disconnect()

    def build(self):
        controller = self.controller
        # Select and sort fields
        fields = []
        for field in controller.fields():
            if (
                (self.output is None
                 or (not self.output
                     and not controller.is_output(field))
                 or (self.output
                     and controller.is_output(field)))
                and (self.user_level is None
                     or self.user_level >= controller.metadata(field, 'user_level', 0))
            ):
                fields.append(field)
        self.fields = sorted(fields, key=lambda f: f.metadata.get('order'))
        self.groups = {
            None: self,
        }
        self.factories = {}
        for field in self.fields:
            group = controller.metadata(field, 'group', None)
            group_content_widget = self.groups.get(group)
            if group_content_widget is None:
                group_content_widget = WidgetsGrid(depth=self.depth)
                self.group_widget = GroupWidget(group)

                self.group_widget.layout().addWidget(group_content_widget)
                self.add_widget_row(self.group_widget)
                self.groups[group] = group_content_widget

            type_str = field_type_str(field)
            factory_type = WidgetFactory.find_factory(type_str, DefaultWidgetFactory)
            factory = factory_type(controller_widget=group_content_widget,
                                   parent_interaction=ControllerFieldInteraction(controller, field, self.depth))
            self.factories[field] = factory
            factory.create_widgets()


    def update_inner_gui(self, indices):
        if self.allow_update_gui:
            self.allow_update_gui = False
            field = indices[0]
            indices = indices[1:]
            if indices:
                factory = self.factories[field]
                factory.update_inner_gui(indices)
            self.allow_update_gui = True

    def update_fields(self):
        if self.allow_update_gui:
            self.allow_update_gui = False
            self.clear()
            self.build()
            self.allow_update_gui = True

    def clear(self):
        for field, factory in self.factories.items():
            factory.delete_widgets()
        self.factories = {}
        self.groups = {}
        if hasattr(self, 'group_widget'):
            del self.group_widget
        self.fields = []

    def disconnect(self):
        if hasattr(self, 'controller'):
            self.controller.on_inner_value_change.add(self.update_inner_gui)
            self.controller.on_fields_change.add(self.update_fields)


class ControllerWidget(BaseControllerWidget, ScrollableWidgetsGrid):
    pass


class ControllerSubwidget(BaseControllerWidget, WidgetsGrid):
    pass


class ControllerWidgetFactory(WidgetFactory):
    def create_widgets(self):
        controller = self.parent_interaction.get_value()
        if controller is undefined:
            controller = field_type(self.parent_interaction.field)()
        self.inner_widget = ControllerSubwidget(controller, depth=self.controller_widget.depth + 1)
        label = self.parent_interaction.get_label()
        self.widget = CollapsableWidget(self.inner_widget, label=label, expanded=(self.parent_interaction.depth==0), 
                                        parent=self.controller_widget)
        self.inner_widget.setContentsMargins(self.widget.toggle_button.sizeHint().height(),0,0,0)
      
        self.controller_widget.add_widget_row(self.widget)

    def delete_widgets(self):
        self.controller_widget.remove_widget_row()
        self.widget.deleteLater()
        self.inner_widget.deleteLater()


from .str import StrWidgetFactory
from .bool import BoolWidgetFactory
from .literal import LiteralWidgetFactory
from .list import (ListStrWidgetFactory,
                   ListIntWidgetFactory,
                   ListFloatWidgetFactory,
                   find_generic_list_factory)
from .set import (SetStrWidgetFactory,
                  SetIntWidgetFactory,
                  SetFloatWidgetFactory,
                  find_generic_set_factory)
from .path import FileWidgetFactory, DirectoryWidgetFactory
# Above imports also import the module. This hides
# the corresponding builtins => remove them
del str, bool, literal, list, set, path

WidgetFactory.widget_factory_types = {
    'str': StrWidgetFactory,
    'int': StrWidgetFactory,
    'float': StrWidgetFactory,
    'bool': BoolWidgetFactory,
    'literal': LiteralWidgetFactory,
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
