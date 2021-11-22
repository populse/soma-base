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
    def __init__(self, *args, **kwargs):
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
    def __init__(self, *args, **kwargs):
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


class BaseControllerWidget:
    def __init__(self, controller, output=False, user_level=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
                group_content_widget = WidgetsGrid()
                group_content_widget.setFrameShape(Qt.QFrame.Box)
                group_widget = CollapsableWidget(group_content_widget, group,
                                                    expanded=True)
                self.add_widget_row(group_widget)
                self.groups[group] = group_content_widget

            type_str = field_type_str(field)
            factory_type = WidgetFactory.find_factory(type_str, DefaultWidgetFactory)
            factory = factory_type(controller_widget=group_content_widget, 
                                   parent_interaction=ControllerFieldInteraction(controller, field))
            self.factories[field] = factory
            factory.create_widgets()


class ControllerWindow(BaseControllerWidget, ScrollableWidgetsGrid):
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
        s: field(type_=str, group='string', label='string')
        os: field(type_=str, optional=True, group='string')
        ls: field(type_=List[str], group='string')
        ols: field(type_=List[str], output=True, group='string')

        i: field(type_=int, group='integer')
        oi: field(type_=int, optional=True, group='integer')
        li: field(type_=List[int], group='integer')
        oli: field(type_=List[int], output=True, group='integer')

        n: float
        on: field(type_=float, optional=True)
        ln: List[float]
        oln: field(type_=List[float], output=True)

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
        lls: List[List[str]]
        lli: List[List[int]]

        c: Controller
        lc: List[Controller]
        o: MyController
        lo: List[MyController]

        Set: Set
        Set_str: Set[str]
        set: set

    app = Qt.QApplication(sys.argv)
    o = C()
    window1 = ControllerWindow(o)
    window1.show()
    window2 = ControllerWindow(o)
    window2.show()
    app.exec_()
    print('o.lli =', getattr(o, 'lli', undefined))

