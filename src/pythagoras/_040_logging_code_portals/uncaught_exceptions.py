from __future__ import annotations

import sys
import traceback

from .._010_basic_portals import get_active_portal
from .._040_logging_code_portals.exception_processing_tracking import (
    _exception_needs_to_be_processed, _mark_exception_as_processed)
from .._800_signatures_and_converters.current_date_gmt_str import (
    current_date_gmt_string)
from .._040_logging_code_portals.execution_environment_summary import (
    add_execution_environment_summary)
from .._040_logging_code_portals.notebook_checker import is_executed_in_notebook
from .._800_signatures_and_converters.random_signatures import (
    get_random_signature)


def pth_excepthook(exc_type, exc_value, trace_back) -> None:
    if _exception_needs_to_be_processed(exc_type, exc_value, trace_back):
        exception_id = "app_"+ get_random_signature() + "_crash"
        event_body = add_execution_environment_summary(
            exc_type=exc_type, exc_value=exc_value, trace_back=trace_back)
        _mark_exception_as_processed(exc_type, exc_value, trace_back)
        portal = get_active_portal()
        portal._crash_history[current_date_gmt_string()
            , exception_id] = event_body

    sys.__excepthook__(exc_type, exc_value, trace_back)


def pth_excepthandler(_, exc_type, exc_value
                    , trace_back, tb_offset=None) -> None:
    if _exception_needs_to_be_processed(exc_type, exc_value, trace_back):
        exception_id = "app_" + get_random_signature() + "_crash"
        event_body = add_execution_environment_summary(
            exc_type=exc_type, exc_value=exc_value, trace_back=trace_back)
        _mark_exception_as_processed(exc_type, exc_value, trace_back)
        portal = get_active_portal()
        portal._crash_history[current_date_gmt_string()
            , exception_id] = event_body
    traceback.print_exception(exc_type, exc_value, trace_back)


_previous_excepthook = None
_number_of_handlers_registrations = 0

def register_systemwide_uncaught_exception_handlers() -> None:
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
        except:
            _previous_excepthook = sys.excepthook
            sys.excepthook = pth_excepthook


def unregister_systemwide_uncaught_exception_handlers() -> None:
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
        except:
            pass