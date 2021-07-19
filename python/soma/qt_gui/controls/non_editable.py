# -*- coding: utf-8 -*-
#
# SOMA - Copyright (C) CEA, 2015
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
#

# System import
from __future__ import absolute_import
import traits.api as traits
# Soma import
from soma.qt_gui.qt_backend import Qt
import sip


class NonEditableControlWidget(object):

    """ Displays that a control cannot be edited or seen. This is used for
    unknown types.
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
        return True

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
        pass

    @staticmethod
    def create_widget(parent, control_name, control_value, trait,
                      label_class=None, user_data=None):
        """ Method to create the string widget.

        Parameters
        ----------
        parent: QWidget (mandatory)
            the parent widget
        control_name: str (mandatory)
            the name of the control we want to create
        control_value: str (mandatory)
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
            a two element tuple of the form (control widget: QLineEdit,
            associated label: QLabel)
        """
        # Create the widget that will be used to fill a string
        try:
            str_value = str(control_value)
        except TypeError:
            try:
                str_value = repr(control_value)
            except TypeError:
                str_value = ' &lt;%s&gt;' % type(control_value).__name__

        widget = Qt.QLabel(
            '<style>background-color: gray; text-color: red;</style>'
            + str_value, parent)
        widget.setEnabled(False)

        # Create the label associated with the string widget
        control_label = getattr(trait, 'label', control_name)
        if label_class is None:
            label_class = Qt.QLabel
        if control_label is not None:
            label = label_class(control_label, parent)
        else:
            label = None

        return (widget, label)

    @staticmethod
    def update_controller(controller_widget, control_name, control_instance,
                          reset_invalid_value=False, *args, **kwargs):
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
        control_instance: QLineEdit (mandatory)
            the instance of the controller widget control we want to
            synchronize with the controller
        """
        pass

    @staticmethod
    def update_controller_widget(controller_widget, control_name,
                                 control_instance):
        """ Update one element of the controller widget.

        At the end the controller widget user editable parameter with the
        name 'control_name' will match the controller trait value with the same
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
        try:
            test = control_instance.setText
        except ReferenceError:
            # widget deleted in the meantime
            return

        if sip.isdeleted(control_instance.__init__.__self__):
            NonEditableControlWidget.disconnect(
                controller_widget, control_name, control_instance)
            return

        # Get the trait value
        new_controller_value = getattr(
            controller_widget.controller, control_name, traits.Undefined)
        try:
            str_value = str(new_controller_value)
        except TypeError:
            try:
                str_value = repr(new_controller_value)
            except TypeError:
                str_value = ' &lt;%s&gt;' % type(new_controller_value).__name__
        control_instance.setText(str_value)

    @classmethod
    def connect(cls, controller_widget, control_name, control_instance):
        """ Connect a 'Str' or 'String' controller trait and a
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
        pass


    @staticmethod
    def disconnect(controller_widget, control_name, control_instance):
        """ Disconnect a 'Str' or 'String' controller trait and a
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
        pass
