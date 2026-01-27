"""System-wide exception handlers for Pythagoras logging integration.

This module registers custom exception handlers that capture uncaught exceptions
and log them to the active LoggingCodePortal. It handles both standard Python
environments (via sys.excepthook) and Jupyter/IPython notebooks (via IPython's
custom exception handler mechanism).

Design Rationale:
    Uncaught exceptions represent critical failures that should always be logged
    for post-mortem analysis. By hooking into the system's exception handling
    mechanisms, Pythagoras ensures these failures are captured even when they
    occur outside of explicitly logged functions.

Handler Registration:
    Handlers are reference-counted to support multiple portal instances.
    Registration is idempotent: multiple calls increment a counter, and
    handlers are only removed when the counter reaches zero during unregistration.
"""

from __future__ import annotations

import sys
import traceback

from .._210_basic_portals import get_current_portal
from .._320_logging_code_portals.exception_processing_tracking import (
    _exception_needs_to_be_processed, _mark_exception_as_processed)
from .._110_supporting_utilities.current_date_gmt_str import (
    current_date_gmt_string)
from .._320_logging_code_portals.execution_environment_summary import (
    add_execution_environment_summary)
from mixinforge import is_executed_in_notebook
from .._110_supporting_utilities.random_signature import (
    get_random_signature)


def pth_excepthook(exc_type, exc_value, trace_back) -> None:
    """Custom sys.excepthook that logs uncaught exceptions to Pythagoras.

    This handler is installed in standard Python environments (non-Jupyter).
    It captures uncaught exceptions, enriches them with execution environment
    context, logs them to the portal's crash history, then delegates to the
    original sys.__excepthook__ to preserve standard Python exception behavior.

    Args:
        exc_type: The exception class.
        exc_value: The exception instance.
        trace_back: Traceback object for the exception.

    Side Effects:
        - Records the exception in the active LoggingCodePortal's crash history
        - Marks the exception as processed to prevent duplicate logging
        - Calls the original sys.__excepthook__ for standard error display
    """
    if _exception_needs_to_be_processed(exc_type, exc_value, trace_back):
        exception_id = "app_"+ get_random_signature() + "_crash"
        event_body = add_execution_environment_summary(
            exc_type=exc_type, exc_value=exc_value, trace_back=trace_back)
        _mark_exception_as_processed(exc_type, exc_value, trace_back)
        portal = get_current_portal()
        portal._crash_history[current_date_gmt_string()
            , exception_id] = event_body

    sys.__excepthook__(exc_type, exc_value, trace_back)


def pth_excepthandler(_, exc_type, exc_value
                    , trace_back, tb_offset=None) -> None:
    """Custom IPython exception handler that logs uncaught exceptions to Pythagoras.

    This handler is installed in Jupyter/IPython environments. It captures
    uncaught exceptions, enriches them with execution context, logs them to
    the portal's crash history, then displays the traceback.

    The signature matches IPython's set_custom_exc() protocol, which requires
    a specific parameter signature that differs from sys.excepthook.

    Args:
        _: IPython shell instance (required by protocol but unused here).
        exc_type: The exception class.
        exc_value: The exception instance.
        trace_back: Traceback object for the exception.
        tb_offset: Optional traceback offset for IPython's display system. Unused.

    Side Effects:
        - Records the exception in the active LoggingCodePortal's crash history
        - Marks the exception as processed to prevent duplicate logging
        - Prints the exception traceback via traceback.print_exception()
    """
    if _exception_needs_to_be_processed(exc_type, exc_value, trace_back):
        exception_id = "app_" + get_random_signature() + "_crash"
        event_body = add_execution_environment_summary(
            exc_type=exc_type, exc_value=exc_value, trace_back=trace_back)
        _mark_exception_as_processed(exc_type, exc_value, trace_back)
        portal = get_current_portal()
        portal._crash_history[current_date_gmt_string()
            , exception_id] = event_body
    traceback.print_exception(exc_type, exc_value, trace_back)


_previous_excepthook = None
_number_of_handlers_registrations = 0

def register_systemwide_uncaught_exception_handlers() -> None:
    """Install Pythagoras exception handlers for the current environment.

    Detects the execution environment (standard Python vs Jupyter/IPython)
    and installs the appropriate handler:
    - Standard Python: replaces sys.excepthook with pth_excepthook
    - Jupyter/IPython: registers pth_excepthandler via set_custom_exc()

    Multiple registrations are reference-counted: the first call installs
    handlers, subsequent calls increment a counter. Handlers are only
    removed when unregister_systemwide_uncaught_exception_handlers() is
    called an equal number of times.

    Side Effects:
        - Increments the global registration counter
        - Installs exception handlers (first registration only)
        - Stores the previous sys.excepthook for later restoration
    """
    global _number_of_handlers_registrations, _previous_excepthook
    _number_of_handlers_registrations += 1
    if _number_of_handlers_registrations > 1:
        return

    if not is_executed_in_notebook():
        _previous_excepthook = sys.excepthook
        sys.excepthook = pth_excepthook
        pass
    else:
        try:
            from IPython import get_ipython
            get_ipython().set_custom_exc((BaseException,), pth_excepthandler)
        except Exception:
            _previous_excepthook = sys.excepthook
            sys.excepthook = pth_excepthook


def unregister_systemwide_uncaught_exception_handlers() -> None:
    """Remove Pythagoras exception handlers from the system.

    Decrements the registration reference counter. When the counter reaches
    zero (indicating all portals have been closed), restores the original
    exception handling behavior:
    - Standard Python: restores the previous sys.excepthook
    - Jupyter/IPython: clears the custom exception handler

    Side Effects:
        - Decrements the global registration counter
        - Restores original exception handlers (when counter reaches zero)
        - Clears the stored previous excepthook reference
    """
    global _number_of_handlers_registrations, _previous_excepthook
    _number_of_handlers_registrations -= 1
    if _number_of_handlers_registrations > 0:
        return

    if _previous_excepthook is not None:
        sys.excepthook = _previous_excepthook
        _previous_excepthook = None

    if is_executed_in_notebook():
        try:
            from IPython import get_ipython
            get_ipython().set_custom_exc((BaseException,), None)
        except Exception:
            pass