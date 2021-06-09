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
from __future__ import print_function
import logging
import os
import sys
import six

# Define the logger
logger = logging.getLogger(__name__)

# Soma import
from soma.qt_gui import qt_backend
from soma.qt_gui.qt_backend import QtGui, QtCore, Qt
from soma.controller import trait_ids
from soma.qt_gui.timered_widgets import TimeredQLineEdit
from soma.functiontools import partial
from soma.sorted_dictionary import OrderedDict
from soma.functiontools import SomaPartial
import weakref
from soma.utils.weak_proxy import get_ref, weak_proxy
import traits.api as traits
import inspect
import sip

# Qt import
try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

qt_backend.set_qt_backend(compatible_qt5=True)
# setup notification in Qt GUI thread
qt_backend.init_traitsui_handler()


class ScrollControllerWidget(Qt.QScrollArea):

    """ Class that create a widget to set the controller parameters.

    The widget is placed in a scroll area when large sets of parameters have
    to be tuned.
    """

    def __init__(self, controller, parent=None, name=None, live=False,
                 hide_labels=False, select_controls=None,
                 disable_controller_widget=False, override_control_types=None,
                 user_data=None, userlevel=0):
        """ Method to initilaize the ScrollControllerWidget class.

        Parameters
        ----------
        controller: derived Controller instance (mandatory)
            a class derived from the Controller class we want to parametrize
            with a widget.
        parent: QtGui.QWidget (optional, default None)
            the controller widget parent widget.
        name: (optional, default None)
            the name of this controller widget
        live: bool (optional, default False)
            if True, synchronize the edited values in the widget with the
            controller values on the fly,
            otherwise, wait synchronization instructions to update the
            controller values.
        hide_labels: bool (optional, default False)
            if True, don't show the labels associated with the controls
        select_controls: str (optional, default None)
            parameter to select specific conrtoller traits. Authorized options
            are 'inputs' or 'outputs'.
        disable_controller_widget: bool (optional, default False)
            if True disable the controller widget.
        override_control_types: dict (optional)
            if given, this is a "factory" dict assigning new controller editor
            types to some traits types.
        user_data: any type (optional)
            optional user data that can be accessed by individual control
            editors
        userlevel: int
            the current user level: some traits may be marked with a non-zero userlevel, and will only be visible if the ControllerWidget userlevel is more than (or equal) the trait level.
        """
        # Inheritance
        super(ScrollControllerWidget, self).__init__(parent)

        self.user_data = user_data

        # Allow the application to resize the scroll area items
        self.setWidgetResizable(True)
        self.setSizePolicy(QtGui.QSizePolicy.Preferred,
                           QtGui.QSizePolicy.Preferred)

        # Display a surounding box
        self.setFrameShape(QtGui.QFrame.StyledPanel)

        # Create the controller widget
        self.controller_widget = ControllerWidget(
            controller, parent, name, live, hide_labels, select_controls,
            override_control_types=override_control_types, user_data=user_data,
            userlevel=userlevel)
        self.controller_widget.layout().setContentsMargins(2, 2, 2, 2)
        self.controller_widget.setSizePolicy(QtGui.QSizePolicy.Expanding,
                                             QtGui.QSizePolicy.Preferred)

        # Enable / disabled the controller widget
        self.controller_widget.setEnabled(not disable_controller_widget)

        # Set the controller widget in the scroll area
        self.setWidget(self.controller_widget)

    def __del__(self):
        # disconnect underlying ControllerWidget so that it can be deleted.
        self.controller_widget.disconnect()

    @property
    def userlevel(self):
        if hasattr(self, 'controller_widget'):
            return self.controller_widget.userlevel
        return 0

    @userlevel.setter
    def userlevel(self, value):
        if hasattr(self, 'controller_widget'):
            self.controller_widget.userlevel = value

    def update_controller(self):
        self.controller_widget.update_controller()


