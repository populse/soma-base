# -*- coding: utf-8 -*-

from soma.qt_gui.qt_backend import QtGui, QtCore
from soma.utils.functiontools import SomaPartial
from soma.qt_gui.timered_widgets import TimeredQLineEdit
from soma.utils.weak_proxy import weak_proxy
from .Str import StrControlWidget


class BytesControlWidget(StrControlWidget):

    """ Control to enter a bytes string.
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

        if control_value in (b'', None, traits.Undefined):
            if control_instance.optional:
                # If the control value is optional, the control is valid and
                # the backgound color of the control is yellow
                color = yellow
                is_valid = True
            else:
                color = red
                if control_value != b'':
                    # allow to reset value
                    is_valid = True

        else:
            is_valid = True

        # Set the new palette to the control instance
        control_palette.setColor(control_instance.backgroundRole(), color)
        control_instance.setPalette(control_palette)

        return is_valid

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
        # Update the controller only if the control is valid
        if BytesControlWidget.is_valid(control_instance):

            # Get the control value
            new_value = control_instance.value()
            if new_value not in (undefined, None):
                new_value = new_value.encode()

            # value is manually modified: protect it
            if getattr(controller_widget.controller, control_name) \
                    != new_value:
                controller_widget.controller.set_metadata(control_name, 'protected', True)
            # Set the control value to the controller associated trait
            setattr(controller_widget.controller, control_name,
                    new_value)
        elif reset_invalid_value:
            # invalid, reset GUI to older value
            old_trait_value = getattr(controller_widget.controller,
                                      control_name)
            control_instance.set_value(old_trait_value)
