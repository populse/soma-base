#
# SOMA - Copyright (C) CEA, 2015
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
#

# System import
import logging
import six

# Define the logger
logger = logging.getLogger(__name__)

# Trait import
from traits.api import HasTraits, Event, CTrait, Instance, Undefined, \
    TraitType, TraitError, Any, Set

# Soma import
from soma.sorted_dictionary import SortedDictionary, OrderedDict
from soma.controller.trait_utils import _type_to_trait_id


class ControllerMeta(HasTraits.__class__):

    """ This metaclass allows for automatic registration of factories.
    """
    def __new__(mcs, name, bases, dictionary):
        """ Method that can be used to define factories.

        Parameters
        ----------
        mcls: meta class (mandatory)
            a meta class.
        name: str (mandatory)
            the controller class name.
        bases: tuple (mandatory)
            the direct base classes.
        attrs: dict (mandatory)
            a dictionnary with the class attributes.
        """
        return super(ControllerMeta, mcs).__new__(mcs, name, bases, dictionary)


class Controller(six.with_metaclass(ControllerMeta, HasTraits)):

    """ A Controller contains some traits: attributes typing and observer
    (callback) pattern.

    The class provides some methods to add/remove/inspect user defined traits.

    Attributes
    ----------
    `user_traits_changed` : Event
        single event that can be sent when several traits changes. This event
        has to be triggered explicitely to take into account changes due to
        call(s) to add_trait or remove_trait.

    Methods
    -------
    user_traits
    is_user_trait
    add_trait
    remove_trait
    _clone_trait
    """

    # This event is necessary because there is no event when a trait is
    # removed with remove_trait and because it is sometimes better to send
    # a single event when several traits changes are done (especially
    # when GUI is updated on real time). This event have to be triggered
    # explicitely to take into account changes due to call(s) to
    # add_trait or remove_trait.
    user_traits_changed = Event

    def __init__(self, *args, **kwargs):
        """ Initilaize the Controller class.

        During the class initialization create a class attribute
        '_user_traits' that contains all the class traits and instance traits
        defined by user (i.e.  the traits that are not automatically
        defined by HasTraits or Controller). We can access this class
        parameter with the 'user_traits' method.

        If user trait parameters are defined directly on derived class, this
        procedure call the 'add_trait' method in order to not share
        user traits between instances.
        """
        # Inheritance
        super(Controller, self).__init__(*args, **kwargs)

        # Create a sorted dictionnary with user parameters
        # The dictionary order correspond to the definition order
        self._user_traits = SortedDictionary()

        # Get all the class traits
        class_traits = self.class_traits()

        # If some traits are defined on the controller, create a list
        # with definition ordered trait name. These names will correspond
        # to user trait sorted dictionary keys
        if class_traits:
            sorted_names = sorted(
                (getattr(trait, "order", ""), name)
                for name, trait in six.iteritems(class_traits)
                if self.is_user_trait(trait))
            sorted_names = [sorted_name[1] for sorted_name in sorted_names]

            # Go through all trait names that have been ordered
            for name in sorted_names:

                # If the trait is defined on the class, need to clone
                # the class trait and add the cloned trait to the instance.
                # This step avoids us to share trait objects between
                # instances.
                if name in self.__base_traits__:
                    logger.debug("Add class parameter '{0}'.".format(name))
                    trait = class_traits[name]
                    self.add_trait(name, self._clone_trait(trait))

                # If the trait is defined on the instance, just
                # add the user parameter to the '_user_traits' instance
                # parameter
                else:
                    logger.debug("Add instance parameter '{0}'.".format(name))
                    self._user_traits[name] = class_traits[name]

    #
    # Private methods
    #

    def _clone_trait(self, clone, metadata=None):
        """ Creates a clone of a specific trait (ie. the same trait
        type but different ids).

        Parameters
        ----------
        clone: CTrait (mandatory)
            the input trait to clone.
        metadata: dict (opional, default None)
            some metadata than can be added to the trait __dict__.

        Returns
        -------
        trait: CTrait
            the cloned input trait.
        """
        # Create an empty trait
        trait = CTrait(0)

        # Clone the input trait in the empty trait structure
        trait.clone(clone)

        # Set the input trait __dict__ elements to the cloned trait
        # __dict__
        if clone.__dict__ is not None:
            trait.__dict__ = clone.__dict__.copy()

        # Update the cloned trait __dict__ if necessary
        if metadata is not None:
            trait.__dict__.update(metadata)

        return trait

    def _propagate_optional_parameter(self, trait, optional=None):
        """
        """
        # Get the trait class name
        handler = trait.handler or trait
        main_id = handler.__class__.__name__
        if main_id == "TraitCoerceType":
            real_id = _type_to_trait_id.get(handler.aType)
            if real_id:
                main_id = real_id

        # Debug message
        logger.debug("Propagation optional parameter of trait with main id %s",
                     main_id)

        # Get the optional parameter and set the default value if necessary
        if optional is not None:
            trait.optional = optional
        else:
            optional = trait.optional
            if optional is None:
                optional = False
                trait.optional = optional

        # Either case
        if main_id in ["Either", "TraitCompound"]:

            # Debug message
            logger.debug("A coumpound trait has been found %s", repr(
                handler.handlers))

            # Update each trait compound optional parameter
            for sub_trait in handler.handlers:
                self._propagate_optional_parameter(sub_trait(), optional)

        # Default case
        else:
            # FIXME may recurse indefinitely if the trait is recursive
            for inner_trait in handler.inner_traits():
                self._propagate_optional_parameter(inner_trait, optional)

    #
    # Public methods
    #

    def user_traits(self):
        """ Method to access the user parameters.

        Returns
        -------
        out: dict
            a dictionnary containing class traits and instance traits
            defined by user (i.e.  the traits that are not automatically
            defined by HasTraits or Controller). Returned values are
            sorted according to the 'order' trait meta-attribute.
        """
        return self._user_traits

    def is_user_trait(self, trait):
        """ Method that evaluate if a trait is a user parameter
        (i.e. not an Event).

        Returns
        -------
        out: bool
            True if the trait is a user trait,
            False otherwise.
        """
        return not isinstance(trait.handler, Event)

    def add_trait(self, name, *trait):
        """ Add a new trait.

        Parameters
        ----------
        name: str (mandatory)
            the trait name.
        trait: traits.api (mandatory)
            a valid trait.
        """
        # Debug message
        logger.debug("Adding trait '{0}'...".format(name))

        # Inheritance: create the instance trait attribute
        super(Controller, self).add_trait(name, *trait)

        # Get the trait instance and if it is a user trait load the traits
        # to get it direcly from the instance (as a property) and add it
        # to the class '_user_traits' attributes
        trait_instance = self.trait(name)
        if self.is_user_trait(trait_instance):
            trait_instance.defaultvalue = trait_instance.default
            self.get(name)
            self._user_traits[name] = trait_instance

        # Update/set the optional trait parameter
        self._propagate_optional_parameter(trait_instance)

    def remove_trait(self, name):
        """ Remove a trait from its name.

        Parameters
        ----------
        name: str (mandatory)
            the trait name to remove.
        """
        # Debug message
        logger.debug("Removing trait '{0}'...".format(name))

        # Call the Traits remove_trait method
        super(Controller, self).remove_trait(name)

        # Remove name from the '_user_traits' without error if it
        # is not present
        self._user_traits.pop(name, None)

    def export_to_dict(self, exclude_undefined=False,
                       exclude_transient=False,
                       exclude_none=False,
                       exclude_empty=False,
                       dict_class=OrderedDict):
        """ return the controller state to a dictionary, replacing controller
        values in sub-trees to dicts also.

        Parameters
        ----------
        exclude_undefined: bool (optional)
            if set, do not export Undefined values
        exclude_transient: bool (optional)
            if set, do not export values whose trait is marked "transcient"
        exclude_none: bool (optional)
            if set, do not export None values
        exclude_empty: bool (optional)
            if set, do not export empty lists/dicts values
        dict_class: class type (optional, default: soma.sorted_dictionary.OrderedDict)
            use this type of mapping type to represent controllers. It should
            follow the mapping protocol API.
        """
        state_dict = dict_class()
        for trait_name, trait in six.iteritems(self.user_traits()):
            if exclude_transient and trait.transient:
                continue
            value = getattr(self, trait_name)
            if isinstance(value, Controller):
                value = value.export_to_dict()
            elif (exclude_undefined and value is Undefined) \
                    or (exclude_none and value is None):
                continue
            if exclude_empty and (value == [] or value == {}):
                continue
            state_dict[trait_name] = value
        return state_dict

    def import_from_dict(self, state_dict, clear=False):
        """ Set Controller variables from a dictionary. When setting values on
        Controller instances (in the Controller sub-tree), replace dictionaries
        by Controller instances appropriately.

        Parameters
        ----------
        state_dict: dict, sorted_dictionary or OrderedDict
            dict containing the variables to set
        clear: bool (optional, default: False)
            if True, older values (in keys not listed in state_dict) will be
            cleared, otherwise they are left in place.
        """
        if clear:
            for trait_name in self.user_traits():
                if trait_name not in state_dict:
                    delattr(self, trait_name)
        for trait_name, value in six.iteritems(state_dict):
            trait = self.trait(trait_name)
            if trait is None and not isinstance(self, OpenKeyController):
                raise KeyError(
                    "item %s is not a trait in the Controller" % trait_name)
            if isinstance(trait.trait_type, Instance) \
                    and issubclass(trait.trait_type.klass, Controller):
                controller = trait.trait_type.create_default_value(
                    trait.trait_type.klass)
                controller.import_from_dict(value)
            else:
                # check trait type for conversions
                tr = self.trait(trait_name)
                if tr and isinstance(tr.trait_type, Set):
                    setattr(self, trait_name, set(value))
                else:
                    setattr(self, trait_name, value)

    def copy(self, with_values=True):
        """ Copy traits definitions to a new Controller object

        Parameters
        ----------
        with_values: bool (optional, default: False)
            if True, traits values will be copied, otherwise the defaut trait
            value will be left in the copy.

        Returns
        -------
        copied: Controller instance
            the returned copy will have the same class as the copied object
            (which may be a derived class from Controller). Traits definitions
            will be copied. Traits values will only be copied if with_values is
            True.
        """
        copied = self.__class__()
        for name, trait in six.iteritems(self.user_traits()):
            copied.add_trait(name, trait)
            if with_values:
                setattr(copied, name, getattr(self, name))
        return copied

    def reorder_traits(self, traits_list):
        """ Reorder traits in the controller according to a new ordered list.

        If the new list does not contain all user traits, the remaining ones
        will be appended at the end.

        Parameters
        ----------
        traits_list: list
            New list of trait names. This list order will be kept.
        """
        former_traits = set(self._user_traits.sortedKeys)
        for t in traits_list:
            if t not in former_traits:
                raise ValueError("parameter %s is not is Controller traits."
                                 % t)
        new_traits = list(traits_list)
        done = set(new_traits)
        for t in self._user_traits.sortedKeys:
            if t not in done:
                new_traits.append(t)
        self._user_traits.sortedKeys = new_traits


