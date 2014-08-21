# -*- coding: utf-8 -*-
import sipconfig
from soma.qt_gui.qt_backend import QtGui, QtCore
from soma.controller import trait_ids, Controller
from soma.functiontools import partial, SomaPartial
from trait_to_widget import StrCreateWidget, FloatCreateWidget, \
    IntCreateWidget, LongCreateWidget, BoolCreateWidget, EnumCreateWidget, \
    StrEnumCreateWidget, FileCreateWidget, DirectoryCreateWidget
from soma.gui.icon_factory import IconFactory
import weakref


class ControllerWidget(QtGui.QWidget):
    # QPixmap instance cannot be build before a QApplication is being created.
    # (it simply exits the program). But for documentation with epydoc, all
    # modules are loaded without C{QApplication}. Therefore, the creation of
    # the following two static QPixmap instances has been put in __init__.

    _create_widget = {}

    def __init__(self, controller,
                 parent=None, name=None, live=False, hide_labels=False):

        super(ControllerWidget, self).__init__(parent)
        if name:
            self.setObjectName(name)
        self.controller = controller
        self.live = live
        self.connected = False
        self.hide_labels = hide_labels
        self._grid_layout = QtGui.QGridLayout()
        self._grid_layout.setAlignment(QtCore.Qt.AlignTop)
        self._grid_layout.setSpacing(3)
        self._grid_layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(self._grid_layout)

        self.btn_expand = None
        self._widgets = {}
        self._create_widgets()
        if self.live:
            self.connect_controller()
        else:
            self.update_controller_widget()

    def __del__(self):
        self.disconnect_controller()

    def update_controller(self):
        """Update traits when GUI change"""
        for name, tuple in self._widgets.iteritems():
            trait, create_widget, attribute_widget, label_widget = tuple
            create_widget.update_controller(self, name, attribute_widget)

    def update_controller_widget(self):
        """Update GUI when traits change"""
        for name, tuple in self._widgets.iteritems():
            trait, create_widget, attribute_widget, label_widget = tuple
            create_widget.update_controller_widget(
                self,
                name,
                attribute_widget,
                label_widget)

    # def back_default_value(self,attribute_widget,name):
            # print 'here back default value'
            # print self.controller.trait(name)
            # print self.controller.trait(name).defaultvalue
            # setattr( self.controller, name,
                # self.controller.trait(name).defaultvalue )
            # attribute_widget.btn_default_value.setVisible(False)
    def connect_controller(self):
        """
        To connect traits and GUI, use update_controller and
        update controller_widget
        """
        if not self.connected:
            for name, tupl in self._widgets.iteritems():
                trait, create_widget, attribute_widget, label_widget = tupl
                create_widget.connect_controller(
                    self,
                    name,
                    attribute_widget,
                    label_widget)
            self.controller.on_trait_change(
                self.update_widgets,
                'user_traits_changed')
            self.update_controller_widget()
            self.connected = True

    def disconnect_controller(self):
        """To disconnect traits and GUI"""
        if self.connected:
            self.controller.on_trait_change(
                self.update_widgets,
                'user_traits_changed',
                remove=True)
            for name, tupl in self._widgets.iteritems():
                trait, create_widget, attribute_widget, label_widget = tupl
                create_widget.disconnect_controller(
                    self,
                    name,
                    attribute_widget,
                    label_widget)
            self.connected = False

    @classmethod
    def find_create_widget_from_trait(cls, trait):
        """
        Find widget corresponding to the trait, call the corresponding
        create_create widget class
        """
        create_widget = None
        for trait_id in trait_ids(trait):
            for create_widget in cls._create_widget.get(trait_id, []):
                if create_widget.is_valid_trait(trait):
                    break
            else:
                create_widget = None
            if create_widget is not None:
                break
        return create_widget

    def _create_widgets(self):
        # print '!_create_widgets!', self.controller.user_traits().keys()
        for name, trait in self.controller.user_traits().iteritems():
            create_widget = self._widgets.get(name)
            if create_widget is None:
                create_widget = self.find_create_widget_from_trait(trait)
                if not create_widget:
                    continue
                attribute_widget, label_widget = create_widget.create_widget(
                    self, name, trait, getattr(self.controller, name))
                if trait.desc:
                    tooltip = '<b>' + name + ':</b> ' + trait.desc
                else:
                    tooltip = None
                if label_widget is None:
                    self._grid_layout.addWidget(
                        attribute_widget,
                        self._grid_layout.rowCount(),
                        0,
                        1,
                        2)
                    if tooltip:
                        attribute_widget.setToolTip(tooltip)
                elif isinstance(label_widget, tuple):
                    row = self._grid_layout.rowCount()
                    if label_widget[0] and not self.hide_labels:
                        self._grid_layout.addWidget(label_widget[0], row, 0)
                        if tooltip:
                            label_widget[0].setToolTip(tooltip)
                    self._grid_layout.addWidget(label_widget[1], row, 1)
                    if tooltip:
                        label_widget[1].setToolTip(tooltip)
                    self._grid_layout.addWidget(
                        attribute_widget,
                        self._grid_layout.rowCount(),
                        0,
                        1,
                        2)
                else:
                    row = self._grid_layout.rowCount()
                    if self.hide_labels:
                        self._grid_layout.addWidget(
                            attribute_widget,
                            row,
                            0,
                            1,
                            2)
                        if tooltip:
                            attribute_widget.setToolTip(tooltip)
                    else:
                        self._grid_layout.addWidget(label_widget, row, 0)
                        self._grid_layout.addWidget(attribute_widget, row, 1)
                        # btn_default_value = QtGui.QPushButton()
                        # btn_default_value.setIcon( QtGui.QIcon(
                            # IconFactory()._valueModified) )
                        # btn_default_value.setVisible(False)
                        # attribute_widget.btn_default_value = btn_default_value
                        # self._grid_layout.addWidget( btn_default_value,row,2
                        # )
                        if tooltip:
                            label_widget.setToolTip(tooltip)
                            attribute_widget.setToolTip(tooltip)
                self._widgets[name] = (
                    trait,
                    create_widget,
                    attribute_widget,
                    label_widget)
            else:
                trait, create_widget, attribute_widget, label_widget \
                    = create_widget
            if getattr(trait, 'hidden', False):
                attribute_widget.hide()
                if label_widget:
                    if isinstance(label_widget, tuple):
                        l = label_widget
                    else:
                        l = [label_widget]
                    for i in l:
                        i.hide()
            else:
                attribute_widget.show()
                if label_widget:
                    if isinstance(label_widget, tuple):
                        l = label_widget
                    else:
                        l = [label_widget]
                    for i in l:
                        i.show()

    def update_widgets(self):
        user_traits = self.controller.user_traits()
        was_connected = self.connected
        if was_connected:
            self.disconnect_controller()
        for name in self._widgets.keys():
            trait, create_widget, attribute_widget, label_widget \
                = self._widgets[name]
            if user_traits.get(name) != trait:
                attribute_widget.close()
                attribute_widget.deleteLater()
                if isinstance(label_widget, tuple):
                    if label_widget[0]:
                        label_widget[0].close()
                        label_widget[0].deleteLater()
                    if label_widget[1]:
                        label_widget[1].close()
                        label_widget[1].deleteLater()
                elif label_widget:
                    label_widget.close()
                    label_widget.deleteLater()
                del self._widgets[name]
        self._create_widgets()
        if was_connected:
            self.connect_controller()
        self.updateGeometry()


