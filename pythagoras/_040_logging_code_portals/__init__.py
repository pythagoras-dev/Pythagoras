"""Classes and functions to work with application-level logging.

The main class in this sub-package is LoggingCodePortal, which extends BasicPortal
to provide application-level logging capabilities for events and exceptions.
'Application-level' means that the events and exceptions are logged into
location(s) that is(are) the same across the entire application,
and does(do) not depend on the specific function from which
the even or exception is originated.

BasicPortal provides two attributes, `crash_history` and `event_log`,
which are persistent dictionaries (PersiDict-s) that store
the exceptions history and event log respectively.

Static methods `log_exception` and `log_event` are provided to log
exceptions and events. These methods are designed to be
called from anywhere in the application, and they will log the exception
or event into all the active LoggingPortals. 'Active' LoggingPortals are
those that have been registered with the current
stack of nested 'with' statements.

The class also supports logging uncaught exceptions globally.
"""

from .logging_portal_core_classes import *
from .kw_args import KwArgs, PackedKwArgs, UnpackedKwArgs
from .execution_environment_summary import *
from .logging_decorator import logging

