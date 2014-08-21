# -*- coding: utf-8 -*-
import sipconfig
from soma.qt_gui.qt_backend import QtGui, QtCore
from soma.controller import trait_ids, Controller
from soma.utils.functiontools import partial, SomaPartial
from soma.qt4gui.api import TimeredQLineEdit
from soma.global_naming import GlobalNaming
from soma.gui.icon_factory import IconFactory
try:
    from traits.api import File, Directory
except ImportError:
    from enthought.traits.api import File, Directory
import weakref


#-------------------------------------------------------------------------
class StrCreateWidget(object):

    @staticmethod
    def is_valid_trait(trait):
        return True

    @staticmethod
    def create_widget(parent, name, trait, value):
        attribute_widget = TimeredQLineEdit(parent)
        label = trait.label
        if not label:
            label = name
        if label is not None:
            label_widget = QtGui.QLabel(label, parent)
        else:
            label_widget = None

        return (attribute_widget, label_widget)

    @staticmethod
    def update_controller(controller_widget, name, attribute_widget):
        """GUI modified so update traits"""
        if isinstance(attribute_widget, TimeredQLineEdit):
            try:
                setattr(
                    controller_widget.controller,
                    name,
                    unicode(attribute_widget.text()))
            except:
                print 'Warning - StrCreateWidget.update_controller: controller widget set failure'
        else:
            setattr(
                controller_widget.controller,
                name,
                unicode(attribute_widget.text_widget.text()))

    @staticmethod
    def update_controller_widget(
            controller_widget, name, attribute_widget, label_widget):
        """Traits modified so update GUI"""
        if isinstance(attribute_widget, TimeredQLineEdit):
            attribute_widget.setText(
                unicode(getattr(controller_widget.controller, name, '')))
        else:
            attribute_widget.text_widget.setText(
                unicode(getattr(controller_widget.controller, name, '')))

    @classmethod
    def connect_controller(
            cls, controller_widget, name, attribute_widget, label_widget):
        widget_hook = partial(cls.update_controller,
                              weakref.proxy(controller_widget), name,
                              attribute_widget)
        if isinstance(attribute_widget, TimeredQLineEdit):
            attribute_widget.userModification.connect(widget_hook)
        else:
            attribute_widget.text_widget.userModification.connect(widget_hook)

        controller_hook = SomaPartial(cls.update_controller_widget,
                                      weakref.proxy(controller_widget), name,
                                      attribute_widget,
                                      label_widget)
        controller_widget.controller.on_trait_change(
            controller_hook, name=name)
        attribute_widget._controller_connections = (
            widget_hook, controller_hook)

    @staticmethod
    def disconnect_controller(
            controller_widget, name, attribute_widget, label_widget):
        widget_hook, controller_hook = attribute_widget._controller_connections
        controller_widget.controller.on_trait_change(
            controller_hook, name=name, remove=True)
        if isinstance(attribute_widget, TimeredQLineEdit):
            attribute_widget.userModification.disconnect(widget_hook)
        else:
            attribute_widget.text_widget.userModification.disconnect(
                widget_hook)
        del attribute_widget._controller_connections


#-------------------------------------------------------------------------
class FloatCreateWidget(StrCreateWidget):

    @staticmethod
    def update_controller(controller_widget, name, attribute_widget):
        setattr(
            controller_widget.controller,
            name,
            float(attribute_widget.text()))

    @staticmethod
    def update_controller_widget(
            controller_widget, name, attribute_widget, label_widget):
        attribute_widget.setText(
            unicode(getattr(controller_widget.controller, name, 0)))


#-------------------------------------------------------------------------
class IntCreateWidget(FloatCreateWidget):

    @staticmethod
    def update_controller(controller_widget, name, attribute_widget):
        setattr(
            controller_widget.controller,
            name,
            int(attribute_widget.text()))


#-------------------------------------------------------------------------
class LongCreateWidget(FloatCreateWidget):

    @staticmethod
    def update_controller(controller_widget, name, attribute_widget):
        setattr(
            controller_widget.controller,
            name,
            long(attribute_widget.text()))


