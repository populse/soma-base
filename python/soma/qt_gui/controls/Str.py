# -*- coding: utf-8 -*-

from functools import partial

from soma.qt_gui.qt_backend import QtGui, QtCore
from soma.qt_gui.timered_widgets import TimeredQLineEdit
from soma.utils.weak_proxy import weak_proxy
from soma.undefined import undefined
import sip


class StrControlWidget(object):

    """ Control to enter a string.
    """

    @staticmethod
    def is_valid(control_instance, *args, **kwargs):
        """ Method to check if the new control value is correct.

        If the new entered value is not correct, the backroung control color
        will be red.

        Parameters
        ----------
        control_instance: QLineEdit (mandatory)
            the control widget we want to validate

        Returns
        -------
        out: bool
            True if the control value is valid,
            False otherwise
        """
        # Get the current control palette
        control_palette = control_instance.palette()

        # Get the control current value
        control_value = control_instance.value()

        color = QtCore.Qt.white
        red = QtGui.QColor(255, 220, 220)
        yellow = QtGui.QColor(255, 255, 200)

        # If the control value is not empty, the control is valid and the
        # backgound color of the control is white
        is_valid = False

        if control_value in ('', None, undefined):
            if control_instance.optional:
                # If the control value is optional, the control is valid and
                # the backgound color of the control is yellow
                color = yellow
                is_valid = True
            else:
                color = red
                if control_value != '':
                    # allow to reset value
                    is_valid = True

        else:
            is_valid = True

        # Set the new palette to the control instance
        control_palette.setColor(control_instance.backgroundRole(), color)
        control_instance.setPalette(control_palette)

        return is_valid

    @classmethod
    def check(cls, control_instance):
        """ Check if a controller widget control is filled correctly.

        Parameters
        ----------
        cls: StrControlWidget (mandatory)
            a StrControlWidget control
        control_instance: QLineEdit (mandatory)
            the control widget we want to validate
        """
        # Hook: function that will be called to check for typo
        # when a 'userModification' qt signal is emited
        widget_callback = partial(cls.is_valid, weak_proxy(control_instance))

        # The first time execute manually the control check method
        widget_callback()

        # When a qt 'userModification' signal is emited, check if the new
        # user value is correct
        control_instance.userModification.connect(widget_callback)

    @staticmethod
    def add_callback(callback, control_instance):
        """ Method to add a callback to the control instance when a 'userModification'
        signal is emited.

        Parameters
        ----------
        callback: @function (mandatory)
            the function that will be called when a 'userModification' signal is
            emited.
        control_instance: QLineEdit (mandatory)
            the control widget we want to validate
        """
        control_instance.userModification.connect(callback)

    @staticmethod
    def create_widget(parent, controller, field,
                      label_class=None):
        """ Method to create the string widget.

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
            a two element tuple of the form (control widget: QLineEdit,
            associated label: QLabel)
        """
        # Create the widget that will be used to fill a string
        widget = TimeredQLineEdit(parent, predefined_values=[undefined])
        # this takes too much space on some GUI contexts
        #if hasattr(widget, 'setClearButtonEnabled'):
            #widget.setClearButtonEnabled(True)

        # Add a widget parameter to tell us if the widget is already connected
        widget.connected = False

        # Add a parameter to tell us if the widget is optional
        widget.optional = controller.is_optional(field)

        # Create the label associated with the string widget
        control_label = controller.metadata(field.name, 'label', field.name)
        if label_class is None:
            label_class = QtGui.QLabel
        if control_label is not None:
            label = label_class(control_label, parent)
        else:
            label = None

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
        control_instance: QLineEdit (mandatory)
            the instance of the controller widget control we want to
            synchronize with the controller
        """
        # Update the controller only if the control is valid
        if StrControlWidget.is_valid(control_instance):

            # Get the control value
            new_value = control_instance.value()
            if new_value not in (undefined, None):
                new_value = str(new_value)

            # value is manually modified: protect it
            if (hasattr(controller_widget.controller, control_name)
                    and getattr(controller_widget.controller, control_name)
                        != new_value):
                controller_widget.controller.set_metadata(control_name, 'protected', True)
            # Set the control value to the controller associated field
            setattr(controller_widget.controller, control_name,
                    new_value)
        elif reset_invalid_value:
            # invalid, reset GUI to older value
            old_value = getattr(controller_widget.controller,
                                      control_name)
            control_instance.set_value(old_value)

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
        control_instance: QLineEdit (mandatory)
            the instance of the controller widget control we want to
            synchronize with the controller
        """
        try:
            was_connected = control_instance.connected
        except ReferenceError:
            # widget deleted in the meantime
            return

        if sip.isdeleted(control_instance.__init__.__self__):
            StrControlWidget.disconnect(controller_widget, control_name,
                                        control_instance)
            return

        # Get the field value
        new_controller_value = getattr(
            controller_widget.controller, control_name, undefined)

        # Set the field value to the string control
        control_instance.set_value(new_controller_value)

    @classmethod
    def connect(cls, controller_widget, control_name, control_instance):
        """ Connect a 'Str' or 'String' controller field and a
        'StrControlWidget' controller widget control.

        Parameters
        ----------
        cls: StrControlWidget (mandatory)
            a StrControlWidget control
        controller_widget: ControllerWidget (mandatory)
            a controller widget that contains the controller we want to update
        control_name: str (mandatory)
            the name of the controller widget control we want to synchronize
            with the controller
        control_instance: QLineEdit (mandatory)
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
                                  control_name, weak_proxy(control_instance),
                                  False)

            # When a qt 'userModification' signal is emited, update the
            # 'control_name' controller field value
            control_instance.userModification.connect(widget_hook)

            widget_hook2 = partial(cls.update_controller,
                                   weak_proxy(controller_widget),
                                   control_name, weak_proxy(control_instance),
                                   True)

            control_instance.editingFinished.connect(widget_hook2)

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
        """ Disconnect a 'Str' or 'String' controller field and a
        'StrControlWidget' controller widget control.

        Parameters
        ----------
        controller_widget: ControllerWidget (mandatory)
            a controller widget that contains the controller we want to update
        control_name: str(mandatory)
            the name of the controller widget control we want to synchronize
            with the controller
        control_instance: QLineEdit (mandatory)
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
            control_instance.userModification.disconnect(widget_hook)
            control_instance.editingFinished.disconnect(widget_hook2)

            # Delete the field - control connection we just remove
            del control_instance._controller_connections

            # Update the control connection status
            control_instance.connected = False
