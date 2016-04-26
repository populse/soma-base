#
# SOMA - Copyright (C) CEA, 2015
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
#

# System import
import re
import logging
import sys
import traits.api as traits

# Define the logger
logger = logging.getLogger(__name__)

# Soma import
from soma.qt_gui.qt_backend import QtCore
from .Str import StrControlWidget

if sys.version_info[0] >= 3:
    unicode = str


class IntControlWidget(StrControlWidget):

    """ Control to enter an integer.
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

        # Get the control current value: format the int string
        # Valid int strings are: +1, -1, 1
        control_text = control_instance.text()
        if type(control_text) not in (str, unicode):
            # old QString with PyQt API v1
            control_text = unicode(control_text)
        control_value = re.sub("^([-+])", "", control_text, count=1)

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
            control_palette.setColor(
                control_instance.backgroundRole(), QtCore.Qt.yellow)
            is_valid = True

        # If the control value is empty, the control is not valid and the
        # backgound color of the control is red
        else:
            control_palette.setColor(
                control_instance.backgroundRole(), QtCore.Qt.red)

        # Set the new palette to the control instance
        control_instance.setPalette(control_palette)

        return is_valid

    @staticmethod
    def update_controller(controller_widget, control_name, control_instance,
                          reset_invalid_value, *args, **kwargs):
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
        if IntControlWidget.is_valid(control_instance):

            # Get the control value
            if control_instance.text() == "":
                new_trait_value = traits.Undefined
            else:
                new_trait_value = int(control_instance.text())

            # Set the control value to the controller associated trait
            setattr(controller_widget.controller, control_name,
                    new_trait_value)
            logger.debug(
                "'IntControlWidget' associated controller trait '{0}' "
                "has been updated with value '{1}'.".format(
                    control_name, new_trait_value))
        elif reset_invalid_value:
            # invalid, reset GUI to older value
            old_trait_value = getattr(controller_widget.controller,
                                      control_name)
            if old_trait_value is traits.Undefined:
                control_instance.setText("")
            else:
                control_instance.setText(unicode(old_trait_value))

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
        control_instance: QLineEdit (mandatory)
            the instance of the controller widget control we want to
            synchronize with the controller
        """
        # Get the trait value
        new_controller_value = getattr(
            controller_widget.controller, control_name, traits.Undefined)

        # Set the trait value to the int control
        if new_controller_value is traits.Undefined:
            control_instance.setText("")
        else:
            control_instance.setText(unicode(new_controller_value))
        logger.debug("'IntControlWidget' has been updated with value "
                     "'{0}'.".format(new_controller_value))