#-------------------------------------------------------------------------
class BoolCreateWidget(object):

    @staticmethod
    def is_valid_trait(trait):
        return True

    @staticmethod
    def create_widget(parent, name, trait, value):
        attribute_widget = QtGui.QCheckBox(parent)
        label = trait.label
        if not label:
            label = name
        if label is not None:
            label_widget = QtGui.QLabel(label, parent)
        else:
            label_widget = None
        return (attribute_widget, label_widget)

    @staticmethod
    def update_controller(controller_widget, name, attribute_widget):
        setattr(
            controller_widget.controller,
            name,
            bool(attribute_widget.isChecked()))

    @staticmethod
    def update_controller_widget(
            controller_widget, name, attribute_widget, label_widget):
        attribute_widget.setChecked(
            getattr(
                controller_widget.controller,
                name,
                False))

    @classmethod
    def connect_controller(
            cls, controller_widget, name, attribute_widget, label_widget):
        widget_hook = partial(cls.update_controller,
                              weakref.proxy(controller_widget), name,
                              attribute_widget)
        attribute_widget.clicked.connect(widget_hook)
        controller_hook = SomaPartial(cls.update_controller_widget,
                                      weakref.proxy(controller_widget), name,
                                      attribute_widget,
                                      label_widget)
        controller_widget.controller.on_trait_change(
            controller_hook, name=name)
        attribute_widget._controller_connections = (
            widget_hook, controller_hook)

    @staticmethod
    def disconnect_controller(
            controller_widget, name, attribute_widget, label_widget):
        widget_hook, controller_hook = attribute_widget._controller_connections
        controller_widget.controller.on_trait_change(
            controller_hook, name=name, remove=True)
        attribute_widget.clicked.disconnect(widget_hook)
        del attribute_widget._controller_connections


#-------------------------------------------------------------------------
class EnumCreateWidget(object):

    @staticmethod
    def is_valid_trait(trait):
        return True

    @staticmethod
    def create_widget(parent, name, trait, value):
        attribute_widget = QtGui.QComboBox(parent)
        values = trait.handler.values
        labels = getattr(trait, 'labels')
        if not labels:
            labels = ()
        labels += (None, ) * (len(values) - len(labels))
        labels = [(unicode(value) if label is None else label)
                  for value, label in zip(values, labels)]
        attribute_widget._values = values
        for label in labels:
            attribute_widget.addItem(label)
        label = trait.label
        if not label:
            label = name
        if label is not None:
            label_widget = QtGui.QLabel(label, parent)
        else:
            label_widget = None
        return (attribute_widget, label_widget)

    @staticmethod
    def update_controller(controller_widget, name, attribute_widget, value):
        # default_value_change(getattr(controller_widget.controller,name),attribute_widget._values[
        # attribute_widget.currentIndex() ],attribute_widget.btn_default_value)
        setattr(
            controller_widget.controller,
            name,
            attribute_widget._values[attribute_widget.currentIndex()])

    @staticmethod
    def update_controller_widget(
            controller_widget, name, attribute_widget, label_widget):
        label = getattr(controller_widget.controller, name, None)
        if label is not None:
            attribute_widget.setCurrentIndex(
                attribute_widget._values.index(label))

    @classmethod
    def connect_controller(
            cls, controller_widget, name, attribute_widget, label_widget):
        widget_hook = partial(cls.update_controller,
                              weakref.proxy(controller_widget), name,
                              attribute_widget)
        attribute_widget.activated.connect(widget_hook)
        controller_hook = SomaPartial(cls.update_controller_widget,
                                      weakref.proxy(controller_widget), name,
                                      attribute_widget,
                                      label_widget)
        controller_widget.controller.on_trait_change(
            controller_hook, name=name)
        attribute_widget._controller_connections = (
            widget_hook, controller_hook)

    @staticmethod
    def disconnect_controller(
            controller_widget, name, attribute_widget, label_widget):
        widget_hook, controller_hook = attribute_widget._controller_connections
        controller_widget.controller.on_trait_change(
            controller_hook, name=name, remove=True)
        attribute_widget.activated.disconnect(widget_hook)
        del attribute_widget._controller_connections


