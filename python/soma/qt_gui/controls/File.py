# -*- coding: utf-8 -*-

from functools import partial
import os

import sip

from soma.controller import is_output
from soma.qt_gui import qt_backend
from soma.qt_gui.qt_backend import QtGui, QtCore
from soma.qt_gui.timered_widgets import TimeredQLineEdit
from soma.undefined import undefined
from soma.utils.weak_proxy import weak_proxy

class FileControlWidget(object):

    """ Control to enter a file.
    """

    @staticmethod
    def is_valid(control_instance, *args, **kwargs):
        """ Method to check if the new control value is correct.

        If the new entered value is not correct, the backroung control color
        will be red.

        Parameters
        ----------
        control_instance: QWidget (mandatory)
            the control widget we want to validate

        Returns
        -------
        out: bool
            True if the control value is a file,
            False otherwise
        """
        # Get the current control palette
        control_palette = control_instance.path.palette()

        # Get the control current value
        control_value = control_instance.path.value()

        color = QtCore.Qt.white
        red = QtGui.QColor(255, 220, 220)
        yellow = QtGui.QColor(255, 255, 200)

        # If the control value contains a file, the control is valid and the
        # backgound color of the control is white
        is_valid = False
        if control_value is undefined:
            # Undefined is an exception: allow to reset it (File instances,
            # even mandatory, are initialized with Undefined value)
            is_valid = True
            if not control_instance.optional:
                color = red
                #print('red undefined: valid')
        else:

            if (os.path.isfile(control_value)
                    or (is_output(control_instance.field)
                        and control_value != '')):
                is_valid = True

            # If the control value is optional, the control is valid and the
            # backgound color of the control is yellow
            elif control_instance.optional \
                    and control_value in ("", ):
                color = yellow
                is_valid = True

            # If the control value is empty, the control is not valid and the
            # backgound color of the control is red
            else:
                if not control_instance.optional:
                    color = red
                    #print('red: invalid', repr(control_value))

        # Set the new palette to the control instance
        control_palette.setColor(control_instance.path.backgroundRole(), color)
        control_instance.path.setPalette(control_palette)

        return is_valid

    @classmethod
    def check(cls, control_instance):
        """ Check if a controller widget control is filled correctly.

        Parameters
        ----------
        cls: FileControlWidget (mandatory)
            a StrControlWidget control
        control_instance: QWidget (mandatory)
            the control widget we want to validate
        """
        # Hook: function that will be called to check for typo
        # when a 'userModification' qt signal is emited
        widget_callback = partial(cls.is_valid, weak_proxy(control_instance))

        # The first time execute manually the control check method
        widget_callback()

        # When a qt 'userModification' signal is emited, check if the new
        # user value is correct
        control_instance.path.userModification.connect(widget_callback)

    @staticmethod
    def add_callback(callback, control_instance):
        """ Method to add a callback to the control instance when a 'userModification'
        signal is emited.

        Parameters
        ----------
        callback: @function (mandatory)
            the function that will be called when a 'userModification' signal is
            emited.
        control_instance: QWidget (mandatory)
            the control widget we want to validate
        """
        control_instance.path.userModification.connect(callback)

    @staticmethod
    def create_widget(parent, controller, field,
                      label_class=None):
        """ Method to create the file widget.

        Parameters
        ----------
        parent: QWidget (mandatory)
            the parent widget
        controller: Controller (mandatory)
            Controller instance containing the field to create a widget
            for.
        field: Field (mandatory)
            the controller field associated to the control
        label_class: Qt widget class (optional, default: None)
            the label widget will be an instance of this class. Its constructor
            will be called using 2 arguments: the label string and the parent
            widget.

        Returns
        -------
        out: 2-uplet
            a two element tuple of the form (control widget: QWidget with two
            elements, a QLineEdit in the 'path' parameter and a browse button
            in the 'browse' parameter, associated label: QLabel)
        """
        # Create the widget that will be used to select a file
        widget = QtGui.QWidget(parent)
        layout = QtGui.QHBoxLayout()
        layout.setSpacing(0)
        layout.setSizeConstraint(QtGui.QLayout.SetMinimumSize)
        layout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(layout)
        # Create a widget to print the file path
        path = TimeredQLineEdit(widget, predefined_values=[undefined])
        # this takes too much space...
        #if hasattr(path, 'setClearButtonEnabled'):
            #path.setClearButtonEnabled(True)
        layout.addWidget(path)
        widget.path = path
        # Create a browse button
        button = QtGui.QPushButton("...", widget)
        button.setObjectName('file_button')
        button.setStyleSheet('QPushButton#file_button '
                             '{padding: 2px 10px 2px 10px; margin: 0px;}')
        layout.addWidget(button)
        widget.browse = button

        # Add a widget parameter to tell us if the widget is already connected
        widget.connected = False

        # Add a parameter to tell us if the widget is optional
        widget.optional = controller.is_optional(field)
        widget.output = is_output(field)

        # Set a callback on the browse button
        control_class = parent.get_control_class(field)
        widget.control_class = control_class
        browse_hook = partial(control_class.onBrowseClicked,
                              weak_proxy(widget))
        widget.browse.clicked.connect(browse_hook)

        # Create the label associated with the string widget
        control_label = controller.metadata(field, 'label', field.name)
        if label_class is None:
            label_class = QtGui.QLabel
        if control_label is not None:
            label = label_class(control_label, parent)
        else:
            label = None
        widget.field = field

        return (widget, label)

    @staticmethod
    def update_controller(controller_widget, control_name, control_instance,
                          reset_invalid_value=False, *args, **kwargs):
        """ Update one element of the controller.

        At the end the controller field value with the name 'control_name'
        will match the controller widget user parameters defined in
        'control_instance'.

        Parameters
        ----------
        controller_widget: ControllerWidget (mandatory)
            a controller widget that contains the controller we want to update
        control_name: str(mandatory)
            the name of the controller widget control we want to synchronize
            with the controller
        control_instance: QWidget (mandatory)
            the instance of the controller widget control we want to
            synchronize with the controller
        """
        # Update the controller only if the control is valid
        control_class = control_instance.control_class
        fail = True
        if control_class.is_valid(control_instance):

            # Get the control value
            new_value = control_instance.path.value()
            protected = controller_widget.controller.field(
                control_name).metadata.get('protected', False)
            # value is manually modified: protect it
            if getattr(controller_widget.controller, control_name, undefined) \
                    != new_value:
                controller_widget.controller.set_metadata(control_name, 'protected', True)
            # Set the control value to the controller associated field
            try:
                if new_value not in (None, undefined):
                    new_value = str(new_value)
                setattr(controller_widget.controller, control_name,
                        new_value)
                fail = False
            except ValidationError as e:
                print(e)
                if not protected:
                    # resgtore protected state after abortion
                    controller_widget.controller.set_metadata(control_name, 'protected', False)

        if fail and reset_invalid_value:
            # invalid, reset GUI to older value
            old_value = getattr(controller_widget.controller,
                                      control_name)
            control_instance.path.set_value(old_value)

    @staticmethod
    def update_controller_widget(controller_widget, control_name,
                                 control_instance):
        """ Update one element of the controller widget.

        At the end the controller widget user editable parameter with the
        name 'control_name' will match the controller field value with the same
        name.

        Parameters
        ----------
        controller_widget: ControllerWidget (mandatory)
            a controller widget that contains the controller we want to update
        control_name: str(mandatory)
            the name of the controller widget control we want to synchronize
            with the controller
        control_instance: QWidget (mandatory)
            the instance of the controller widget control we want to
            synchronize with the controller
        """

        # Get the field value
        try:
            was_connected = control_instance.connected
        except ReferenceError:
            # widget deleted in the meantime
            return

        if sip.isdeleted(control_instance.__init__.__self__):
            FileControlWidget.disconnect(controller_widget, control_name,
                                         control_instance)
            return

        new_controller_value = getattr(
            controller_widget.controller, control_name, "")

        # Set the field value to the string control
        control_instance.path.setText(str(new_controller_value))

    @classmethod
    def connect(cls, controller_widget, control_name, control_instance):
        """ Connect a 'File' controller field and a 'FileControlWidget'
        controller widget control.

        Parameters
        ----------
        cls: FileControlWidget (mandatory)
            a StrControlWidget control
        controller_widget: ControllerWidget (mandatory)
            a controller widget that contains the controller we want to update
        control_name: str (mandatory)
            the name of the controller widget control we want to synchronize
            with the controller
        control_instance: QWidget (mandatory)
            the instance of the controller widget control we want to
            synchronize with the controller
        """
        # Check if the control is connected
        if not control_instance.connected:

            # Update one element of the controller.
            # Hook: function that will be called to update a specific
            # controller field when a 'userModification' qt signal is emited
            widget_hook = partial(cls.update_controller,
                                  weak_proxy(controller_widget),
                                  control_name,
                                  weak_proxy(control_instance),
                                  False)

            # When a qt 'userModification' signal is emited, update the
            # 'control_name' controller field value
            control_instance.path.userModification.connect(widget_hook)

            widget_hook2 = partial(cls.update_controller,
                                   weak_proxy(controller_widget),
                                   control_name,
                                   weak_proxy(control_instance), True)

            control_instance.path.editingFinished.connect(widget_hook2)

            # Update the control.
            # Hook: function that will be called to update the control value
            # when the 'control_name' controller field is modified.
            controller_hook = partial(
                cls.update_controller_widget, weak_proxy(controller_widget),
                control_name, weak_proxy(control_instance))

            # When the 'control_name' controller field value is modified,
            # update the corresponding control
            controller_widget.controller.on_attribute_change.add(
                controller_hook, control_name)

            # Store the field - control connection we just build
            control_instance._controller_connections = (
                widget_hook, widget_hook2, controller_hook)

            # Update the control connection status
            control_instance.connected = True

    @staticmethod
    def disconnect(controller_widget, control_name, control_instance):
        """ Disconnect a 'File' controller field and a 'FileControlWidget'
        controller widget control.

        Parameters
        ----------
        controller_widget: ControllerWidget (mandatory)
            a controller widget that contains the controller we want to update
        control_name: str(mandatory)
            the name of the controller widget control we want to synchronize
            with the controller
        control_instance: QWidget (mandatory)
            the instance of the controller widget control we want to
            synchronize with the controller
        """
        # Check if the control is connected
        if control_instance.connected:

            # Get the stored widget and controller hooks
            (widget_hook, widget_hook2,
             controller_hook) = control_instance._controller_connections

            # Remove the controller hook from the 'control_name' field
            controller_widget.controller.on_attribute_change.remove(
                controller_hook, control_name)

            if sip.isdeleted(control_instance.__init__.__self__):
                return

            # Remove the widget hook associated with the qt 'userModification'
            # signal
            control_instance.path.userModification.disconnect(widget_hook)
            control_instance.path.editingFinished.disconnect(widget_hook2)

            # Delete the field - control connection we just remove
            del control_instance._controller_connections

            # Update the control connection status
            control_instance.connected = False

    #
    # Callbacks
    #

    @staticmethod
    def onBrowseClicked(control_instance):
        """ Browse the file system and update the control instance accordingly.

        If a valid file path has already been entered the file dialogue will
        automatically point to the file folder, otherwise the current working
        directory is used.

        Parameters
        ----------
        control_instance: QWidget (mandatory)
            the file widget item
        """
        # Get the current file path
        current_control_value = os.getcwd()
        if FileControlWidget.is_valid(control_instance):
            current_control_value \
                = str(control_instance.path.text())

        # get widget via a __self__ in a method, because control_instance may
        # be a weakproxy.
        widget = control_instance.__repr__.__self__
        ext = []
        # TODO: manage extensions via formats
        # field = control_instance.field
        # if trait.allowed_extensions:
        #     ext = trait.allowed_extensions
        # if trait.extensions:
        #     ext = trait.extensions
        ext = ' '.join(f'*{e}' for e in ext)
        if ext:
            ext += ';; All files (*)'
        # Create a dialog to select a file
        if control_instance.output:
            fname = qt_backend.getSaveFileName(
                widget, "Output file", current_control_value, ext,
                None, QtGui.QFileDialog.DontUseNativeDialog)
        else:
            fname = qt_backend.getOpenFileName(
                widget, "Open file", current_control_value, ext, None,
                QtGui.QFileDialog.DontUseNativeDialog)

        # Set the selected file path to the path sub control
        control_instance.path.set_value(str(fname))
