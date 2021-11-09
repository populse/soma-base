# -*- coding: utf-8 -*-
from functools import partial

from soma.qt_gui.qt_backend import Qt
from soma.utils.functiontools import SomaPartial
from soma.utils.weak_proxy import weak_proxy
import sip


class CompoundControlWidget(object):

    """ Control to select a value from Union fields.
    """

    @staticmethod
    def is_valid(control_instance, *args, **kwargs):
        """ Method to check if the new control value is correct.

        Parameters
        ----------
        control_instance: QWidget (mandatory)
            the control widget we want to validate

        Returns
        -------
        out: bool
        """
        # nothing to do here since we delegate to another control widget.
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
        # nothing to do here since we delegate to another control widget.
        pass

    @staticmethod
    def create_widget(parent, controller, field,
                      label_class=None):
        """ Create the widget.

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
        widget = Qt.QWidget(parent)

        # we have a combobox for the field type, and one of the control types
        # implementations depending on it

        layout = Qt.QVBoxLayout()
        widget.setLayout(layout)
        widget.type_combo = Qt.QComboBox()
        hlayout = Qt.QHBoxLayout()
        #layout.addLayout(hlayout)
        lwidget = Qt.QWidget()
        lwidget.setLayout(hlayout)
        hlayout.addWidget(Qt.QLabel('Compound type:'))
        hlayout.addWidget(widget.type_combo)
        widget.header_widget = lwidget
        widget.user_data = user_data

        # get compound types
        main_type, types = parse_type_str(field_type_str(field))
        for t in types:
            widget.type_combo.addItem(t)
        widget.type_combo.setCurrentIndex(0)

        widget.compound_widget = None
        widget.field = field  # we need to access it later
        widget.compound_label = None

        type_id = CompoundControlWidget.type_id_for(trait.handler.handlers,
                                                    control_value)
        widget.current_type_id = type_id
        widget.type_combo.setCurrentIndex(type_id)

        CompoundControlWidget.create_compound_widget(widget)

        widget.type_combo.currentIndexChanged.connect(
            partial(CompoundControlWidget.change_type_index, widget))

        # Add a parameter to tell us if the widget is optional
        widget.optional = trait.optional

        # Create the label associated with the enum widget
        control_label = controller.metadata(field.name, 'label', field.name)
        if label_class is None:
            label_class = Qt.QLabel
        if control_label is not None:
            label = (label_class(control_label, parent), lwidget)
        else:
            label = lwidget

        return (widget, label)

 
    @staticmethod
    def create_compound_widget(widget):
        control_widget = widget.parent()
        while control_widget \
                and not hasattr(control_widget, 'get_control_class') \
                and not hasattr(control_widget, 'controller_widget'):
            control_widget = control_widget.parent()
        if hasattr(control_widget, 'controller_widget'):
            control_widget = control_widget.controller_widget

        if widget.compound_widget is not None:
            # disconnect it
            try:
                widget.compound_class.disconnect(
                    control_widget, widget.trait_name, widget.compound_widget)
            except Exception:
                pass  # probably something already deleted
            del widget.compound_class

            lay_item = widget.layout().takeAt(0)
            w = lay_item.widget()
            w.deleteLater()
            del w
            del lay_item

            if widget.compound_label:
                if isinstance(widget.compound_label, (tuple, list)):
                    for l in widget.compound_label:
                        l.deleteLater()
                else:
                    widget.compound_label.deleteLater()
        widget.compound_label = None

        field = widget.field
        thandler = trait.handler.handlers[widget.current_type_id]
        ttype = CompoundControlWidget.as_ctrait(thandler)
        # Create the control instance and associated label
        control_class = control_widget.get_control_class(ttype)

        control_instance, control_label = control_class.create_widget(
            control_widget, widget.trait_name,
            getattr(control_widget.controller, widget.trait_name),
            ttype, user_data=widget.user_data)
        if isinstance(control_label, (tuple, list)):
            if len(control_label) != 0:
                control_label[0].deleteLater() # del only label
                control_label = control_label[1:]
                layout = widget.header_widget.layout()
                for l in control_label:
                    layout.addWidget(l)
                if control_label:
                    widget.compound_label = control_label
        else:
            control_label.deleteLater()
        del control_label

        widget.compound_widget = control_instance
        widget.compound_class = control_class
        widget.layout().addWidget(control_instance)

        control_class.is_valid(control_instance)
        control_class.update_controller_widget(
            control_widget, widget.trait_name, control_instance)
        control_class.connect(control_widget, widget.trait_name,
                              control_instance)

    @staticmethod
    def change_type_index(widget, index):
        if index != widget.current_type_id:
            widget.current_type_id = index
            CompoundControlWidget.create_compound_widget(widget)

    @staticmethod
    def update_controller(controller_widget, control_name,
                          control_instance, *args, **kwargs):
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
        control_instance: StrControlWidget (mandatory)
            the instance of the controller widget control we want to
            synchronize with the controller
        """
        # nothing to do here since we delegate to another control widget.
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
        control_instance: CompoundControlWidget (mandatory)
            the instance of the controller widget control we want to
            synchronize with the controller
        """
        try:
            trait_types = control_instance.trait.handler.handlers
        except ReferenceError:
            # widget deleted in the meantime
            return

        if sip.isdeleted(control_instance.__init__.__self__):
            CompoundControlWidget.disconnect(controller_widget, control_name,
                                             control_instance)
            return

        if not hasattr(controller_widget.controller, control_name):
            return  # probably deleting this item
        # Get the controller trait value
        new_controller_value = getattr(
            controller_widget.controller, control_name, None)

        # if the value type has changed, select the appropriate type in
        # compound
        type_id = CompoundControlWidget.type_id_for(trait_types,
                                                    new_controller_value)
        if type_id != control_instance.current_type_id:
            control_instance.type_combo.setCurrentIndex(type_id)

    @staticmethod
    def type_id_for(handlers, value):
        i = 0
        for i, trait in enumerate(handlers):
            # create a custom object with same traits
            temp = traits.HasTraits()
            ctrait = CompoundControlWidget.as_ctrait(trait)
            tname = 'param'
            temp.add_trait(tname, ctrait)
            try:
                setattr(temp, tname, value)
                # OK we have found a working one
                return i
            except Exception as e:
                pass
        else:
            # should not happen
            print('problem in type_id_for:', handlers, value)
            return 0

    @classmethod
    def connect(cls, controller_widget, control_name, control_instance):
        """ Connect an 'Enum' controller trait and an 'EnumControlWidget'
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
        # Update one element of the controller widget.
        # Hook: function that will be called to update the specific widget
        # when a trait event is detected.
        controller_hook = SomaPartial(
            cls.update_controller_widget, weak_proxy(controller_widget),
            control_name, weak_proxy(control_instance))

        # When the 'control_name' controller trait value is modified, update
        # the corresponding control
        controller_widget.controller.on_trait_change(
            controller_hook, name=control_name, dispatch='ui')

        # Store the trait - control connection we just build
        control_instance._controller_connections = (controller_hook, )
 
    @staticmethod
    def disconnect(controller_widget, control_name, control_instance):
        """ Disconnect an 'Enum' controller trait and an 'EnumControlWidget'
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
        if not hasattr(control_instance, '_controller_connections'):
            return
        controller_hook = control_instance._controller_connections[0]

        # Remove the controller hook from the 'control_name' trait
        controller_widget.controller.on_trait_change(
            controller_hook, name=control_name, remove=True)

        # Delete the trait - control connection we just remove
        del control_instance._controller_connections