#-------------------------------------------------------------------------
class StrEnumCreateWidget(object):

    @staticmethod
    def is_valid_trait(trait):
        return trait.values is not None

    @staticmethod
    def create_widget(parent, name, trait, value):
        values = list(trait.values)
        if trait.labels:
            raise ValueError('labels is not allowed for Str with values')
        attribute_widget = QtGui.QComboBox(parent)
        attribute_widget.setEditable(True)
        attribute_widget._values = values
        for label in values:
            attribute_widget.addItem(label)
        label = trait.label
        if not label:
            label = name
        if label is not None:
            label_widget = QtGui.QLabel(label, parent)
        else:
            label_widget = None
        return (attribute_widget, label_widget)

    @staticmethod
    def update_controller(controller_widget, name, attribute_widget, value):
        setattr(
            controller_widget.controller,
            name,
            unicode(attribute_widget.currentText()))

    @staticmethod
    def update_controller_widget(
            controller_widget, name, attribute_widget, label_widget):
        value = getattr(controller_widget.controller, name, '')
        try:
            index = attribute_widget._values.index(value)
        except ValueError:
            index = -1
        if index != -1:
            attribute_widget.setCurrentIndex(index)
        else:
            attribute_widget.setEditText(value)

    @classmethod
    def connect_controller(
            cls, controller_widget, name, attribute_widget, label_widget):
        widget_hook = partial(cls.update_controller,
                              weakref.proxy(controller_widget), name,
                              attribute_widget)
        attribute_widget.editTextChanged.connect(widget_hook)
        controller_hook = SomaPartial(cls.update_controller_widget,
                                      weakref.proxy(controller_widget), name,
                                      attribute_widget,
                                      label_widget)
        controller_widget.controller.on_trait_change(
            controller_hook, name=name)
        attribute_widget._controller_connections = (
            widget_hook, controller_hook)

    @staticmethod
    def disconnect_controller(
            controller_widget, name, attribute_widget, label_widget):
        widget_hook, controller_hook = attribute_widget._controller_connections
        controller_widget.controller.on_trait_change(
            controller_hook, name=name, remove=True)
        attribute_widget.editTextChanged.disconnect(widget_hook)
        del attribute_widget._controller_connections