#-------------------------------------------------------------------------
class ListCreateWidget(object):

    class ListController(Controller):
        pass

    @staticmethod
    def is_valid_trait(trait):
        item_trait = trait.inner_traits[0]
        create_widget = ControllerWidget.find_create_widget_from_trait(
            item_trait)
        return create_widget is not None

    @classmethod
    def create_widget(cls, parent, name, trait, value):
        item_trait = trait.inner_traits[0]
        # print '!ListCreateWidget!', name, 'List( %s )' % trait_ids(
        # item_trait )
        list_controller = cls.ListController()
        for i in xrange(len(value)):
            list_controller.add_trait(str(i), item_trait)
            trait = list_controller.trait(str(i))
            trait.order = i
            setattr(list_controller, str(i), value[i])
        result = ControllerCreateWidget.create_widget(
            parent, name, None, list_controller)
        attribute_widget = result[0]
        attribute_widget.controller_widget.connect_controller()
        attribute_widget.item_trait = item_trait
        attribute_widget.list_controller = list_controller
        attribute_widget.connected = False
        return result

    @staticmethod
    def update_controller(controller_widget, name, attribute_widget):
        items = [getattr(attribute_widget.list_controller, str(i))
                 for i in
                 xrange(len(attribute_widget.list_controller.user_traits()))]
        # print '!update_controller!', name, len( items ), items
        setattr(controller_widget.controller, name, items)

    @classmethod
    def update_controller_widget(
            cls, controller_widget, name, attribute_widget, label_widget):
        was_connected = attribute_widget.connected
        cls.disconnect_controller(
            controller_widget,
            name,
            attribute_widget,
            label_widget)
        attribute_widget.controller_widget.disconnect_controller()
        items = getattr(controller_widget.controller, name)
        len_widget = len(attribute_widget.list_controller.user_traits())
        # print '!update_controller_widget!', name, len_widget, items
        user_traits_changed = False
        if len(items) < len_widget:
            for i in xrange(len(items), len_widget):
                attribute_widget.list_controller.remove_trait(str(i))
            user_traits_changed = True
        elif len(items) > len_widget:
            for i in xrange(len_widget, len(items)):
                attribute_widget.list_controller.add_trait(
                    str(i), attribute_widget.item_trait)
                trait = attribute_widget.list_controller.trait(str(i))
                trait.order = i
            user_traits_changed = True
        for i in xrange(len(items)):
            setattr(attribute_widget.list_controller, str(i), items[i])
        # print '!update_controller_widget! done', name
        attribute_widget.controller_widget.connect_controller()
        if user_traits_changed:
            attribute_widget.list_controller.user_traits_changed = True
        if was_connected:
            cls.connect_controller(
                controller_widget,
                name,
                attribute_widget,
                label_widget)

    @classmethod
    def connect_controller(
            cls, controller_widget, name, attribute_widget, label_widget):
        if not attribute_widget.connected:
            def list_controller_hook(obj, key, old, new):
                # print '!list_controller_hook!', ( obj, key, old, new )
                items = getattr(controller_widget.controller, name)
                items[int(key)] = new
            for n in attribute_widget.list_controller.user_traits():
                attribute_widget.list_controller.on_trait_change(
                    list_controller_hook, n)
            controller_hook = SomaPartial(
                cls.update_controller_widget,
                weakref.proxy(controller_widget), name, attribute_widget,
                label_widget)
            controller_widget.controller.on_trait_change(
                controller_hook, name + '[]')
            attribute_widget._controller_connections = (
                list_controller_hook, controller_hook)
            attribute_widget.connected = True

    @staticmethod
    def disconnect_controller(
            controller_widget, name, attribute_widget, label_widget):
        if attribute_widget.connected:
            list_controller_hook, controller_hook \
                = attribute_widget._controller_connections
            controller_widget.controller.on_trait_change(
                controller_hook, name + '[]', remove=True)
            for n in attribute_widget.list_controller.user_traits():
                attribute_widget.list_controller.on_trait_change(
                    list_controller_hook, n, remove=True)
            del attribute_widget._controller_connections
            attribute_widget.connected = False


