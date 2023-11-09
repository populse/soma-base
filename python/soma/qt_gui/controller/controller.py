# -*- coding: utf-8 -*-

from functools import partial

try:
    from pydantic.v1 import ValidationError
except ImportError:
    from pydantic import ValidationError

from . import (
    WidgetFactory,
    WidgetsGrid,
    DefaultWidgetFactory,
    GroupWidget,
    ControllerFieldInteraction,
    ScrollableWidgetsGrid,
)
from ..collapsible import CollapsibleWidget
from soma.undefined import undefined
from soma.controller import field_type, field_type_str