#-------------------------------------------------------------------------
class FileCreateWidget(object):

    @staticmethod
    def is_valid_trait(trait):
        return True

    @classmethod
    def create_widget(cls, parent, name, trait, value):
        text_widget, label_widget = StrCreateWidget.create_widget(
            parent, name, trait, value)
        attribute_widget = QtGui.QWidget(parent)
        horizontal_layout = QtGui.QHBoxLayout(attribute_widget)
        horizontal_layout.setContentsMargins(0, 0, 0, 0)
        horizontal_layout.addWidget(text_widget)
        attribute_widget.text_widget = text_widget

        btn_browse = QtGui.QPushButton(attribute_widget)
        if trait.output is True:
            btn_browse.setIcon(QtGui.QIcon(IconFactory()._imageBrowseOutput))
        if trait.output is False:
            btn_browse.setIcon(QtGui.QIcon(IconFactory()._imageBrowseInput))
        if trait(name).is_trait_type(Directory):
            btn_browse.setIcon(QtGui.QIcon(IconFactory()._imageBrowseDir))
        horizontal_layout.addWidget(btn_browse)
        btn_browse.setFixedSize(20, 20)
        attribute_widget.btn_browse = btn_browse
        attribute_widget._browse_hook = partial(
            cls.file_dialog, weakref.proxy(parent), name,
            weakref.proxy(attribute_widget))
        attribute_widget.btn_browse.clicked.connect(
            attribute_widget._browse_hook)

        viewers = getattr(parent.controller, 'viewers', None)
        if viewers and name in viewers:
            btn_viewer = QtGui.QPushButton(attribute_widget)
            horizontal_layout.addWidget(btn_viewer)
            btn_viewer.setFixedSize(20, 20)
            btn_viewer.setIcon(QtGui.QIcon(IconFactory()._imageViewer))
            attribute_widget.btn_viewer = btn_viewer
            if hasattr(parent.controller, 'call_viewer'):
                viewer_hook = partial(
                    parent.controller.call_viewer,
                    parent,
                    name)
                attribute_widget._viewer_hook = viewer_hook
                attribute_widget.btn_viewer.clicked.connect(viewer_hook)
        return (attribute_widget, label_widget)

    @staticmethod
    def file_dialog(parent, name, attribute_widget):
        if hasattr( parent.controller.user_traits()[name], 'output' ) \
                and parent.controller.user_traits()[name].output:
            outputfile = True
        else:
            outputfile = False
        if sipconfig.Configuration().sip_version >= 0x040a00:
            #/nfs/neurospin/cati/cati_shared/MEMENTO/CONVERTED/001/0010020_LAFR/M000/MRI/3DT1/0010020_LAFR_M000_3DT1_S002.nii.gz
                #''
            if not outputfile:
                value = QtGui.QFileDialog.getOpenFileName(
                    parent, 'Select a file', '', '',
                    options=QtGui.QFileDialog.DontUseNativeDialog)
            else:
                value = QtGui.QFileDialog.getSaveFileName(
                    parent, 'Select a file', '', '',
                    options=QtGui.QFileDialog.DontUseNativeDialog)
        else:
            if outputfile:
                value = QtGui.QFileDialog.getOpenFileName(
                    self._widget, 'Select a file', '', '',
                    0, QtGui.QFileDialog.DontUseNativeDialog)
            else:
                value = QtGui.QFileDialog.getSaveFileName(
                    self._widget, 'Select a file', '', '',
                    0, QtGui.QFileDialog.DontUseNativeDialog)
        setattr(parent.controller, name, unicode(value))

    @staticmethod
    def update_viewer(controller_widget, name, attribute_widget):
        if hasattr(controller_widget.controller, 'viewers'):
            if name in controller_widget.controller.viewers:
                try:
                    open(getattr(controller_widget.controller, name))
                    attribute_widget.btn_viewer.setEnabled(True)
                except IOError:
                    attribute_widget.btn_viewer.setEnabled(False)

    @staticmethod
    def update_controller(controller_widget, name, attribute_widget):
        """GUI modified so update traits"""
        StrCreateWidget.update_controller(
            controller_widget,
            name,
            attribute_widget.text_widget)
        # StrCreateWidget.update_controller( controller_widget, name,
        # attribute_widget)

    @staticmethod
    def update_controller_widget(
            controller_widget, name, attribute_widget, label_widget):
        """Traits modified so update GUI"""
        StrCreateWidget.update_controller_widget(
            controller_widget,
            name,
            attribute_widget.text_widget,
            label_widget)
        # StrCreateWidget.update_controller_widget( controller_widget, name,
        # attribute_widget, label_widget )

        # To disable viewer if file doesn't exist
        # if controller_widget.controller.trait( name ).viewer is not None:
        if hasattr(controller_widget.controller, 'viewers'):
            if name in controller_widget.controller.viewers:
                try:
                    open(getattr(controller_widget.controller, name))
                    attribute_widget.btn_viewer.setEnabled(True)
                except IOError:
                    attribute_widget.btn_viewer.setEnabled(False)

    @classmethod
    def connect_controller(
            cls, controller_widget, name, attribute_widget, label_widget):
        # StrCreateWidget.connect_controller( controller_widget, name,
        # attribute_widget.text_widget, label_widget )
        StrCreateWidget.connect_controller(
            controller_widget,
            name,
            attribute_widget.text_widget,
            label_widget)

        # Function call when traits change to update if viewer enabled or not
        controller_hook = SomaPartial(cls.update_viewer,
                                      weakref.proxy(controller_widget), name,
                                      attribute_widget)
        controller_widget.controller.on_trait_change(controller_hook, name)

        attribute_widget._controller_connections = controller_hook

    @staticmethod
    def disconnect_controller(
            controller_widget, name, attribute_widget, label_widget):
        controller_hook = attribute_widget._controller_connections
        controller_widget.controller.on_trait_change(
            controller_hook, name, remove=True)
        StrCreateWidget.disconnect_controller(
            controller_widget,
            name,
            attribute_widget.text_widget,
            label_widget)
        del attribute_widget._controller_connections


#-------------------------------------------------------------------------
class DirectoryCreateWidget(FileCreateWidget):

    @staticmethod
    def file_dialog(controller_widget, name, attribute_widget):
        value = QtGui.QFileDialog.getExistingDirectory(
            controller_widget, 'Select a directory', '',
            options=QtGui.QFileDialog.ShowDirsOnly | QtGui.QFileDialog.DontUseNativeDialog)
        setattr(controller_widget.controller, name, unicode(value))


def find_function_viewer(name_viewer):
    return GlobalNaming().get_object(name_viewer)


# def default_value_change(old,new,btn):
        # if old !=new:
                # btn.setVisible(True)