#-------------------------------------------------------------------------
class ControllerCreateWidget(object):

    """Class for instance trait"""
    @staticmethod
    def is_valid_trait(trait):
        return True

    @classmethod
    def create_widget(cls, parent, name, trait, sub_controller):
        label = getattr(trait, 'label', None)
        if not label:
            label = name
        if label is not None:
            label_widget = QtGui.QLabel(label, parent)
        else:
            label_widget = None

        btn_expand = QtGui.QPushButton(parent)
        btn_expand.setIcon(QtGui.QIcon(IconFactory()._imageExpand))

        scroll_area = QtGui.QScrollArea(parent=parent)
        scroll_area.setWidgetResizable(True)
        # scroll_area.setSizePolicy( QtGui.QSizePolicy(
            # QtGui.QSizePolicy.Expanding,
            # QtGui.QSizePolicy.Expanding
            # ) )
        sub_controller_widget = ControllerWidget(sub_controller,
                                                 parent=scroll_area)
        scroll_area.setWidget(sub_controller_widget)
        # sub_controller_widget.setSizePolicy( QtGui.QSizePolicy(
            # QtGui.QSizePolicy.Expanding,
            # QtGui.QSizePolicy.MinimumExpanding
            # ) )
        scroll_area.setFrameShape(QtGui.QFrame.StyledPanel)
        expand_hook = partial(cls.expand_collapse, scroll_area)
        btn_expand.connect(btn_expand, QtCore.SIGNAL('clicked()'),
                           expand_hook)
        attribute_widget = scroll_area
        attribute_widget.btn_expand = btn_expand
        attribute_widget.label_widget = label_widget
        attribute_widget.expand_hook = expand_hook
        scroll_area.hide()
        attribute_widget.controller_widget = sub_controller_widget
        return (attribute_widget, (label_widget, btn_expand))

    @staticmethod
    def update_controller(controller_widget, name, attribute_widget):
        attribute_widget.controller_widget.update_controller()

    @staticmethod
    def update_controller_widget(
            controller_widget, name, attribute_widget, label_widget):
        attribute_widget.controller_widget.update_controller_widget()

    @staticmethod
    def connect_controller(
            controller_widget, name, attribute_widget, label_widget):
        attribute_widget.controller_widget.connect_controller()

    @staticmethod
    def disconnect_controller(
            controller_widget, name, attribute_widget, label_widget):
        attribute_widget.controller_widget.disconnect_controller()

    @staticmethod
    def expand_collapse(attribute_widget):
        if attribute_widget.isVisible():
            attribute_widget.hide()
            attribute_widget.btn_expand.setIcon(
                QtGui.QIcon(IconFactory()._imageExpand))
        else:
            attribute_widget.show()
            attribute_widget.btn_expand.setIcon(
                QtGui.QIcon(IconFactory()._imageCollapse))