class DeletableLineEdit(QtGui.QWidget):

    """ Close button + line editor, used for modifiable key labels
    """
    userModification = QtCore.Signal()
    buttonPressed = QtCore.Signal()

    def __init__(self, text=None, parent=None):
        super(DeletableLineEdit, self).__init__(parent)
        layout = QtGui.QHBoxLayout()
        self.setLayout(layout)
        delete_button = QtGui.QToolButton()
        layout.addWidget(delete_button)
        # Set the tool icons
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(
            _fromUtf8(":/soma_widgets_icons/delete")),
            QtGui.QIcon.Normal, QtGui.QIcon.Off)
        delete_button.setIcon(icon)
        self.line_edit = TimeredQLineEdit(text)
        layout.addWidget(self.line_edit)
        self.line_edit.userModification.connect(self.userModification)
        delete_button.pressed.connect(self.buttonPressed)

    def text(self):
        return self.line_edit.text()

    def setText(self, text):
        self.line_edit.setText(text)


class ControllerWidget(QtGui.QWidget):

    """ Class that create a widget to set the controller parameters.
    """

    # Parameter to store the mapping between the string trait descriptions and
    # the associated control classes
    _defined_controls = {}

    def __init__(self, controller, parent=None, name=None, live=False,
                 hide_labels=False, select_controls=None,
                 editable_labels=False, override_control_types=None,
                 user_data=None, userlevel=0):
        """ Method to initilaize the ControllerWidget class.

        Parameters
        ----------
        controller: derived Controller instance (mandatory)
            a class derived from the Controller class we want to parametrize
            with a widget.
        parent: QtGui.QWidget (optional, default None)
            the controller widget parent widget.
        name: (optional, default None)
            the name of this controller widget
        live: bool (optional, default False)
            if True, synchronize the edited values in the widget with the
            controller values on the fly,
            otherwise, wait the synchronization instruction to update the
            controller values.
        hide_labels: bool (optional, default False)
            if True, don't show the labels associated with the controls
        select_controls: str (optional, default None)
            parameter to select specific conrtoller traits. Authorized options
            are 'inputs' or 'outputs'.
        editable_labels: bool (optional, default False)
            if True, labels (trait keys) may be edited by the user, their
            modification will trigger a signal.
        override_control_types: dict (optional)
            if given, this is a "factory" dict assigning new controller editor
            types to some traits types.
        user_data: any type (optional)
            optional user data that can be accessed by individual control
            editors
        userlevel: int
            the current user level: some traits may be marked with a non-zero userlevel, and will only be visible if the ControllerWidget userlevel is more than (or equal) the trait level.
        """
        # Inheritance
        super(ControllerWidget, self).__init__(parent)

        self._userlevel = userlevel

        if override_control_types:
            # copy dict
            self._defined_controls = dict(self.__class__._defined_controls)
            self._defined_controls.update(override_control_types)

        QtCore.QResource.registerResource(os.path.join(os.path.dirname(
            os.path.dirname(__file__)), 'resources', 'widgets_icons.rcc'))

        # Class parameters
        if controller is None:
            raise ValueError('null controller')
        if controller is traits.Undefined:
            raise ValueError('undefined controller')
        self.controller = controller
        self.live = live
        self.hide_labels = hide_labels
        self.select_controls = select_controls
        # Parameter to store the connection status between the
        # controller widget and the controller
        self.connected = False
        # Parameter to store all the controller widget controls:
        # the keys correspond to the control name (a control name is
        # associated to a controller trait with the same name), the
        # dictionary elements are 4-uplets of the form (trait, control_class,
        # control_instance, control_label).
        self._controls = {}
        self._keys_connections = {}
        self.editable_labels = editable_labels
        self.user_data = user_data

        # If possilbe, set the widget name
        if name:
            self.setObjectName(name)

        # Create the layout of the controller widget
        # We will add all the controls to this layout
        self._grid_layout = QtGui.QGridLayout()
        self._grid_layout.setAlignment(QtCore.Qt.AlignTop)
        self._grid_layout.setSpacing(3)
        self._grid_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._grid_layout)

        self._groups = OrderedDict()

        # Create all the layout controls associated with the controller values
        # we want to tune (ie the user traits)
        self._create_controls()
        self.connect_keys()

        # Start the event loop that check for wrong edited fields (usefull
        # when we work off line, otherwise the traits make the job but it is
        # still user friendly).
        self._check()

        # Set the synchrinization between this object and the input controller:
        # 1) synchronize the edited values in the widget with the controller
        # values on the fly
        if self.live:
            self.connect()

        # 2) initialize the controller widget with the controller values and
        # wait synchronization instructions to update the controller values.
        else:
            self.update_controller_widget()

    #
    # Public members
    #

    def is_valid(self):
        """ Check that all edited fields are correct.

        Returns
        -------
        valid: bool
            True if all the controller widget controls are correctly filled,
            False otherwise
        """
        # Initilaized the output
        valid = True

        # Go through all the controller widget controls
        for control_name, control_groups in six.iteritems(self._controls):
            for group_name, control in six.iteritems(control_groups):

                # Unpack the control item
                trait, control_class, control_instance, control_label = control

                # Call the current control specific check method
                valid = control_class.is_valid(control_instance)

                # Stop checking if a wrong control has been found
                if not valid:
                    break

        return valid

    @property
    def userlevel(self):
        return self._userlevel

    @userlevel.setter
    def userlevel(self, value):
        self._userlevel = value
        self.update_controls()

    def update_controller(self):
        """ Update the controller.

        At the end the controller traits values will match the controller
        widget user defined parameters.
        """
        # Go through all the controller widget controls
        for control_name, control_groups in six.iteritems(self._controls):
            for group_name, control in six.iteritems(control_groups):

                # Unpack the control item
                trait, control_class, control_instance, control_label = control

                # Call the current control specific update controller method
                control_class.update_controller(self, control_name,
                                                control_instance)

    def update_controller_widget(self):
        """ Update the controller widget.

        At the end the controller widget user editable parameters will match
        the controller traits values.
        """
        # Go through all the controller widget controls
        for control_name, control_groups in six.iteritems(self._controls):
            for group_name, control in six.iteritems(control_groups):

                # Unpack the control item
                trait, control_class, control_instance, control_label = control

                # Call the current control specific update controller widget
                # method
                control_class.update_controller_widget(self, control_name,
                                                      control_instance)

    def connect(self):
        """ Connect the controller trait and the controller widget controls

        At the end al control will be connected with the associated trait, and
        when a 'user_traits_changed' signal is emited, the controls are updated
        (ie, deleted if necessary).
        """
        # If the controller and controller widget are not yet connected
        if not self.connected:

            # Go through all the controller widget controls
            for control_name, control_groups in six.iteritems(self._controls):
                for group_name, control in six.iteritems(control_groups):

                    # Unpack the control item
                    trait, control_class, control_instance, control_label \
                        = control

                    # Call the current control specific connection method
                    logger.debug("Connecting control '{0}: {1}'...".format(
                        control_name, control_instance))
                    control_class.connect(self, control_name, control_instance)

            # Add an event connected with the 'user_traits_changed' controller
            # signal: update the controls
            self.controller.on_trait_change(
                self.update_controls, "user_traits_changed", dispatch='ui')

            # if 'visible_groups' is a trait, connect it to groups
            if self.controller.trait('visible_groups'):
                self.controller.on_trait_change(
                    self.groups_vibility_changed, 'visible_groups',
                    dispatch='ui')

            # Update the controller widget values
            self.update_controller_widget()

            # notifications should be removed when the GUI is destroyed
            # (on C++ side)
            self.destroyed.connect(
                partial(self.static_disconnect, self.controller,
                        self.update_controls, self.groups_vibility_changed,
                        self._controls))
            # Update the connection status
            self.connected = True

    def connect_keys(self):
        if not self.editable_labels or self._keys_connections:
            return
        keys_connect = {}
        # Go through all the controller widget controls
        for control_name, control_groups in six.iteritems(self._controls):
            for group_name, control in six.iteritems(control_groups):
                hook1 = partial(self.__class__._key_modified,
                                weakref.proxy(self), control_name)
                hook2 = partial(self.__class__._delete_key,
                                weakref.proxy(self), control_name)
                #control = self._controls[control_name]
                label_control = control[3]
                if isinstance(label_control, tuple):
                    label_control = label_control[0]
                label_control.userModification.connect(hook1)
                label_control.buttonPressed.connect(hook2)
                keys_connect[control_name] = (label_control, hook1, hook2)
        self._keys_connections = keys_connect

    @staticmethod
    def static_disconnect(controller, update_controls, groups_vibility_changed,
                          controls, widget):
        ''' disconnect() cannot be called at the right time.
        static_disconnect() is called via a Qt signat when the widget is
        destroyed. But the python part is already destroyed then.
        '''
        controller.on_trait_change(
            update_controls, "user_traits_changed", remove=True)

        # if 'visible_groups' is a trait, connect it to groups
        if controller.trait('visible_groups'):
            controller.on_trait_change(
                groups_vibility_changed, 'visible_groups', remove=True)

        # Go through all the controller widget controls
        for control_name, control_groups in six.iteritems(controls):
            for group_name, control in six.iteritems(control_groups):

                # Unpack the control item
                trait, control_class, control_instance, control_label \
                    = control

                # Call the current control specific disconnection method
                try:
                    control_class.disconnect(widget, control_name,
                                             control_instance)
                except Exception:
                    pass  # probably something already deleted

    def disconnect(self):
        """ Disconnect the controller trait and the controller widget controls
        """
        # If the controller and controller widget are connected
        if self.connected:

            # Remove the 'update_controls' event connected with the
            # 'user_traits_changed' controller signal
            self.controller.on_trait_change(
                self.update_controls, "user_traits_changed", remove=True)

            # if 'visible_groups' is a trait, connect it to groups
            if self.controller.trait('visible_groups'):
                self.controller.on_trait_change(
                    self.groups_vibility_changed, 'visible_groups',
                    remove=True)

            # Go through all the controller widget controls
            for control_name, control_groups in six.iteritems(self._controls):
                for group_name, control in six.iteritems(control_groups):

                    # Unpack the control item
                    trait, control_class, control_instance, control_label \
                        = control

                    # Call the current control specific disconnection method
                    try:
                        control_class.disconnect(self, control_name,
                                                 control_instance)
                    except Exception:
                        pass  # probably something already deleted

            # Update the connection status
            self.connected = False

    def disconnect_keys(self):
        for control_name, connections in six.iteritems(self._keys_connections):
            label_widget, hook1, hook2 = connections
            label_widget.userModification.disconnect(hook1)
            label_widget.buttonPressed.disconnect(hook2)
        self._keys_connections = {}

    def update_controls(self):
        """ Event to refresh controller widget controls and intern parameters.

        The refresh is done off line, ie. we need first to disconnect the
        controller and the controller widget.
        """
        # Get the controller traits
        user_traits = self.controller.user_traits()

        # Assess the refreshing is done off line
        was_connected = self.connected
        if was_connected:
            self.disconnect()
        self.disconnect_keys()

        # Go through all the controller widget controls
        to_remove_controls = []
        for control_name, control_groups in six.iteritems(self._controls):
            for group_name, control in six.iteritems(control_groups):

                # Message
                logger.debug(
                    "Check if we need to update '{0}': trait in '{1}' "
                    "different from '{2}'?".format(
                        control_name, control, user_traits.get(control_name)))

                # Unpack the control item
                trait, control_class, control_instance, control_label = control

                # If the the controller trait is different from the trait
                # associated with the control
                if user_traits.get(control_name) != trait:

                    # Close and schedule for deletation the control widget
                    control_instance.close()
                    control_instance.deleteLater()

                    # Close and schedule for deletation the control labels
                    if isinstance(control_label, tuple):
                        for label in control_label:
                            if not sip.isdeleted(label):
                                label.close()
                                label.deleteLater()
                    elif control_label:
                        if not sip.isdeleted(control_label):
                            control_label.close()
                            control_label.deleteLater()

                    # Store the controls to be removed
                    to_remove_controls.append(control_name)

        # Delete all dead controls from the class '_controls' intern parameter
        for control_name in to_remove_controls:
            logger.debug("Delete control '{0}'.".format(control_name))
            del self._controls[control_name]

        # Recreate all the layout controls associated with the controller
        # values we want to tune (ie the user_traits): this procedure check
        # if the control has not already been created.
        self._create_controls()

        # Restore the connection status
        if was_connected:
            self.connect()
        self.connect_keys()

        # Update the widget geometry
        self.updateGeometry()

    #
    # Private members
    #

    def _check(self):
        """ Check that all edited fields are correct.

        At the end the controls with wrong values will be colored in red.
        """
        # Go through all the controller widget controls
        for control_name, control_groups in six.iteritems(self._controls):
            for group_name, control in six.iteritems(control_groups):

                # Unpack the control item
                trait, control_class, control_instance, control_label = control

                # Call the current control specific check method
                control_class.check(control_instance)

    def _create_controls(self):
        """ Method that will create a control for each user trait of the
        controller.

        Controller trait parameters that cannot be maped to controls
        will not appear in the user interface.
        """
        # Select only the controller traits of interest
        all_traits = self.controller.user_traits()
        if self.select_controls is None:
            selected_traits = all_traits
        elif self.select_controls == "inputs":
            selected_traits = dict(
                (trait_name, trait)
                for trait_name, trait in six.iteritems(all_traits)
                if not trait.output)
        elif self.select_controls == "outputs":
            selected_traits = dict(
                (trait_name, trait)
                for trait_name, trait in six.iteritems(all_traits)
                if trait.output)
        else:
            raise Exception(
                "Unrecognized 'select_controls' option '{0}'. Valid "
                "options are 'inputs' or 'outputs'.".format(self.select_controls))

        # Go through all the controller user traits
        skipped = set(['visible_groups'])
        for trait_name, trait in six.iteritems(selected_traits):
            if trait_name in skipped:
                continue
            # Create the widget
            self.create_control(trait_name, trait)

    def create_control(self, trait_name, trait):
        """ Create a control associated to a trait.

        Parameters
        ----------
        trait_name: str (mandatory)
            the name of the trait from which we want to create a control. The
            control widget will share the same name
        trait: Trait (mandatory)
            a trait item
        """
        # Search if the current trait has already been processed
        control_groups = self._controls.get(trait_name)
        control_instances = []
        control_labels = []

        # If no control has been found in the class intern parameters
        if control_groups is None:

            # Call the search function that will map the trait type to the
            # corresponding control type
            control_class = self.get_control_class(trait)

            # If no control has been found, skip this trait and print
            # an error message. Note that the parameter will not be
            # accessible in the user interface.
            if control_class is None:
                logger.error(
                    "No control defined for trait '{0}': {1}. This "
                    "parameter will not be accessible in the "
                    "user interface.".format(trait_name, trait_ids(trait)))
                return

            # handle groups
            layouts = []
            groups = trait.groups
            if groups:
                for group in groups:
                    group_widget = self._groups.get(group)
                    if group_widget is None:
                        group_widget = self._create_group_widget(group)
                        self._groups[group] = group_widget
                    layouts.append(group_widget.hideable_widget.layout())
            else:
                layouts.append(self._grid_layout)

            group = None
            for i, layout in enumerate(layouts):
                if groups:
                    group = groups[i]
                control_instance, control_label \
                      = self._create_control_in_layout(trait_name, trait,
                                                       layout, group)
                control_instances.append(control_instance)
                if control_label:
                    if not isinstance(control_label, tuple):
                        control_label = [control_label]
                    control_labels += list(control_label)
                    if isinstance(control_label[0], QtGui.QLabel):
                        control_label[0].setTextInteractionFlags(
                            QtCore.Qt.TextSelectableByKeyboard |
                            QtCore.Qt.TextSelectableByMouse)
                    control_label[0].setContextMenuPolicy(
                        Qt.Qt.CustomContextMenu)
                    control_label[0].customContextMenuRequested.connect(
                        partial(self._label_context_menu,
                                weakref.ref(control_label[0]), trait_name))

        # Otherwise, the control associated with the current trait name is
        # already inserted in the grid layout, just unpack the values
        # contained in the private '_controls' class parameter
        else:
            for group, control in six.iteritems(control_groups):
                _, _, control_instance, control_label = control
                control_instances.append(control_instance)
                if control_label:
                    if isinstance(control_label, tuple):
                        control_labels += list(control_label)
                    else:
                        control_labels.append(control_label)

        # Each trait has a hidden property. Take care of this information
        hide = (getattr(trait, 'hidden', False)
                or getattr(trait, 'unused', False)
                or (getattr(trait, 'userlevel', 0) is not None
                    and trait.userlevel > self.userlevel))

        # Show/Hide the control and associated labels
        for control_instance in control_instances:
            control_instance.setVisible(not hide)
        for label in control_labels:
            if not sip.isdeleted(label):  # sometimes happens...
                label.setVisible(not hide)

    def _create_group_widget(self, group):
        group_widget = QtGui.QGroupBox()
        last_row = self._grid_layout.rowCount()
        self._grid_layout.addWidget(group_widget, last_row, 0,
                                    1, 2)
        lay1 = QtGui.QVBoxLayout()
        lay1.setContentsMargins(0, 0, 0, 0)
        lay2 = QtGui.QHBoxLayout()
        lay1.addLayout(lay2)
        lay2.setContentsMargins(10, 0, 0, 0)
        lay2.addWidget(QtGui.QLabel('<html><em>%s</em></html>' % group))
        lay2.addStretch(1)
        icon = QtGui.QIcon()
        icon.addPixmap(
            QtGui.QPixmap(_fromUtf8(":/soma_widgets_icons/nav_down")),
            QtGui.QIcon.Normal, QtGui.QIcon.Off)
        group_widget.fold_button = QtGui.QPushButton(icon, '')
        group_widget.fold_button.setFixedSize(30, 20)
        lay2.addWidget(group_widget.fold_button)
        widget = QtGui.QWidget()
        group_widget.setLayout(lay1)
        lay1.addWidget(widget)
        group_widget.hideable_widget = widget
        layout = QtGui.QGridLayout()
        widget.setLayout(layout)
        layout.setAlignment(QtCore.Qt.AlignTop)
        layout.setSpacing(3)
        layout.setContentsMargins(5, 5, 5, 5)
        group_widget.setAlignment(QtCore.Qt.AlignLeft)

        visible_groups = getattr(self.controller, 'visible_groups', set())
        if group in visible_groups:
            show = True
        else:
            show = False
        group_widget.hideable_widget.setVisible(show)

        if not show:
            icon = QtGui.QIcon()
            icon.addPixmap(
                QtGui.QPixmap(_fromUtf8(":/soma_widgets_icons/nav_right")),
                QtGui.QIcon.Normal, QtGui.QIcon.Off)
            group_widget.fold_button.setIcon(icon)

        #group_widget.fold_button.clicked.connect(SomaPartial(
            #self._toggle_group_visibility, group))
        # FIXME: if we use this, self gets deleted somewhere. This is not
        # normal.
        group_widget.fold_button.clicked.connect(partial(
            self.__class__._toggle_group_visibility, weak_proxy(self), group))

        return group_widget

    def _set_group_visibility(self, group, checked):
        group_widget = self._groups[group]
        group_widget.hideable_widget.setVisible(checked)
        icon = QtGui.QIcon()
        if checked:
            icon.addPixmap(
                QtGui.QPixmap(_fromUtf8(":/soma_widgets_icons/nav_down")),
                QtGui.QIcon.Normal, QtGui.QIcon.Off)
        else:
            icon.addPixmap(
                QtGui.QPixmap(_fromUtf8(":/soma_widgets_icons/nav_right")),
                QtGui.QIcon.Normal, QtGui.QIcon.Off)
        group_widget.fold_button.setIcon(icon)

    def _toggle_group_visibility(self, group, checked=False):
        visible_groups = getattr(self.controller, 'visible_groups', set())
        if group in visible_groups:
            show = False
            visible_groups.remove(group)
        else:
            show = True
            visible_groups.add(group)
        self._set_group_visibility(group, show)
        self.controller.visible_groups = visible_groups

    def _create_control_in_layout(self, trait_name, trait, layout, group=None):
        # Call the search function that will map the trait type to the
        # corresponding control type
        control_class = self.get_control_class(trait)
        ## FIXME: for now we use a hack for compound/either traits, until
        ## we write a "real" GUI for them
        #if isinstance(trait.trait_type, (traits.TraitCompound, traits.Either)):
            ## compound trait: use the 1st
            #trait = trait.handler.handlers[0].as_ctrait()
        # Create the control instance and associated label
        if self.editable_labels:
            label_class = DeletableLineEdit
        else:
            label_class = QtGui.QLabel
        control_instance, control_label = control_class.create_widget(
            self, trait_name, getattr(self.controller, trait_name),
            trait, label_class, user_data=self.user_data)
        control_class.is_valid(control_instance)

        # If the trait contains a description, insert a tool tip to the
        # control instance
        type_name = type(trait.trait_type).__name__.split('.')[-1]
        #protected = ''
        #if self.controller.is_parameter_protected(trait_name):
            #protected = ' - modified'
        tooltip = "<b>%s</b> (%s)" % (trait_name, type_name)
        if trait.desc:
            tooltip += "<b>:</b> " + trait.desc
        if control_label:
            if isinstance(control_label, tuple):
                control_label[0].setToolTip(tooltip)
            else:
                control_label.setToolTip(tooltip)
        else:
            control_instance.setToolTip(tooltip)

        # Get the last empty row in the grid layout
        # Trick: If the grid layout is empty check the element 0
        # (not realistic but te grid layout return None)
        last_row = layout.rowCount()
        widget_item = layout.itemAtPosition(last_row, 1)
        while widget_item is None and last_row > 0:
            last_row -= 1
            widget_item = layout.itemAtPosition(last_row, 1)
        last_row += 1

        # If the control has no label, append the control in a two
        # columns span area of the grid layout
        if control_label is None:

            # Grid layout 'addWidget' parameters: QWidget, int row,
            # int column, int rowSpan, int columnSpan
            layout.addWidget(
                control_instance, last_row, 0, 1, 2)

        # If the control has two labels, add a first row with the
        # labels (one per column), and add the control in
        # the next row of the grid layout in the second column
        elif isinstance(control_label, tuple):

            # Get the number of label
            nb_of_labels = len(control_label)

            # If more than two labels are detected, print an error message.
            # We actually consider only the two first labels and skip the
            # others
            if nb_of_labels > 2:
                logger.error("To many labels associated with control "
                              "'{0}': {1}. Only consider the two first "
                              "labels and skip the others".format(
                                  trait_name, control_label))

            # Append each label in different columns
            if not self.hide_labels:
                layout.addWidget(
                    control_label[0], last_row, 0)
            if nb_of_labels >= 2:
                layout.addWidget(control_label[1], last_row, 1)

            # Append the control in the next row in the second column
            layout.addWidget(control_instance, last_row + 1, 1)

        # Otherwise, append the label and control in two separate
        # columns of the grid layout
        else:

            # Append the label in the first column
            if not self.hide_labels:
                layout.addWidget(control_label, last_row, 0)

            # Append the control in the second column
            layout.addWidget(
                control_instance, last_row, 1, 1, 1)

        # Store some informations about the inserted control in the
        # private '_controls' class parameter
        # Keys: the trait names
        # Parameters: the trait - the control name - the control - and
        # the labels associated with the control
        self._controls.setdefault(trait_name, {})[group] = (
            trait, control_class, control_instance, control_label)

        return control_instance, control_label

    def _key_modified(self, old_key):
        """ Dict / open controller key modification callback
        """
        control_groups = self._controls[old_key]
        control_labels = []
        for group_name, control in six.iteritems(control_groups):
            print('group_name:', group_name, ', control:', control)
            if isinstance(control[3], list):
                control_labels += control[3]
            else:
                control_labels.append(control[3])
        key = None
        for control_label in control_labels:
            if hasattr(control_label, 'text'):
                key = str(control_label.text())
                was_connected = self.connected
                if was_connected:
                    self.disconnect()
                self.disconnect_keys()

        if key is None:
            print('Modified dict key widget cannot be found', file=sys.stderr)
            return

        controller = self.controller
        print('add trait on:', controller)
        trait = controller.trait(old_key)
        controller.add_trait(key, trait)
        setattr(controller, key, getattr(controller, old_key))
        controller.remove_trait(old_key)
        self._controls[key] = self._controls[old_key]
        del self._controls[old_key]
        if was_connected:
            self.connect()
        # reconnect label widget
        self.connect_keys()
        # self.update_controls()  # not even needed
        if hasattr(self, 'main_controller_def'):
            main_control_class, controller_widget, control_name, frame = \
                self.main_controller_def
            main_control_class.update_controller(
                controller_widget, control_name, frame)
        # self.update_controller()

    def _delete_key(self, key):
        """ Dict / open controller key deletion callback
        """
        controller = self.controller
        trait = controller.trait(key)
        controller.remove_trait(key)
        self.update_controls()
        if hasattr(self, 'main_controller_def'):
            main_control_class, controller_widget, control_name, frame = \
                self.main_controller_def
            main_control_class.update_controller(
                controller_widget, control_name, frame)
        # self.update_controller()

    def groups_vibility_changed(self):
        visible_groups = self.controller.visible_groups or set()
        for group, group_widget in six.iteritems(self._groups):
            if group in visible_groups:
                show = True
            else:
                show = False
            self._set_group_visibility(group, show)

    def get_control_class(self, trait):
        """ Find the control associated with the input trait.

        The mapping is defined in the global class parameter
        '_defined_controls'.

        Parameters
        ----------
        trait: Trait (mandatory)
            a trait item

        Returns
        -------
        control_class: class
            the control class associated with the input trait.
            If no match has been found, return None
        """
        # Initilaize the output variable
        control_class = None

        todo = [trait]
        done = set()
        while todo:
            trait = todo.pop(0)
            done.add(trait)

            trait_id = None
            ids = trait_ids(trait)
            if len(ids) >= 2:
                trait_id = 'Compound'
            elif len(ids) == 1:
                trait_id = ids[0]

            if trait_id is not None:
                control_class = self._defined_controls.get(trait_id)
                # Recursive construction: consider only the top level
                while control_class is None:
                    split_id = trait_id.rsplit("_", 1)
                    if len(split_id) == 1:
                        break
                    trait_id = split_id[0]
                    # Try to get the control class
                    control_class = self._defined_controls.get(trait_id)

                if control_class is not None:
                    break

            # not found: look in superclasses
            bases = trait.trait_type.__class__.__bases__ \
                + trait.__class__.__bases__
            for base in bases:
                if issubclass(base, traits.TraitType):
                    trait = self._instantiate_trait(base)
                    todo.append(trait)

        if control_class is None:
            # fallback to a label displaying "this value cannot be seen/edited"
            control_class = self._defined_controls.get('unknown')

        if inspect.isfunction(control_class):
            # the function may instantiate a specialized type dynamically
            control_class = control_class(trait)

        return control_class

    def _instantiate_trait(self, trait_type):
        if issubclass(trait_type, traits.BaseRange):
            return trait_type(0)
        return trait_type()

    def _label_context_menu(self, widget, control_name, pos):
        menu = Qt.QMenu(control_name, None)
        protect = menu.addAction('%s modified' % control_name)
        protect.setCheckable(True)
        protected = self.controller.is_parameter_protected(control_name)
        protect.setChecked(protected)

        menu.exec_(widget().mapToGlobal(pos))
        if protect.isChecked() != protected:
            self.controller.protect_parameter(control_name,
                                              protect.isChecked())


from soma.qt_gui.controls import controls

# Fill the controller widget mapping between the string trait descriptions and
# the associated control classes
ControllerWidget._defined_controls.update(controls)
