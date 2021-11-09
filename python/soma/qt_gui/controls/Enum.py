# -*- coding: utf-8 -*-

from functools import partial
from soma.controller.field import field_literal_values

from soma.qt_gui.qt_backend import QtGui
from soma.utils.weak_proxy import weak_proxy
from soma.undefined import undefined
import sip


class EnumControlWidget(object):

    """ Control to select a value from a list.
    """

    @staticmethod
    def is_valid(control_instance, *args, **kwargs):
        """ Method to check if the new control value is correct.

        Parameters
        ----------
        control_instance: QComboBox (mandatory)
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
        cls: EnumControlWidget (mandatory)
            an EnumControlWidget control
        control_instance: QComboBox (mandatory)
            the control widget we want to validate
        """
        # Hook: function that will be called to check for typo
        # when a 'textEdited' qt signal is emited
        widget_callback = partial(cls.is_valid, weak_proxy(control_instance))

        # Execute manually the first time the control check method
        widget_callback()

        # When a qt 'editTextChanged' signal is emited, check if the new
        # user value is correct
        control_instance.editTextChanged.connect(widget_callback)

    @staticmethod
    def add_callback(callback, control_instance):
        """ Method to add a callback to the control instance when a 'editTextChanged'
        signal is emited.

        Parameters
        ----------
        callback: @function (mandatory)
            the function that will be called when a 'editTextChanged' signal is
            emited.
        control_instance: QComboBox (mandatory)
            the control widget we want to validate
        """
        control_instance.editTextChanged.connect(callback)

    @staticmethod
    def create_widget(parent, controller, field,
                      label_class=None):
        """ Method to create the widget.

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
            a two element tuple of the form (control widget: QComboBox,
            associated label: QLabel)
        """
        # Create the widget that will be used to select a value
        widget = QtGui.QComboBox(parent)

        # Save the possible choices
        widget._choices = field_literal_values(field)

        # Add a parameter to tell us if the widget is optional
        widget.optional = controller.is_optional(field)

        # Set the enum list items to the widget
        for item in widget._choices:
            widget.addItem(str(item))

        # Select the default value
        # If the default value is not in the enum list, pick the first item
        # of the enum list
        control_value = getattr(controller, field.name, undefined)
        if control_value not in widget._choices:
            widget.setCurrentIndex(0)
        else:
            widget.setCurrentIndex(widget._choices.index(control_value))

        # Create the label associated with the enum widget
        control_label = controller.metadata(field.name, 'label', field.name)
        if label_class is None:
            label_class = QtGui.QLabel
        if control_label is not None:
            label = label_class(control_label, parent)
        else:
            label = None

        return (widget, label)

    @staticmethod
    def update_controller(controller_widget, control_name,
                          control_instance, *args, **kwargs):
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
        control_instance: StrControlWidget (mandatory)
            the instance of the controller widget control we want to
            synchronize with the controller
        """
        if EnumControlWidget.is_valid(control_instance):
            new_value = control_instance._choices[
                control_instance.currentIndex()]
            # value is manually modified: protect it
            if getattr(controller_widget.controller, control_name, undefined) \
                    != new_value:
                controller_widget.controller.set_metadata(control_name, 'protected', True)
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
        control_instance: StrControlWidget (mandatory)
            the instance of the controller widget control we want to
            synchronize with the controller
        """

        # Get the controller field value
        try:
            test = control_instance.setCurrentIndex
        except ReferenceError:
            # widget deleted in the meantime
            return

        if sip.isdeleted(control_instance.__init__.__self__):
            EnumControlWidget.disconnect(controller_widget, control_name,
                                         control_instance)
            return

        new_controller_value = getattr(
            controller_widget.controller, control_name, None)

        # If the controller value is not empty, update the controller widget
        # associated control
        if new_controller_value not in (None, undefined):
            control_instance.setCurrentIndex(
                control_instance._choices.index(new_controller_value))
 
    @classmethod
    def connect(cls, controller_widget, control_name, control_instance):
        """ Connect an 'Enum' controller field and an 'EnumControlWidget'
        controller widget control.

        Parameters
        ----------
        cls: EnumControlWidget (mandatory)
            an EnumControlWidget control
        controller_widget: ControllerWidget (mandatory)
            a controller widget that contains the controller we want to update
        control_name: str (mandatory)
            the name of the controller widget control we want to synchronize
            with the controller
        control_instance: QComboBox (mandatory)
            the instance of the controller widget control we want to
            synchronize with the controller
        """
        # Update one element of the controller.
        # Hook: function that will be called to update a specific
        # controller field when an 'activated' qt signal is emited
        widget_hook = partial(cls.update_controller,
                              weak_proxy(controller_widget),
                              control_name, weak_proxy(control_instance))

        # When a qt 'activated' signal is emited, update the
        # 'control_name' controller field value
        control_instance.activated.connect(widget_hook)

        # Update one element of the controller widget.
        # Hook: function that will be called to update the specific widget
        # when a field event is detected.
        controller_hook = partial(
            cls.update_controller_widget, weak_proxy(controller_widget),
            control_name, weak_proxy(control_instance))

        # When the 'control_name' controller field value is modified, update
        # the corresponding control
        controller_widget.controller.on_attribute_change.add(
            controller_hook, control_name)

        # Store the field - control connection we just build
        control_instance._controller_connections = (
            widget_hook, controller_hook)
 
    @staticmethod
    def disconnect(controller_widget, control_name, control_instance):
        """ Disconnect an 'Enum' controller field and an 'EnumControlWidget'
        controller widget control.

        Parameters
        ----------
        controller_widget: ControllerWidget (mandatory)
            a controller widget that contains the controller we want to update
        control_name: str(mandatory)
            the name of the controller widget control we want to synchronize
            with the controller
        control_instance: QComboBox (mandatory)
            the instance of the controller widget control we want to
            synchronize with the controller
        """
        # Get the stored widget and controller hooks
        (widget_hook,
         controller_hook) = control_instance._controller_connections

        # Remove the controller hook from the 'control_name' field
        controller_widget.controller.on_attribute_change.remove(
            controller_hook, control_name)

        # Remove the widget hook associated with the qt 'activated'
        # signal
        if not sip.isdeleted(control_instance.__init__.__self__):
            control_instance.activated.disconnect(widget_hook)

        # Delete the field - control connection we just remove
        del control_instance._controller_connections