class OpenKeyController(Controller):

    """ A dictionary-like controller, with "open keys": items may be added
    on the fly, traits are created upon assignation.

    A value trait type should be specified to build the items.

    Usage:

    >>> dict_controller = OpenKeyController(value_trait=traits.Str())
    >>> print dict_controller.user_traits().keys()
    []
    >>> dict_controller.my_item = 'bubulle'
    >>> print dict_controller.user_traits().keys()
    ['my_item']
    >>> print dict_controller.export_to_dict()
    {'my_item': 'bubulle'}
    >>> del dict_controller.my_item
    >>> print dict_controller.export_to_dict()
    {}
    """
    _reserved_names = set(['trait_added'])

    def __init__(self, value_trait=Any(), *args, **kwargs):
        """ Build an OpenKeyController controller.

        Parameters
        ----------
        value_trait: Trait instance (optional, default: Any())
            trait type to be used when creating traits on the fly
        """
        super(OpenKeyController, self).__init__(*args, **kwargs)
        super(OpenKeyController, self).__setattr__('_value_trait', value_trait)

    def __setattr__(self, name, value):
        if not name.startswith('_') and name not in self.__dict__ \
                and name not in self.traits() \
                and not name in OpenKeyController._reserved_names:
            self.add_trait(name, self._value_trait)
        super(OpenKeyController, self).__setattr__(name, value)

    def __delattr__(self, name):
        if self.trait(name):
            self.remove_trait(name)
        else:
            super(OpenKeyController, self).__delattr__(name)


