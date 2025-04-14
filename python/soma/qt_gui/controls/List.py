# -*- coding: utf-8 -*-
#
# SOMA - Copyright (C) CEA, 2015
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
#

# System import
import os
import logging
from functools import partial
import six
from six.moves import range

# Define the logger
logger = logging.getLogger(__name__)

# Soma import
from soma.qt_gui import qt_backend
from soma.qt_gui.qt_backend import QtGui, QtCore
from soma.utils.functiontools import SomaPartial
from soma.controller import trait_ids
from soma.controller import Controller
from soma.qt_gui.controller_widget import ControllerWidget, get_ref, weak_proxy
import traits.api as traits
import json
import csv
import sys
import sip

from six.moves import cStringIO as StringIO

# Qt import
try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

QtCore.QResource.registerResource(os.path.join(os.path.dirname(
    os.path.dirname(__file__)), 'resources', 'widgets_icons.rcc'))


class ListController(Controller):

    """ Dummy list controller to simplify the creation of a list widget
    """
    pass


class ListControlWidget(object):

    """ Control to enter a list of items.
    """

    #
    # Public members
    #

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
        # Initialized the output
        valid = True

        # If the trait is optional, the control is valid
        if control_instance.trait.optional is True:
            return valid

        # Go through all the controller widget controls
        controller_widget = control_instance.controller_widget
        for control_name, control_groups \
                in six.iteritems(controller_widget._controls):

            if not control_groups:
                continue
            # Unpack the control item
            trait, control_class, control_instance, control_label \
                = next(iter(control_groups.values()))

            # Call the current control specific check method
            valid = control_class.is_valid(control_instance)

            # Stop checking if a wrong control has been found
            if not valid:
                break

        return valid

    @classmethod
    def check(cls, control_instance):
        """ Check if a controller widget list control is filled correctly.

        Parameters
        ----------
        cls: ListControlWidget (mandatory)
            a ListControlWidget control
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
            emitted.
        control_instance: QFrame (mandatory)
            the control widget we want to validate
        """
        pass

    @staticmethod
    def create_widget(parent, control_name, control_value, trait,
                      label_class=None, max_items=0, user_data=None):
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
        max_items: int (optional)
            display at most this number of items. Defaults to 0: no limit.

        Returns
        -------
        out: 2-uplet
            a two element tuple of the form (control widget: ,
            associated labels: (a label QLabel, the tools QWidget))
        """
        # Get the inner trait: expect only one inner trait
        # note: trait.inner_traits might be a method (ListInt) or a tuple
        # (List), whereas trait.handler.inner_trait is always a method
        if len(trait.handler.inner_traits()) == 1:
            inner_trait = trait.handler.inner_traits()[0]
        elif len(trait.handler.inner_traits()) == 0:
            # maybe a generic list, or a compound trait
            if hasattr(trait.handler, 'handlers') \
                    and len(trait.handler.handlers) > 0 \
                    and hasattr(trait.handler.handlers[0], 'inner_traits') \
                    and len(trait.handler.handlers[0].inner_traits()) > 0:
                inner_trait = trait.handler.handlers[0].inner_traits()[0]
            else:
                # can't determine type, fallback to string
                inner_trait = traits.Str()
        else:
            raise Exception(
                "Expect only one inner trait in List control. Trait '{0}' "
                "inner trait is '{1}'.".format(control_name,
                                               trait.handler.inner_traits()))

        if control_value is traits.Undefined:
            control_value = []
        elif not isinstance(control_value, (list, tuple)):
            # in nipype MultiPath, single values are not in a list
            control_value = [control_value]

        # Create the list widget: a frame
        parent = get_ref(parent)
        frame = QtGui.QFrame(parent=parent)
        #frame.setFrameShape(QtGui.QFrame.StyledPanel)
        frame.setFrameShape(QtGui.QFrame.NoFrame)

        # Create tools to interact with the list widget: expand or collapse -
        # add a list item - remove a list item
        tool_widget = QtGui.QWidget(parent)
        layout = QtGui.QHBoxLayout()
        layout.addStretch(1)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        tool_widget.setLayout(layout)
        # Create the tool buttons
        resize_button = QtGui.QToolButton()
        add_button = QtGui.QToolButton()
        delete_button = QtGui.QToolButton()
        layout.addWidget(resize_button)
        layout.addWidget(add_button)
        layout.addWidget(delete_button)
        # Set the tool icons
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/soma_widgets_icons/add")),
                       QtGui.QIcon.Normal, QtGui.QIcon.Off)
        add_button.setIcon(icon)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/soma_widgets_icons/delete")),
                       QtGui.QIcon.Normal, QtGui.QIcon.Off)
        delete_button.setIcon(icon)
        icon = QtGui.QIcon()
        icon.addPixmap(
            QtGui.QPixmap(_fromUtf8(":/soma_widgets_icons/nav_down")),
            QtGui.QIcon.Normal, QtGui.QIcon.Off)
        resize_button.setIcon(icon)
        resize_button.setFixedSize(30, 22)
        add_button.setFixedSize(40, 22)
        delete_button.setFixedSize(40, 22)

        menu = QtGui.QMenu()
        menu.addAction('Enter list',
                       partial(ListControlWidget.enter_list,
                               weak_proxy(parent), control_name,
                               weak_proxy(frame)))
        menu.addAction('Load list',
                       partial(ListControlWidget.load_list,
                               weak_proxy(parent), control_name,
                               weak_proxy(frame)))
        if isinstance(inner_trait.trait_type, traits.File) \
                or isinstance(inner_trait.trait_type, traits.Directory):
            menu.addAction('Select files',
                           partial(ListControlWidget.select_files,
                                   weak_proxy(parent),
                                   control_name, weak_proxy(frame)))
        add_button.setMenu(menu)

        menu = QtGui.QMenu()
        menu.addAction('Clear all',
                       partial(ListControlWidget.clear_all,
                               weak_proxy(parent), control_name,
                               weak_proxy(frame), trait.trait_type.minlen))
        delete_button.setMenu(menu)

        # Create a new controller that contains length 'control_value' inner
        # trait elements
        controller = ListController()

        if inner_trait.groups:
            del inner_trait.groups

        n = max_items
        if n == 0:
            n = len(control_value)

        for cnt, inner_control_values in enumerate(control_value[:n]):
            controller.add_trait(str(cnt), inner_trait)
            #if inner_trait.groups:
                #del trait(str(cnt)).groups
            setattr(controller, str(cnt), inner_control_values)

        # Create the associated controller widget
        controller_widget = ControllerWidget(
            controller, parent=frame, live=True,
            override_control_types=parent._defined_controls,
            user_data=user_data)
        controller_widget.setObjectName('inner_controller')
        controller_widget.setStyleSheet(
            'ControllerWidget#inner_controller { padding: 0px; }')

        # Store some parameters in the list widget
        frame.inner_trait = inner_trait
        frame.trait = trait
        frame.controller = controller
        frame.controller_widget = controller_widget
        frame.connected = False
        frame.max_items = max_items

        # Add the list controller widget to the list widget
        frame.setLayout(controller_widget.layout())
        frame.layout().setContentsMargins(0, 0, 0, 0)
        frame.setObjectName('inner_frame')
        frame.setStyleSheet('QFrame#inner_frame { padding: 0px; }')

        # Set some callback on the list control tools
        # Resize callback
        resize_hook = partial(
            ListControlWidget.expand_or_collapse, weak_proxy(frame),
            weak_proxy(resize_button))
        resize_button.clicked.connect(resize_hook)
        # Add list item callback
        add_hook = partial(
            ListControlWidget.add_list_item, weak_proxy(parent),
            control_name, weak_proxy(frame))
        add_button.clicked.connect(add_hook)
        # Delete list item callback
        delete_hook = partial(
            ListControlWidget.delete_list_item, weak_proxy(parent),
            control_name, weak_proxy(frame))
        delete_button.clicked.connect(delete_hook)

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

        return (frame, (label, tool_widget))

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
        # Get the list widget inner controller values
        new_trait_value = [
            getattr(control_instance.controller, str(i))
            for i in range(len(control_instance.controller.user_traits()))]

        #if not hasattr(control_instance, 'max_items'):
            #print('no max_items in:', control_instance)
        #else:
        if control_instance.max_items != 0 \
                and len(new_trait_value) == control_instance.max_items:
            old_value = getattr(controller_widget.controller, control_name)
            new_trait_value += old_value[control_instance.max_items:]

        updating = getattr(controller_widget, '_updating', False)
        controller_widget._updating = True

        protected = controller_widget.controller.is_parameter_protected(
            control_name)
        # value is manually modified: protect it
        if getattr(controller_widget.controller, control_name) \
                != new_trait_value:
            controller_widget.controller.protect_parameter(control_name)
        # Update the 'control_name' parent controller value
        try:
            setattr(controller_widget.controller, control_name,
                    new_trait_value)
        except Exception as e:
            print(e, file=sys.stderr)
            if not protected:
                controller_widget.controller.unprotect_parameter(control_name)

        controller_widget._updating = updating
        logger.debug(
            "'ListControlWidget' associated controller trait '{0}' has "
            "been updated with value '{1}'.".format(
                control_name, new_trait_value))

    @staticmethod
    def validate_all_values(controller_widget, control_instance):
        '''Performs recursively update_controller() on list elements to
        make the Controller instance values match values in widgets.
        '''
        for k, groups in six.iteritems(controller_widget._controls):
            for g, ctrl in six.iteritems(groups):
                ctrl[1].update_controller(controller_widget, k,
                                          control_instance,
                                          reset_invalid_value=True)
                if ctrl[1] is ListControlWidget:
                    frame = ctrl[2]
                    sub_cw = frame.controller_widget
                    for sub_k, sub_groups in six.iteritems(sub_cw._controls):
                        for sub_g, sub_ctrl in six.iteritems(sub_groups):
                            sub_ctrl[1].update_controller(
                                sub_cw, sub_k, sub_ctrl[2],
                                reset_invalid_value=True)


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
        # there are 2 Controller instances here:
        # * controller_widget.controller is the "official" edited controller,
        #   which contains a trait "control_name" with a list value
        # * control_instance.controller is a proxy Controller built here
        #   that represents the list items: elements keys are indexes.
        #   This controller has another widget (for list items):
        #   control_instance.controller_widget.
        try:
            was_connected = control_instance.connected
        except ReferenceError:
            # widget deleted in the meantime
            return
        if getattr(controller_widget, '_updating', False):
            return
        controller_widget._updating = True

        if sip.isdeleted(control_instance.__init__.__self__):
            ListControlWidget.disconnect(controller_widget, control_name,
                                         control_instance)
            return

        # One callback has not been removed properly
        if control_name in controller_widget.controller.user_traits():

            # Get the list widget current connection status
            was_connected = control_instance.connected

            # Disconnect the list controller and the inner list controller
            cls.disconnect(controller_widget, control_name, control_instance)
            control_instance.controller_widget.disconnect()

            # Get the 'control_name' list value from the top list controller
            trait_value = getattr(controller_widget.controller, control_name)
            if trait_value in (None, traits.Undefined):
                trait_value = []
            elif not isinstance(trait_value, (tuple, list)):
                # nipype MultiPath may have one item outside of a list
                trait_value = [trait_value]

            # Get the number of list elements in the controller associated
            # with the current list control
            len_widget = len(control_instance.controller.user_traits())

            # Parameter that is True if a user trait associated with the
            # current list control has changed
            user_traits_changed = False

            # Special case: some traits have been deleted to the top controller
            if len(trait_value) < len_widget:

                # Need to remove to the inner list controller some traits
                for i in range(len(trait_value), len_widget):
                    control_instance.controller.remove_trait(str(i))

                # Notify that some traits of the inner list controller have
                # been deleted
                user_traits_changed = True

            # Special case: some new traits have been added to the top
            # controller
            elif len(trait_value) > len_widget \
                    and (control_instance.max_items == 0
                         or len_widget < control_instance.max_items):

                # Need to add to the inner list controller some traits
                # with type 'inner_trait'
                for i in range(len_widget, len(trait_value)):
                    control_instance.controller.add_trait(
                        str(i), control_instance.inner_trait)

                # Notify that some traits of the inner list controller
                # have been added
                user_traits_changed = True

            # Update the controller associated with the current control
            n = len(trait_value)
            if control_instance.max_items != 0 \
                    and control_instance.max_items < n:
                n = control_instance.max_items
            for i in range(n):
                setattr(control_instance.controller, str(i), trait_value[i])

            # Connect the inner list controller
            control_instance.controller_widget.connect()

            # Emit the 'user_traits_changed' signal if necessary
            if user_traits_changed:
                control_instance.controller.user_traits_changed = True

                logger.debug(
                    "'ListControlWidget' inner controller has been updated:"
                    "old size '{0}', new size '{1}'.".format(
                        len_widget, len(trait_value)))

            # Restore the previous list controller connection status
            if was_connected:
                cls.connect(controller_widget, control_name, control_instance)

        else:
            logger.error("oups: control_name %s not in list controller "
              "traits: %s"
              % (control_name,
                 repr(list(
                    controller_widget.controller.user_traits().keys()))))
            # print cls, controller_widget, control_name, control_instance
            # print control_instance.controller
            # print control_instance.controller.user_traits()

        controller_widget._updating = False

    @classmethod
    def connect(cls, controller_widget, control_name, control_instance):
        """ Connect a 'List' controller trait and a 'ListControlWidget'
        controller widget control.

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

            # Connect also all list items
            inner_controls = control_instance.controller_widget._controls
            for (inner_control_name,
                 inner_control_groups) in six.iteritems(inner_controls):
                for group, inner_control \
                        in six.iteritems(inner_control_groups):

                    # Unpack the control item
                    inner_control_instance = inner_control[2]
                    inner_control_class = inner_control[1]

                    # Call the inner control connect method
                    inner_control_class.connect(
                        control_instance.controller_widget, inner_control_name,
                        inner_control_instance)

            # Update the list control connection status
            control_instance.connected = True

    @staticmethod
    def disconnect(controller_widget, control_name, control_instance):
        """ Disconnect a 'List' controller trait and a 'ListControlWidget'
        controller widget control.

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
    def add_list_item(controller_widget, control_name, control_instance):
        """ Append one element in the list controller widget.

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
        # Get the number of traits associated with the current list control
        # controller
        nb_of_traits = len(control_instance.controller.user_traits())
        if control_instance.max_items != 0 \
                and nb_of_traits >= control_instance.max_items:
            # don't display more.
            return
        trait_name = str(nb_of_traits)

        # Add the new trait to the inner list controller
        control_instance.controller.add_trait(
            trait_name, control_instance.inner_trait)
        control_instance._updating = True
        setattr(control_instance.controller, trait_name,
                control_instance.inner_trait.default)
        control_instance._updating = False

        # Update the list controller
        if hasattr(control_instance, '_controller_connections'):
            control_instance._controller_connections[0]()

        # control_instance.controller_widget.update_controller_widget()
        logger.debug("Add 'ListControlWidget' '{0}' new trait "
                     "callback.".format(trait_name))

    @staticmethod
    def delete_list_item(controller_widget, control_name, control_instance):
        """ Delete the last control element

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
        # Delete the last inserted control
        #print('delete_list_item', controller_widget, control_name, control_instance)

        # inner controller for list items
        controller = control_instance.controller
        keys = controller.user_traits().keys()
        keys = sorted([int(k) for k in keys])
        if not keys:
            print('no element to remove')
            return

        last_key = str(keys[-1])
        controller.remove_trait(last_key)

        # Update the list controller
        if hasattr(control_instance, '_controller_connections'):
            control_instance._controller_connections[0]()
        # notification will update the controller GUI.

    @staticmethod
    def expand_or_collapse(control_instance, resize_button):
        """ Callback to expand or collapse a 'ListControlWidget'.

        Parameters
        ----------
        control_instance: QFrame (mandatory)
            the list widget item
        resize_button: QToolButton
            the signal sender
        """
        # Change the icon depending on the button status
        icon = QtGui.QIcon()

        # Hide the control
        if control_instance.isVisible():
            control_instance.hide()
            icon.addPixmap(
                QtGui.QPixmap(_fromUtf8(":/soma_widgets_icons/nav_right")),
                QtGui.QIcon.Normal, QtGui.QIcon.Off)

        # Show the control
        else:
            control_instance.show()
            icon.addPixmap(
                QtGui.QPixmap(_fromUtf8(":/soma_widgets_icons/nav_down")),
                QtGui.QIcon.Normal, QtGui.QIcon.Off)

        # Set the new button icon
        resize_button.setIcon(icon)

    @staticmethod
    def enter_list(controller_widget, control_name, control_instance):
        controller_widget = get_ref(controller_widget)
        widget = ListValuesEditor(controller_widget, controller_widget,
                                  control_name)
        done = False
        while not done:
            if widget.exec_():
                parent_controller = controller_widget.controller
                elem_trait \
                    = parent_controller.trait(control_name).inner_traits[0]
                value = ListControlWidget.parse_list(
                    widget.textedit.toPlainText(),
                    widget.format_c.currentText(),
                    widget.separator_c.currentText(), elem_trait)
                if value is not None:
                    try:
                        setattr(parent_controller, control_name, value)
                    except Exception as e:
                        print(e)
                    done = True
                else:
                    r = QtGui.QMessageBox.warning(
                        controller_widget, 'Parsing error',
                        'Could not parse the text input',
                        QtGui.QMessageBox.Retry | QtGui.QMessageBox.Abort,
                        QtGui.QMessageBox.Retry)
                    if r == QtGui.QMessageBox.Abort:
                        done = True
            else:
                done = True
    @staticmethod
    def parse_list(text, format, separator, elem_trait):
        if format == 'JSON':
            formats = [format, 'CSV']
        elif format == 'CSV':
            formats = [format, 'JSON']
        else:
            formats = ['JSON', 'CSV']
        for format in formats:
            if format == 'JSON':
                try:
                    parsed = json.loads(text)
                    return parsed
                except Exception:
                    pass
            elif format == 'CSV':
                try:
                    reader = csv.reader(
                        text.split('\n'), delimiter=str(separator),
                        quotechar='"', quoting=csv.QUOTE_MINIMAL,
                        skipinitialspace=True)
                    ctrait = traits.TraitCastType(
                        type(elem_trait.default))
                    c = traits.HasTraits()
                    c.add_trait('x', ctrait)
                    parsed = []
                    for x in reader:
                        if isinstance(x, list):
                            for y in x:
                                c.x = y
                                parsed.append(c.x)
                        else:
                            c.x = x
                            parsed.append(c.x)
                    return parsed
                except Exception:
                    pass
        # could not parse
        return None


    @staticmethod
    def load_list(controller_widget, control_name, control_instance):
        controller_widget = get_ref(controller_widget)
        control_instance = get_ref(control_instance)

        # get widget via a __self__ in a method, because control_instance may
        # be a weakproxy.
        widget = control_instance.__repr__.__self__

        fname = qt_backend.getOpenFileName(
            widget, "Open file", "", "", None,
            QtGui.QFileDialog.DontUseNativeDialog)
        if fname:
            parent_controller = controller_widget.controller
            elem_trait = parent_controller.trait(control_name).inner_traits[0]
            text = open(fname).read()
            if fname.endswith('.csv'):
                format = 'CSV'
            else:
                format = 'JSON'
            value = ListControlWidget.parse_list(text, format, ',', elem_trait)
            if value is not None:
                setattr(parent_controller, control_name, value)
            else:
                QtGui.QMessageBox.warning(
                    controller_widget, 'Parsing error',
                    'Could not parse the input file',
                    QtGui.QMessageBox.Cancel, QtGui.QMessageBox.Cancel)

    @staticmethod
    def select_files(controller_widget, control_name, control_instance):
        control_instance = get_ref(control_instance)
        parent_controller = controller_widget.controller
        elem_trait = parent_controller.trait(control_name).inner_traits[0]
        fnames = None
        current_dir = os.path.join(os.getcwd(), os.pardir)
        if isinstance(elem_trait.trait_type, traits.Directory):

            # Create a dialog to select a directory
            fdialog = QtGui.QFileDialog(
                control_instance, "Open directories",
                current_dir)
            fdialog.setOptions(QtGui.QFileDialog.ShowDirsOnly |
                               QtGui.QFileDialog.DontUseNativeDialog)
            fdialog.setFileMode(QtGui.QFileDialog.Directory)
            fdialog.setModal(True)
            if fdialog.exec_():
                fnames = fdialog.selectedFiles()
        else:
            if elem_trait.output:
                fdialog = QtGui.QFileDialog(
                    control_instance, "Output files",
                    current_dir)
                fdialog.setOptions(QtGui.QFileDialog.DontUseNativeDialog)
                fdialog.setFileMode(QtGui.QFileDialog.AnyFile)
                fdialog.setModal(True)
                if fdialog.exec_():
                    fnames = fdialog.selectedFiles()
            else:
                fdialog = QtGui.QFileDialog(
                    control_instance, "Open files",
                    current_dir)
                fdialog.setOptions(QtGui.QFileDialog.DontUseNativeDialog)
                fdialog.setFileMode(QtGui.QFileDialog.ExistingFiles)
                fdialog.setModal(True)
                if fdialog.exec_():
                    fnames = fdialog.selectedFiles()

        # Set the selected files to the path sub control
        if fnames is not None:
            old_value = getattr(parent_controller, control_name)
            new_value = old_value + fnames
            setattr(parent_controller, control_name, new_value)


    @staticmethod
    def clear_all(controller_widget, control_name, control_instance, minlen):
        controller = control_instance.controller
        parent_controller = controller_widget.controller
        value = parent_controller.trait(control_name).default
        setattr(parent_controller, control_name, value)


class ListValuesEditor(QtGui.QDialog):

    def __init__(self, parent, controller_widget, control_name):

        super(ListValuesEditor, self).__init__(parent)

        self.controller_widget = controller_widget
        self.control_name = control_name
        self.format = 'JSON'
        self.separator = ','
        self.modified = False

        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)
        textedit = QtGui.QTextEdit()
        layout.addWidget(textedit)
        hlayout2 = QtGui.QHBoxLayout()
        layout.addLayout(hlayout2)

        hlayout2.addWidget(QtGui.QLabel('Format:'))
        format_c = QtGui.QComboBox()
        hlayout2.addWidget(format_c)
        hlayout2.addWidget(QtGui.QLabel('Separator:'))
        sep_c = QtGui.QComboBox()
        hlayout2.addWidget(sep_c)

        format_c.addItem('JSON')
        format_c.addItem('CSV')

        sep_c.addItem(',')
        sep_c.addItem(';')
        sep_c.addItem(' ')

        hlayout2.addStretch(1)
        ok = QtGui.QPushButton('OK')
        cancel = QtGui.QPushButton('Cancel')
        hlayout2.addWidget(ok)
        hlayout2.addWidget(cancel)

        ok.pressed.connect(self.accept)
        cancel.pressed.connect(self.reject)

        parent_controller = controller_widget.controller
        value = getattr(parent_controller, control_name)

        text = json.dumps(value)
        textedit.setText(text)

        self.textedit = textedit
        self.format_c = format_c
        self.separator_c = sep_c
        self.internal_change = False

        textedit.textChanged.connect(self.set_modified)
        format_c.currentIndexChanged.connect(self.format_changed)
        sep_c.currentIndexChanged.connect(self.separator_changed)

    def set_modified(self):
        if self.internal_change:
            self.internal_change = False
            return
        self.modified = True
        self.textedit.textChanged.disconnect(self.set_modified)

    def format_changed(self, index):
        self.format = self.format_c.itemText(index)
        self.internal_change = True
        if self.modified:
            return
        self.textedit.setText(self.text_repr())

    def text_repr(self):
        parent_controller = self.controller_widget.controller
        value = getattr(parent_controller, self.control_name)
        if self.format == 'JSON':
            text = json.dumps(value)
        elif self.format == 'CSV':
            text_io = StringIO()
            writer = csv.writer(
                text_io, delimiter=str(self.separator),
                quotechar='"', quoting=csv.QUOTE_MINIMAL,
                skipinitialspace=True)
            writer.writerow(value)
            text = text_io.getvalue()
        else:
            raise ValueError('unsupported format %s' % self.format)
        return text

    def separator_changed(self, index):
        self.separator = self.separator_c.itemText(index)
        self.internal_change = True
        if self.modified:
            return
        self.textedit.setText(self.text_repr())
