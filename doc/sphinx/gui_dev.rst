``Controller`` graphical interface development
==============================================

Creating a GUI for a controller field type is done by creating and registering a
dedicated class derived from :py:class:`WidgetFactory`. This class must define
two methods:

- :py:meth:`create_widgets` that creates one or two widget to interact with the
  controller field and add them to the layout with
  ``self.controller_widget.add_widget_row(widget1, widget2)``
- :py:meth:`delete_widgets` that calls
  ``self.controller_widget.remove_widget_row()`` to remove the widgets from the
  parent layout and then free any resource created for the widgets.

For interaction with parent widget and with controller the py:class:`WidgetFactory`
can use two objects ``self.controller_widget`` and ``self.parent_interaction`` that
are described below:

``self.controller_widget``
--------------------------

``self.controller_widget`` is an instance of one of the two entrypoints for
creating a GUI for a controller that are :py:class:`ControllerWidget` and
:py:class:`ControllerSubwidget`. They are both deriving from
:py:class:`BaseControllerWidget` that is responsible for the parsing of the
controller and the creation of the inner widgets. They differ in their main
layout and the way subwidgets are added to that layout:

- :py:class:`ControllerWidget` is supposed to be used as first widget in hierarchy
  and has a vertical slider if its content it too high.
- :py:class:`ControllerSubwidget` is used as subwidget and has no slider.

The main method these controller widget expose are:

- :py:meth:`add_widget_row` to add one or two widget(s) to the parent layout.
- :py:meth:`remove_widget_row` to remove widgets from the last row of the parent
  layout.

12345678901234567890123456789012345678901234567890123456789012345678901234567890

``self.parent_interaction``
---------------------------

This object must be used for any interaction with the controller or the controller
field value. It is responsible for modifying the value and taking whatever action
is necessary to propagate this modification through the controller hierarchy. This
is important for values embedded in a type that doesn't allow notification. For
instance, if we are in a widget that corresponds to a value in a list. Modifying
this value with `self.parent_interaction`` will warn the parent interaction object
that can, for instance, go on in warning grand-parent if the parent is a list or
raise a value change signal if the parent is a ``Controller``.

The methods available on ``self.parent_interaction`` for interacting with a
controller are:

- :py:meth:`get_value`: get the value of the item (either a field, a list item, etc.)
  from the controller.
- :py:meth:`set_value`: modify the value of the item in the controller.
- :py:meth:`set_inner_value`: modify the value of a subitem of the item in the
  controller. For instance modify a list item if item is a list.
- :py:meth:`get_label`: get the name to display in a GUI for this item.
- :py:meth:`on_change_add`: add a callback that will be called whenever the item
  value is changed in the container.
- :py:meth:`on_change_remove`: remove the callback registered by :py:meth:`on_change_add`.
- :py:meth:`set_protected`: set the protected metadata for this item.
- :py:meth:`is_optional`: get the optional metadata of this item.
- :py:meth:`inner_value_changed`: indicate that an inner item value had been changed
  to launch the necessary callbacks.