ControllerWidget._create_widget['Str'] = [StrCreateWidget]
ControllerWidget._create_widget['Unicode'] = [StrCreateWidget]
ControllerWidget._create_widget['Float'] = [FloatCreateWidget]
ControllerWidget._create_widget['Int'] = [IntCreateWidget]

ControllerWidget._create_widget['Long'] = [LongCreateWidget]
ControllerWidget._create_widget['Bool'] = [BoolCreateWidget]

ControllerWidget._create_widget['Enum'] = [EnumCreateWidget]
ControllerWidget._create_widget['Str'].insert(0, StrEnumCreateWidget)
ControllerWidget._create_widget['Unicode'].insert(0, StrEnumCreateWidget)
ControllerWidget._create_widget['File'] = [FileCreateWidget]
ControllerWidget._create_widget['Directory'] = [DirectoryCreateWidget]
ControllerWidget._create_widget[
    'Instance_Controller'] = [
    ControllerCreateWidget]
ControllerWidget._create_widget['Any'] = [StrCreateWidget]

ControllerWidget._create_widget['List_Str'] = [ListCreateWidget]
ControllerWidget._create_widget['List_Float'] = [ListCreateWidget]
ControllerWidget._create_widget['List_Int'] = [ListCreateWidget]
ControllerWidget._create_widget['List_Long'] = [ListCreateWidget]
ControllerWidget._create_widget['List_Bool'] = [ListCreateWidget]
ControllerWidget._create_widget['List_Enum'] = [ListCreateWidget]
ControllerWidget._create_widget['List_Directory'] = [ListCreateWidget]
ControllerWidget._create_widget['List_File'] = [ListCreateWidget]
ControllerWidget._create_widget['List_Any'] = [ListCreateWidget]


