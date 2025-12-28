"""Application-level logging infrastructure for Pythagoras.

This sub-package provides comprehensive logging capabilities for function
executions, events, and exceptions. It extends DataPortal to enable both
function-level and application-level logging with persistent storage.

Key Components:

LoggingCodePortal:
    The main portal class that provides logging infrastructure. Maintains
    three persistent dictionaries:
    - _run_history: Function execution artifacts (attempts, results, outputs)
    - _crash_history: Exception logs organized by date
    - _event_history: Custom event logs organized by date

LoggingFn:
    A function wrapper (created via @logging decorator) that automatically
    records execution attempts, results, exceptions, and events. Extends
    StorableFn with logging capabilities.

LoggingFnCallSignature:
    Unique identifier combining a function and its arguments, used to organize
    execution artifacts in storage.

LoggingFnExecutionRecord:
    Read-only view of artifacts from a completed execution session.

Logging Functions:
    - log_exception(): Log the current exception to the active portal
    - log_event(): Log custom events with arbitrary keyword arguments

Usage:
    Application-level logging means events and exceptions are logged to
    persistent storage shared across the entire application, enabling
    cross-session debugging and analysis.
"""

from .logging_portal_core_classes import *
from .kw_args import KwArgs, PackedKwArgs, UnpackedKwArgs
from .execution_environment_summary import *
from .logging_decorator import logging

