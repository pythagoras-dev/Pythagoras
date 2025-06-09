from __future__ import annotations

import sys
import traceback

from src.pythagoras._010_basic_portals.portal_aware_class import find_portal_to_use
from src.pythagoras._040_logging_code_portals.exception_processing_tracking import (
    _exception_needs_to_be_processed, _mark_exception_as_processed)
from src.pythagoras._820_strings_signatures_converters.current_date_gmt_str import (
    current_date_gmt_string)
from src.pythagoras._040_logging_code_portals.execution_environment_summary import (
    add_execution_environment_summary)
from src.pythagoras._040_logging_code_portals.notebook_checker import is_executed_in_notebook
from src.pythagoras._820_strings_signatures_converters.random_signatures import (
    get_random_signature)


def pth_excepthook(exc_type, exc_value, trace_back) -> None:
    if _exception_needs_to_be_processed(exc_type, exc_value, trace_back):
        exception_id = "app_"+ get_random_signature() + "_crash"
        event_body = add_execution_environment_summary(
            exc_type=exc_type, exc_value=exc_value, trace_back=trace_back)
        _mark_exception_as_processed(exc_type, exc_value, trace_back)
        portal = find_portal_to_use()
        portal.crash_history[current_date_gmt_string()
        , exception_id] = event_body

    sys.__excepthook__(exc_type, exc_value, trace_back)


def pth_excepthandler(_, exc_type, exc_value
                    , trace_back, tb_offset=None) -> None:
    if _exception_needs_to_be_processed(exc_type, exc_value, trace_back):
        exception_id = "app_" + get_random_signature() + "_crash"
        event_body = add_execution_environment_summary(
            exc_type=exc_type, exc_value=exc_value, trace_back=trace_back)
        _mark_exception_as_processed(exc_type, exc_value, trace_back)
        portal = find_portal_to_use()
        portal.crash_history[current_date_gmt_string()
        , exception_id] = event_body
    traceback.print_exception(exc_type, exc_value, trace_back)


_previous_excepthook = None


def register_systemwide_uncaught_exception_handlers() -> None:
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
    global _previous_excepthook
    if _previous_excepthook is not None:
        sys.excepthook = _previous_excepthook
        _previous_excepthook = None

    if is_executed_in_notebook():
        try:
            from IPython import get_ipython
            get_ipython().set_custom_exc((BaseException,), None)
        except:
            pass