class ControllerTrait(TraitType):

    """ A specialized trait type for Controller values.
    """

    def __init__(self, controller, inner_trait=None, **kwargs):
        """ Build a Controller valued trait.

        Contrarily to Instance(Controller), it ensures better validation when
        assigning values.

        It has the ability to convert values from dictionaries, so the trait
        value can be assigned with a dict, whereas it is actually a Controller.
        This works recursively if the controller contains traits which are also
        controllers.

        Parameters
        ----------
        controller: Controller instance (mandatory)
            default value for trait, and placeholder for allowed traits
        inner_trait: Trait instance (optional)
            if provided, the controller is assumed to be an "open key" type,
            new keys/traits can be added on the fly like in a dictionary, and
            this inner_trait is the trait type used to instantiate new
            traits when new keys are encountered while setting values.
            If inner_trait is not provided, we will look if the controller
            instance is an OpenKeyController, and in such case, take its value
            trait.
        """
        super(ControllerTrait, self).__init__(None, **kwargs)
        self.controller = controller
        self.default_value = controller
        if inner_trait is None and hasattr(controller, '_value_trait'):
            inner_trait = controller._value_trait
        self.inner_trait = inner_trait
        self.handler = self

    def validate(self, object, name, value):
        if isinstance(value, Controller):
            sup_inst = super(ControllerTrait, self)
            if hasattr(sup_inst, 'validate'):
                return sup_inst.validate(value)
            else:
                return value
        if not hasattr(value, 'items'):
            raise TraitError('trait must be a Controller or a mapping type')
        new_value = getattr(object, name).copy(with_values=False)
        if self.inner_trait:
            for key in new_value.user_traits():
                if key not in value:
                    new_value.remove_trait(key)
            for key in value:
                if not self.controller.trait(key):
                    new_value.add_trait(key, self.inner_trait)
        new_value.import_from_dict(value)
        return new_value

    def inner_traits(self):
        if self.inner_trait:
            return (self.inner_trait, )
        return ()
