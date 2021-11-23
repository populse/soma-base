# -*- coding: utf-8 -*-

from soma.controller import (
    field_type_str,
    parse_type_str,
)
from soma.qt_gui.qt_backend import Qt
from .factories import (
    DefaultWidgetFactory,
     WidgetFactory,
     ControllerFieldInteraction,
)
from .collapsable import CollapsableWidget


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


class BaseControllerWidget:
    def __init__(self, controller, output=False, user_level=None, depth=0, *args, **kwargs):
        super().__init__(depth=depth, *args, **kwargs)
        self.depth = depth
        # Select and sort fields
        fields = []
        for field in controller.fields():
            if (
                (output or not controller.metadata(field, 'output', False))
                and (user_level is None or user_level >= controller.metadata(field, 'user_level', 0))
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


class ControllerWidget(BaseControllerWidget, ScrollableWidgetsGrid):
    pass


if __name__ == '__main__':
    import sys

    from soma.undefined import undefined
    from soma.controller import (
        Controller,
        field,
        List,
        Literal,
        file,
        directory,
        Union,
        Dict,
        Set
    ) 
    class MyController(Controller):
        s: str
        i: int
        ls: List[str]

    class C(Controller):
        x: field(type_=List[str])
        y: field(type_=List[str])
        z: field(type_=List[str])
        s: field(type_=str, group='string', label='the label')
        os: field(type_=str, optional=True, group='string')
        ls: field(type_=List[str], group='string')
        ols: field(type_=List[str], output=True, group='string')
        lls: field(type_=List[List[str]], label='list^2[str]', group='string')
        llls: field(type_=List[List[List[str]]], label='list^3[str]', group='string')

        i: field(type_=int, group='integer')
        oi: field(type_=int, optional=True, group='integer')
        li: field(type_=List[int], group='integer')
        oli: field(type_=List[int], output=True, group='integer')
        lli: field(type_=List[List[int]], label='list^2[int]', group='integer')
        llli: field(type_=List[List[List[int]]], label='list^3[int]', group='integer')

        n: field(type_=float, group='float')
        on: field(type_=float, optional=True, group='float')
        ln: field(type_=List[float], group='float') 
        oln: field(type_=List[float], output=True, group='float')
        lln: field(type_=List[List[float]], label='list^2[float]', group='float')
        llln: field(type_=List[List[List[float]]], label='list^3[float]', group='float')

        b: bool
        ob: field(type_=bool, output=True)
        lb: List[bool]
        olb: field(type_=List[bool], output=True)

        e: Literal['one', 'two', 'three']
        oe: field(type_=Literal['one', 'two', 'three'], output=True)
        le: List[Literal['one', 'two', 'three']]
        ole: field(type_=List[Literal['one', 'two', 'three']], output=True)
        
        f: file()
        of: file(write=True)
        lf: List[file()]
        olf: List[file(write=True)]
        
        d: directory()
        od: directory(write=True)
        ld: List[directory()]
        old: List[directory(write=True)]

        u: Union[str, List[str]]
        ou: field(type_=Union[str, List[str]], output=True)
        lu: List[Union[str, List[str]]]
        olu: field(type_=List[Union[str, List[str]]], output=True)

        m: Dict
        om: field(type_=dict, output=True)
        lm: List[dict]
        olm: field(type_=List[dict], output=True)
        mt: Dict[str, List[int]]

        l: list

        controller: field(type_=Controller, group='controller')
        list_controller: field(type_=List[Controller], group='controller')
        custom: field(type_=MyController, group='controller')
        list_custom: field(type_=List[MyController], group='controller')
        list2_custom: field(type_=List[List[MyController]], group='controller')

        Set: Set
        Set_str: Set[str]
        set: set

    app = Qt.QApplication(sys.argv)
    o = C()
    window1 = ControllerWidget(o)
    window1.show()
    window2 = ControllerWidget(o)
    window2.show()
    app.exec_()
    print('o.lli =', getattr(o, 'lli', undefined))

