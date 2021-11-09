# -*- coding: utf-8 -*-
from functools import partial
import sip

from soma.qt_gui.qt_backend import QtGui, Qt
from soma.utils.functiontools import SomaPartial
from soma.qt_gui.controller_widget import weak_proxy
from soma.undefined import undefined


class BoolControlWidget(object):

    """ Control to set or unset an option.
    """

    @staticmethod
    def is_valid(control_instance, *args, **kwargs):
        """ Method to check if the new control value is correct.

        Parameters
        ----------
        control_instance: QCheckBox (mandatory)
            the control widget we want to validate

        Returns
        -------
        out: bool
            always True since the control value is always valid
        """
        return True

    @classmethod
    def check(cls, control_instance):
        """ Check if a controller widget control is filled correctly.

        Parameters
        ----------
        cls: BoolControlWidget (mandatory)
            a BoolControlWidget control
        control_instance: QCheckBox (mandatory)
            the control widget we want to validate
        """
        # Hook: function that will be called to check for typo
        # when a 'clicked' qt signal is emited
        widget_callback = partial(cls.is_valid, weak_proxy(control_instance))

        # Execute manually the first time the control check method
        widget_callback()

        # When a qt 'clicked' signal is emited, check if the new
        # user value is correct
        control_instance.clicked.connect(widget_callback)

    @staticmethod
    def add_callback(callback, control_instance):
        """ Method to add a callback to the control instance when a 'clicked'
        signal is emited.

        Parameters
        ----------
        callback: @function (mandatory)
            the function that will be called when a 'clicked' signal is emited.
        control_instance: QCheckBox (mandatory)
            the control widget we want to validate
        """
        control_instance.clicked.connect(callback)

    @staticmethod
    def create_widget(parent, controller, field,
                      label_class=None):
        """ Method to create the bool widget.

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
        # Create the widget that will be used to select an option
        widget = QtGui.QCheckBox(parent)

        # Add a widget parameter to tell us if the widget is already connected
        widget.connected = False

        # Create the label associated with the bool widget
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
                          *args, **kwargs):
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
        control_instance: QCheckBox (mandatory)
            the instance of the controller widget control we want to
            synchronize with the controller
        """
        # Update the controller only if the control is valid
        if BoolControlWidget.is_valid(control_instance):

            # Get the control value
            new_value = bool(control_instance.isChecked())

            # value is manually modified: protect it
            if getattr(controller_widget.controller, control_name, undefined) \
                    != new_value:
                controller_widget.controller.set_metadata(control_name, 'protected', True)
            # Set the control value to the controller associated field
            setattr(controller_widget.controller, control_name,
                    new_value)

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
        control_instance: QCheckBox (mandatory)
            the instance of the controller widget control we want to
            synchronize with the controller
        """
        try:
            test = control_instance.setTristate
        except ReferenceError:
            # widget deleted in the meantime
            return

        if sip.isdeleted(control_instance.__init__.__self__):
            BoolControlWidget.disconnect(controller_widget, control_name,
                                         control_instance)
            return

        # Get the field value
        new_controller_value = getattr(
            controller_widget.controller, control_name, False)

        if new_controller_value is undefined:
            control_instance.setTristate(True)
        # Set the field value to the bool control
        if new_controller_value is True:
            new_controller_checked = Qt.Qt.Checked
        elif new_controller_value is False:
            new_controller_checked = Qt.Qt.Unchecked
        else:
            new_controller_checked = Qt.Qt.PartiallyChecked
        control_instance.setCheckState(new_controller_checked)

    @classmethod
    def connect(cls, controller_widget, control_name, control_instance):
        """ Connect a 'Bool' controller field and a 'BoolControlWidget'
        controller widget control.

        Parameters
        ----------
        cls: BoolControlWidget (mandatory)
            a BoolControlWidget control
        controller_widget: ControllerWidget (mandatory)
            a controller widget that contains the controller we want to update
        control_name: str (mandatory)
            the name of the controller widget control we want to synchronize
            with the controller
        control_instance: QCheckBox (mandatory)
            the instance of the controller widget control we want to
            synchronize with the controller
        """
        # Check if the control is connected
        if not control_instance.connected:

            # Update one element of the controller.
            # Hook: function that will be called to update a specific
            # controller field when a 'textChanged' qt signal is emited
            widget_hook = partial(cls.update_controller,
                                  weak_proxy(controller_widget),
                                  control_name, weak_proxy(control_instance))

            # When a qt 'clicked' signal is emited, update the
            # 'control_name' controller field value
            control_instance.clicked.connect(widget_hook)

            # Update the control.
            # Hook: function that will be called to update the control value
            # when the 'control_name' controller field is modified.
            controller_hook = SomaPartial(
                cls.update_controller_widget, weak_proxy(controller_widget),
                control_name, weak_proxy(control_instance))

            # When the 'control_name' controller field value is modified,
            # update the corresponding control
            controller_widget.controller.on_attribute_change.add(
                controller_hook, control_name)

            # Store the field - control connection we just build
            control_instance._controller_connections = (
                widget_hook, controller_hook)

            # Update the control connection status
            control_instance.connected = True

    @staticmethod
    def disconnect(controller_widget, control_name, control_instance):
        """ Disconnect a 'Bool' controller field and a 'BoolControlWidget'
        controller widget control.

        Parameters
        ----------
        controller_widget: ControllerWidget (mandatory)
            a controller widget that contains the controller we want to update
        control_name: str(mandatory)
            the name of the controller widget control we want to synchronize
            with the controller
        control_instance: QCheckBox (mandatory)
            the instance of the controller widget control we want to
            synchronize with the controller
        """
        # Check if the control is connected
        if control_instance.connected:

            # Get the stored widget and controller hooks
            (widget_hook,
             controller_hook) = control_instance._controller_connections

            # Remove the controller hook from the 'control_name' field
            controller_widget.controller.on_attribute_change.remove(
                controller_hook, control_name)

            # Remove the widget hook associated with the qt 'clicked' signal
            if not sip.isdeleted(control_instance.__init__.__self__):
                control_instance.clicked.disconnect(widget_hook)

            # Delete the field - control connection we just remove
            del control_instance._controller_connections

            # Update the control connection status
            control_instance.connected = False
