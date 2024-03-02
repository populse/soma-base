from functools import partial

try:
    from pydantic.v1 import ValidationError
except ImportError:
    from pydantic import ValidationError

from soma.controller import field_type, field_type_str
from soma.undefined import undefined

from ..collapsible import CollapsibleWidget
from . import (
    ControllerFieldInteraction,
    DefaultWidgetFactory,
    GroupWidget,
    ScrollableWidgetsGrid,
    WidgetFactory,
    WidgetsGrid,
)
