"""Classes and functions to work with application-level logging.

The main class in this sub-package is LoggingCodePortal, which extends DataPortal
to provide application-level logging capabilities for events and exceptions.
'Application-level' means that the events and exceptions are logged into
location(s) that is(are) the same across the entire application.

LoggingCodePortal provides three attributes, _run_history, _crash_history,
and  _event_history`, which are persistent dictionaries (PersiDict-s) that store
the exceptions and logged / recorded events.

Functions log_exception() and `log_event() are provided to log
exceptions and events. These methods are designed to be
called from anywhere in the application, and they will log the exception
or event into the best suitable LoggingPortal.
"""

from .logging_portal_core_classes import *
from .kw_args import KwArgs, PackedKwArgs, UnpackedKwArgs
from .execution_environment_summary import *
from .logging_decorator import logging