#-------------------------------------------------------------------------------
# if __name__ == '__main__':
    # import sys
    # try:
        # from traits.api import Str, Unicode, Float, Int, Long, Bool, Enum, Directory, File, Instance, List
    # except:
        # from enthought.traits.api import Str, Unicode, Float, Int, Long, Bool, Enum, Directory, File, Instance, List
    # from soma.controller import Controller

    # app = QtGui.QApplication( sys.argv )

    # class InstanceTraits( Controller ):
        # def __init__( self ):
            # self.add_trait( 'str', Str( desc='This is a string', order=1, viewer='viewers.image.ImageViewer' ) )
            # self.add_trait( 'str2', Str( desc='This is a String', order=2 ) )
            # self.add_trait( 'unicode', Str( desc='This is a unicode', order=2 ) )
            # self.add_trait( 'float', Float( desc='This is a float', order=3 ) )
            # self.add_trait( 'int', Int( desc='This is an int', order=4 ) )
            # self.add_trait( 'long', Long( desc='This is a long', order=5 ) )
            # self.add_trait( 'bool', Bool( desc='This is a boolean.', order=6 ) )
            # self.add_trait( 'enum', Enum( 'first value', 'second value', 'third value', desc='This is an enum.', order=7 ) )
            # self.add_trait( 'str_enum', Str( desc='This is a StrEnum', values=( 'first value', 'second value', 'third value' ), order=8 ) )
            # self.add_trait( 'directory', Directory( desc='This is a directory.', order=9 ) )
            # self.add_trait( 'file', File( desc='This is a file.', order=10 )
            # )

            # self.add_trait( 'list_str', List( Str, desc='This is a string list', order=11 ) )
            # self.add_trait( 'list_unicode', List( Unicode, desc='This is a unicode list', order=12 ) )
            # self.add_trait( 'list_float', List( Float, desc='This is a float list', order=13 ) )
            # self.add_trait( 'list_int', List( Int, desc='This is an int list', order=14 ) )
            # self.add_trait( 'list_long', List( Long, desc='This is a long list', order=15 ) )
            # self.add_trait( 'list_bool', List( Bool, desc='This is a boolean list', order=16 ) )
            # self.add_trait( 'list_enum', List( Enum( 'first value', 'second value', 'third value' ), desc='This is an enum list', order=17 ) )
            # self.add_trait( 'list_str_enum', List( Str( values=( 'first value', 'second value', 'third value' ) ), desc='This is a StrEnum list', order=18 ) )
            # self.add_trait( 'list_directory', List( Directory, desc='This is a directory list', order=19 ) )
            # self.add_trait( 'list_file', List( File, desc='This is a file
            # list', order=20 ) )



    # class WidgetOnGui( Controller ):
        # lists_size = Int( 0, order=0, desc='Resize all the lists' )
        # connected = Bool( default_value=True, order=1, desc='Disconnect one of the two widgets' )
        # traits_on_class = Instance( ClassTraits, desc='All traits on this attribute are defined on class', order=2 )
        # traits_on_instance0 = Instance( InstanceTraits, desc='All traits on this attribute are defined on class', order=2 )
        # traits_on_instance = Instance( SimpMorpho, desc='All traits on this
        # attribute are defined on instance', order=3 )


        # def __init__( self ):
            # super( WidgetOnGui, self ).__init__()
            # self.traits_on_class = ClassTraits()
            # self.traits_on_instance0 = InstanceTraits()
            # self.traits_on_instance = SimpMorpho()
            # self.dummy = 'I am hidden'


        # def on_run(self):
            # print 'IN THE FUNCTION RUN'
            # self.traits_on_instance()






    # def resize( main, old, new ):
        # for o in ( main.traits_on_class, main.traits_on_instance ):
        # for o in main.traits_on_instance :
            # for a in ( 'list_str', 'list_unicode', 'list_float', 'list_int', 'list_long', 'list_bool', 'list_enum', 'list_str_enum', 'list_directory', 'list_file' ):
                        # list = getattr( o, a )
                # len_list = len( list )
                # if main.lists_size > len_list:
                    # print '!resize! + ', a, len_list, main.lists_size, list + [ o.trait( a ).inner_traits[0].default ] * ( main.lists_size - len_list )
                    # setattr( o, a, list + [ o.trait( a ).inner_traits[0].default ] * ( main.lists_size - len_list ) )
                    # print '!resize! done'
                # elif main.lists_size < len_list:
                    # print '!resize! - ', a, len_list, main.lists_size
                    # setattr( o, a, list[ : main.lists_size ] )
                    # print '!resize! done'

    # def f( connected ):
        # print '!f!', connected
        # if connected:
            # w1.connect_controller()
        # else:
            # w1.disconnect_controller()
    # o.on_trait_change( f, 'connected' )


    # w2 = ControllerWidget( o, live=True )
    # w2.show()

    # def f(object,name,old,new ):
        # print 'in f'
        # print ( object,name,old,new )

    # o.traits_on_instance.on_trait_change( f )
    # o.on_trait_change( resize, 'lists_size' )
    # app.exec_()


    # w1.on_trait_change(update,'t1mri')

    # def update(object,name,old,new):
            # o.traits_on_instance._t1mri_changed()
