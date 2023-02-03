# -*- coding: utf-8 -*-
#
# SOMA - Copyright (C) CEA, 2015
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
#

# System import
from __future__ import print_function

from __future__ import absolute_import
import os
import logging
import six
from six.moves import range

# Define the logger
logger = logging.getLogger(__name__)

# Soma import
from soma.qt_gui import qt_backend
from soma.qt_gui.qt_backend import QtGui, QtCore
from soma.utils.functiontools import SomaPartial, partial
from soma.controller import trait_ids
from soma.controller import Controller
from soma.qt_gui.controller_widget import ControllerWidget, \
    ScrollControllerWidget, get_ref, weak_proxy

from .List import ListControlWidget, ListController
import traits.api as traits
import weakref
import sip

# Qt import
try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

QtCore.QResource.registerResource(os.path.join(os.path.dirname(
    os.path.dirname(__file__)), 'resources', 'widgets_icons.rcc'))


class OffscreenListControlWidget(object):

    """ Control to enter a list of items.
    """

    #
    # Public members
    #

    max_items = 5

    @staticmethod
    def is_valid(control_instance, *args, **kwargs):
        """ Method to check if the new control values are correct.

        If the new list controls values are not correct, the backroung
        color of each control in the list will be red.

        Parameters
        ----------
        control_instance: QFrame (mandatory)
            the control widget we want to validate

        Returns
        -------
        valid: bool
            True if the control values are valid,
            False otherwise
        """
        # Initilaized the output
        valid = True

        return valid

    @classmethod
    def check(cls, control_instance):
        """ Check if a controller widget list control is filled correctly.

        Parameters
        ----------
        cls: OffscreenListControlWidget (mandatory)
            an OffscreenListControlWidget control
        control_instance: QFrame (mandatory)
            the control widget we want to validate
        """
        pass

    @staticmethod
    def add_callback(callback, control_instance):
        """ Method to add a callback to the control instance when the list
        trait is modified

        Parameters
        ----------
        callback: @function (mandatory)
            the function that will be called when a 'textChanged' signal is
            emited.
        control_instance: QFrame (mandatory)
            the control widget we want to validate
        """
        pass

    @staticmethod
    def create_widget(parent, control_name, control_value, trait,
                      label_class=None, user_data=None):
        """ Method to create the list widget.

        Parameters
        ----------
        parent: QWidget (mandatory)
            the parent widget
        control_name: str (mandatory)
            the name of the control we want to create
        control_value: list of items (mandatory)
            the default control value
        trait: Tait (mandatory)
            the trait associated to the control
        label_class: Qt widget class (optional, default: None)
            the label widget will be an instance of this class. Its constructor
            will be called using 2 arguments: the label string and the parent
            widget.

        Returns
        -------
        out: 2-uplet
            a two element tuple of the form (control widget: ,
            associated labels: (a label QLabel, the tools QWidget))
        """
        # Get the inner trait: expect only one inner trait
        # note: trait.inner_traits might be a method (ListInt) or a tuple
        # (List), whereas trait.handler.inner_trait is always a method
        if len(trait.handler.inner_traits()) != 1:
            raise Exception(
                "Expect only one inner trait in List control. Trait '{0}' "
                "inner trait is '{1}'.".format(
                    control_name, trait.handler.inner_traits()))
        inner_trait = trait.handler.inner_traits()[0]

        # Create the widget
        frame = QtGui.QFrame()
        frame.setFrameShape(QtGui.QFrame.StyledPanel)
        frame.user_data = user_data
        layout = QtGui.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        frame.setLayout(layout)
        #item = QtGui.QLabel('&lt;list of %s&gt;'
                            #% str(inner_trait.trait_type.__class__.__name__))
        #item.setTextInteractionFlags(QtCore.Qt.TextSelectableByKeyboard |
                                     #QtCore.Qt.TextSelectableByMouse)
        #item.setFrameStyle(QtGui.QFrame.StyledPanel | QtGui.QFrame.Sunken)
        #layout.addWidget(item)

        # Create tools to interact with the list widget: expand or collapse -
        # add a list item - remove a list item
        tool_widget = QtGui.QWidget(parent)
        layout.addWidget(tool_widget)

        layout = QtGui.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        tool_widget.setLayout(layout)
        # Store some parameters in the list widget
        frame.inner_trait = inner_trait
        frame.trait = trait
        frame.connected = False
        if control_value is traits.Undefined:
            control_value = []
        elif not isinstance(control_value, (list, tuple)):
            # in nipype MultiPath, single values are not in a list
            control_value = [control_value]
        frame.trait_name = control_name

        # Create the label associated with the list widget
        control_label = trait.label
        if control_label is None:
            control_label = control_name
        if label_class is None:
            label_class = QtGui.QLabel
        if control_label is not None:
            label = label_class(control_label, parent)
        else:
            label = None
        frame.label_class = label_class

        # view the model
        items = OffscreenListControlWidget.partial_view_widget(
            weak_proxy(parent), weak_proxy(frame), control_value)
        layout.addWidget(items)
        #layout.addWidget(QtGui.QLabel('...'))
        frame.control_widget = items
        frame.controller = items.control_widget.controller
        frame.controller_widget = items.control_widget.controller_widget

        # Create the tool buttons
        edit_button = QtGui.QToolButton()
        layout.addWidget(edit_button)
        # Set the tool icons
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/soma_widgets_icons/add")),
            QtGui.QIcon.Normal, QtGui.QIcon.Off)
        edit_button.setIcon(icon)
        edit_button.setFixedSize(30, 22)

        #layout.addStretch(1)

        # Set some callback on the list control tools
        # Resize callback
        edit_hook = partial(
            OffscreenListControlWidget.edit_elements, weak_proxy(parent),
            weak_proxy(frame), weak_proxy(edit_button))
        edit_button.clicked.connect(edit_hook)

        return (frame, label)

    @staticmethod
    def partial_view_widget(controller_widget, parent_frame, control_value):
        widget = OneLineQTableWidget()
        widget.horizontalHeader().hide()
        widget.verticalHeader().hide()
        widget.max_items = OffscreenListControlWidget.max_items

        if control_value is traits.Undefined:
            control_value = []
        elif not isinstance(control_value, (list, tuple)):
            # in nipype MultiPath, single values are not in a list
            control_value = [control_value]

        control_widget, control_label = ListControlWidget.create_widget(
            controller_widget, parent_frame.trait_name, control_value,
            parent_frame.trait, parent_frame.label_class,
            max_items=widget.max_items, user_data=parent_frame.user_data)

        control_label[0].deleteLater()
        control_label[1].deleteLater()
        del control_label

        n = len(control_value)
        max_items = widget.max_items
        if max_items > 0:
            m = min(max_items, n)
            if n > max_items:
                widget.setColumnCount(m + 1)
            else:
                widget.setColumnCount(n)
        else:
            m = n
            widget.setColumnCount(n)
        clayout = control_widget.layout()
        widget.setRowCount(1)
        for i in range(m):
            litem = clayout.itemAtPosition(i + 1, 1)
            if litem is not None:
                item = litem.widget()
                widget.setCellWidget(0, i, item)
            if qt_backend.get_qt_backend() == 'PyQt5':
                widget.horizontalHeader().setSectionResizeMode(
                    i, QtGui.QHeaderView.Stretch)
            else:
                widget.horizontalHeader().setResizeMode(
                    i, QtGui.QHeaderView.Stretch)
        if n > m:
            widget.setCellWidget(0, max_items, QtGui.QLabel('...'))
            if qt_backend.get_qt_backend() == 'PyQt5':
                widget.horizontalHeader().setSectionResizeMode(
                    max_items, QtGui.QHeaderView.Fixed)
            else:
                widget.horizontalHeader().setResizeMode(
                    max_items, QtGui.QHeaderView.Fixed)

        widget.resizeRowToContents(0)
        #scroll_height = widget.findChildren(QtGui.QScrollBar)[-1].height()
        height = widget.rowHeight(0) \
            + sum(widget.getContentsMargins()[1:4:2]) # + scroll_height
        widget.setSizePolicy(QtGui.QSizePolicy.Expanding,
                             QtGui.QSizePolicy.Minimum)
        #widget.viewport().setSizePolicy(QtGui.QSizePolicy.MinimumExpanding,
                                        #QtGui.QSizePolicy.Fixed)
        #widget.viewport().setFixedHeight(widget.rowHeight(0))
        widget.setFixedHeight(height)

        widget.control_widget = control_widget
        control_widget.hide()

        return widget

    @staticmethod
    def update_controller(controller_widget, control_name, control_instance,
                          *args, **kwarg):
        """ Update one element of the controller.

        At the end the controller trait value with the name 'control_name'
        will match the controller widget user parameters defined in
        'control_instance'.

        Parameters
        ----------
        controller_widget: ControllerWidget (mandatory)
            a controller widget that contains the controller we want to update
        control_name: str(mandatory)
            the name of the controller widget control we want to synchronize
            with the controller
        control_instance: QFrame (mandatory)
            the instance of the controller widget control we want to
            synchronize with the controller
        """
        ListControlWidget.update_controller(
            controller_widget, control_name,
            control_instance.control_widget.control_widget, *args, **kwarg)

    @classmethod
    def update_controller_widget(cls, controller_widget, control_name,
                                 control_instance):
        """ Update one element of the list controller widget.

        At the end the list controller widget user editable parameter with the
        name 'control_name' will match the controller trait value with the same
        name.

        Parameters
        ----------
        controller_widget: ControllerWidget (mandatory)
            a controller widget that contains the controller we want to update
        control_name: str(mandatory)
            the name of the controller widget control we want to synchronize
            with the controller
        control_instance: QFrame (mandatory)
            the instance of the controller widget control we want to
            synchronize with the controller
        """
        try:
            if control_name not in controller_widget.controller.user_traits():
                return
        except ReferenceError:
            return

        # Get the list widget current connection status
        try:
            was_connected = control_instance.connected
            test = control_instance.control_widget.layout
        except (ReferenceError, RuntimeError):
            # widget deleted in the meantime
            return

        # Disconnect the list controller and the inner list controller
        cls.disconnect(controller_widget, control_name, control_instance)
        control_instance.controller_widget.disconnect()

        widget = control_instance.control_widget
        if sip.isdeleted(widget):
            OffscreenListControlWidget.disconnect(
                controller_widget, control_name, control_instance)
            return

        clayout = widget.control_widget.layout()
        owned_widgets = set()
        parent = widget
        for i in range(widget.columnCount()):
            w = widget.cellWidget(0, i)
            if w is not None:
                parent = w.parentWidget()
                owned_widgets.add(w)
        ListControlWidget.update_controller_widget(
            controller_widget, control_name, widget.control_widget)
        keys = list(control_instance.controller.user_traits().keys())
        #n = len(control_instance.controller.user_traits())
        parent_value = getattr(controller_widget.controller, control_name)
        if parent_value is traits.Undefined:
            parent_value = []
        elif not isinstance(parent_value, (list, tuple)):
            # in nipype MultiPath, single values are not in a list
            parent_value = [parent_value]
        n = len(parent_value)
        max_items = widget.max_items
        if max_items > 0:
            m = min(max_items, n)
            if n > max_items:
                widget.setColumnCount(m + 1)
            else:
                widget.setColumnCount(n)
        else:
            m = n
            widget.setColumnCount(n)
        for i in range(m):
            try:
                items = widget.control_widget.controller_widget._controls[
                    str(i)]
                item = items[None][2]
                if item not in owned_widgets:
                    widget.setCellWidget(0, i, item)
                if qt_backend.get_qt_backend() == 'PyQt5':
                    widget.horizontalHeader().setSectionResizeMode(
                        i, QtGui.QHeaderView.Stretch)
                else:
                    widget.horizontalHeader().setResizeMode(
                        i, QtGui.QHeaderView.Stretch)
            except KeyError:
                print('KeyError in OffscreenListControlWidget', i)
                print('controls:', widget.control_widget.controller_widget._controls)
        if n > m:
            label = QtGui.QLabel('...')
            width = label.sizeHint().width()
            widget.setCellWidget(0, max_items, QtGui.QLabel('...'))
            if qt_backend.get_qt_backend() == 'PyQt5':
                widget.horizontalHeader().setSectionResizeMode(
                    max_items, QtGui.QHeaderView.Fixed)
            else:
                widget.horizontalHeader().setResizeMode(
                    max_items, QtGui.QHeaderView.Fixed)
            widget.horizontalHeader().resizeSection(max_items, width)

        widget.resizeRowToContents(0)
        height = widget.rowHeight(0) \
            + sum(widget.getContentsMargins()[1:4:2])
        widget.setFixedHeight(height)

        # Restore the previous list controller connection status
        if was_connected:
            cls.connect(controller_widget, control_name, control_instance)
            control_instance.controller_widget.connect()

    @classmethod
    def connect(cls, controller_widget, control_name, control_instance):
        """ Connect a 'List' controller trait and an
        'OffscreenListControlWidget' controller widget control.

        Parameters
        ----------
        cls: StrControlWidget (mandatory)
            a StrControlWidget control
        controller_widget: ControllerWidget (mandatory)
            a controller widget that contains the controller we want to update
        control_name: str (mandatory)
            the name of the controller widget control we want to synchronize
            with the controller
        control_instance: QFrame (mandatory)
            the instance of the controller widget control we want to
            synchronize with the controller
        """
        # Check if the control is connected
        if not control_instance.connected:

            # Update the list item when one of his associated controller trait
            # changed.
            # Hook: function that will be called to update the controller
            # associated with a list widget when a list widget inner controller
            # trait is modified.
            list_controller_hook = SomaPartial(
                cls.update_controller, weak_proxy(controller_widget),
                control_name, weak_proxy(control_instance))

            # Go through all list widget inner controller user traits
            for trait_name in control_instance.controller.user_traits():

                # And add the callback on each user trait
                control_instance.controller.on_trait_change(
                    list_controller_hook, trait_name, dispatch='ui')
                logger.debug("Item '{0}' of a 'ListControlWidget', add "
                             "a callback on inner controller trait "
                             "'{0}'.".format(control_name, trait_name))

            # Update the list controller widget.
            # Hook: function that will be called to update the specific widget
            # when a trait event is detected on the list controller.
            controller_hook = SomaPartial(
                cls.update_controller_widget, weak_proxy(controller_widget),
                control_name, weak_proxy(control_instance))

            # When the 'control_name' controller trait value is modified,
            # update the corresponding control
            controller_widget.controller.on_trait_change(
                controller_hook, control_name, dispatch='ui')

            # Update the list connection status
            control_instance._controller_connections = (
                list_controller_hook, controller_hook)
            logger.debug("Add 'List' connection: {0}.".format(
                control_instance._controller_connections))

            # Update the list control connection status
            control_instance.connected = True

    @staticmethod
    def disconnect(controller_widget, control_name, control_instance):
        """ Disconnect a 'List' controller trait and an
        'OffscreenListControlWidget' controller widget control.

        Parameters
        ----------
        cls: StrControlWidget (mandatory)
            a StrControlWidget control
        controller_widget: ControllerWidget (mandatory)
            a controller widget that contains the controller we want to update
        control_name: str (mandatory)
            the name of the controller widget control we want to synchronize
            with the controller
        control_instance: QFrame (mandatory)
            the instance of the controller widget control we want to
            synchronize with the controller
        """
        # Check if the control is connected
        if control_instance.connected:

            # Get the stored widget and controller hooks
            (list_controller_hook,
             controller_hook) = control_instance._controller_connections

            # Remove the controller hook from the 'control_name' trait
            controller_widget.controller.on_trait_change(
                controller_hook, control_name, remove=True)

            # Remove the list controller hook associated with the controller
            # traits
            for trait_name in control_instance.controller.user_traits():
                control_instance.controller.on_trait_change(
                    list_controller_hook, trait_name, remove=True)

            # Delete the trait - control connection we just remove
            del control_instance._controller_connections

            # Disconnect also all list items
            inner_controls = control_instance.controller_widget._controls
            for (inner_control_name,
                 inner_control_groups) in six.iteritems(inner_controls):
                for group, inner_control \
                        in six.iteritems(inner_control_groups):

                    # Unpack the control item
                    inner_control_instance = inner_control[2]
                    inner_control_class = inner_control[1]

                    # Call the inner control disconnect method
                    inner_control_class.disconnect(
                        control_instance.controller_widget, inner_control_name,
                        inner_control_instance)

            # Update the list control connection status
            control_instance.connected = False

    #
    # Callbacks
    #


    @staticmethod
    def edit_elements(controller_widget, control_instance, edit_button):
        """ Callback to view/edit a 'ListControlWidget'.

        Parameters
        ----------
        control_instance: QFrame (mandatory)
            the list widget item
        edit_button: QToolButton
            the signal sender
        """
        controller_widget = get_ref(controller_widget)
        widget = QtGui.QDialog(controller_widget)
        widget.setModal(True)
        layout = QtGui.QVBoxLayout()
        widget.setLayout(layout)
        #hlayout = QtGui.QHBoxLayout()
        #layout.addLayout(hlayout)

        temp_controller = Controller()
        trait = control_instance.trait

        temp_controller.add_trait(control_instance.trait_name, trait)
        if temp_controller.trait(control_instance.trait_name).groups \
                is not None:
            temp_controller.trait(control_instance.trait_name).groups = None

        value = getattr(controller_widget.controller,
                        control_instance.trait_name)

        try:
            setattr(temp_controller, control_instance.trait_name, value)
        except Exception:
            # invalid value - don't prevent using the GUI
            pass
        control_types = dict(controller_widget._defined_controls)
        control_types['List'] = ListControlWidget
        control_types['List_File'] = ListControlWidget
        temp_controller_widget = ScrollControllerWidget(
            temp_controller, live=True, override_control_types=control_types,
            user_data=control_instance.user_data)

        layout.addWidget(temp_controller_widget)

        hlayout2 = QtGui.QHBoxLayout()
        layout.addLayout(hlayout2)
        hlayout2.addStretch(1)
        ok = QtGui.QPushButton('OK')
        cancel = QtGui.QPushButton('Cancel')
        hlayout2.addWidget(ok)
        hlayout2.addWidget(cancel)

        ok.pressed.connect(widget.accept)
        cancel.pressed.connect(widget.reject)

        if widget.exec_():

            ctrl = temp_controller_widget.controller_widget._controls.get(
                control_instance.trait_name)[None]
            ListControlWidget.validate_all_values(
                temp_controller_widget.controller_widget, ctrl[2])
            new_trait_value = getattr(temp_controller,
                                      control_instance.trait_name)

            setattr(controller_widget.controller,
                    control_instance.trait_name,
                    new_trait_value)

        del temp_controller_widget

    #@staticmethod
    #def item_changed(control_widget, item):
        #print('item_changed:', controller_widget, item)


class OneLineQTableWidget(QtGui.QTableWidget):
    '''QTableWidget witon one line, with fixed row height. Resizes to add the
    horizontal scrollbar at the bottom when it becomes visible without changing
    the visible row height.
    '''
    def resizeEvent(self, event):
        scrollbar = self.horizontalScrollBar().isVisible()
        mheight = self.rowHeight(0) \
            + sum(self.getContentsMargins()[1:4:2])
        if self.height() != mheight:
            self.setFixedHeight(mheight)
        super(OneLineQTableWidget, self).resizeEvent(event)
