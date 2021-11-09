# -*- coding: utf-8 -*-

import re
import sys

import sip

from soma.qt_gui.qt_backend import QtCore, QtGui
from .Str import StrControlWidget
from soma.undefined import undefined

class FloatControlWidget(StrControlWidget):

    """ Control to enter a float.
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

        # Get the control current value: format the float string
        # Valid float strings are: +1, -1, 1, 1.1
        control_text = control_instance.text()
        if not isinstance(control_text, str):
            # old QString with PyQt API v1
            control_text = str(control_text)
        control_value = control_text.replace(".", "", 1)
        control_value = re.sub("^([-+])", "", control_value, count=1)

        red = QtGui.QColor(255, 220, 220)
        yellow = QtGui.QColor(255, 255, 200)

        # If the control value contains only digits, the control is valid and
        # the backgound color of the control is white
        is_valid = False
        if control_value.isdigit():
            control_palette.setColor(
                control_instance.backgroundRole(), QtCore.Qt.white)
            is_valid = True

        # If the control value is optional, the control is valid and the
        # backgound color of the control is yellow
        elif control_instance.optional is True and control_value == "":
            control_palette.setColor(control_instance.backgroundRole(), yellow)
            is_valid = True

        # If the control value is empty, the control is not valid and the
        # backgound color of the control is red
        else:
            control_palette.setColor(control_instance.backgroundRole(), red)

        # Set the new palette to the control instance
        control_instance.setPalette(control_palette)

        return is_valid

    @staticmethod
    def update_controller(controller_widget, control_name, control_instance,
                          reset_invalid_value=False, *args, **kwarg):
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
        if FloatControlWidget.is_valid(control_instance):

            # Get the control value
            if control_instance.text() == "":
                new_value = undefined
            else:
                new_value = float(control_instance.text())

            protected = controller_widget.controller.field(
                control_name).metadata.get('protected', False)
            # value is manually modified: protect it
            if getattr(controller_widget.controller, control_name) \
                    != new_value:
                controller_widget.controller.set_metadata(control_name, 'protected', True)
            # Set the control value to the controller associated field
            try:
                setattr(controller_widget.controller, control_name,
                        new_value)
                return
            except ValidationError:
                if not protected:
                    controller_widget.controller.set_metadata(control_name, 'protected', False)

        if reset_invalid_value:
            # invalid, reset GUI to older value
            old_value = getattr(controller_widget.controller,
                                      control_name)
            if old_value is undefined:
                control_instance.setText("")
            else:
                control_instance.setText(str(old_value))

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
            test = control_instance.setText
        except ReferenceError:
            # widget deleted in the meantime
            return

        if sip.isdeleted(control_instance.__init__.__self__):
            FloatControlWidget.disconnect(controller_widget, control_name,
                                          control_instance)
            return

        # Get the field value
        new_controller_value = getattr(
            controller_widget.controller, control_name, undefined)

        # Set the field value to the float control
        if new_controller_value is undefined:
            control_instance.setText("")
        else:
            control_instance.setText(str(new_controller_value))
