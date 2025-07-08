from __future__ import annotations

import sys
import traceback
from typing import Callable, Any

import pandas as pd
from parameterizable import register_parameterizable_class
from persidict import PersiDict, KEEP_CURRENT, Joker

from .._010_basic_portals import NotPicklable, get_active_portal
from .._010_basic_portals.basic_portal_core_classes import (
    _describe_persistent_characteristic, _describe_runtime_characteristic)

from .._030_data_portals import ValueAddr
from .._040_logging_code_portals.exception_processing_tracking import (
    _exception_needs_to_be_processed, _mark_exception_as_processed)
from .._040_logging_code_portals.uncaught_exceptions import \
    unregister_systemwide_uncaught_exception_handlers, \
    register_systemwide_uncaught_exception_handlers
from persidict import OverlappingMultiDict
from .._040_logging_code_portals.kw_args import KwArgs, PackedKwArgs
from .output_capturer import OutputCapturer
from .._030_data_portals.data_portal_core_classes import (
    DataPortal, StorableFn)
from .._800_signatures_and_converters.current_date_gmt_str import (
    current_date_gmt_string)
from .._040_logging_code_portals.execution_environment_summary import (
    build_execution_environment_summary, add_execution_environment_summary)
from .._800_signatures_and_converters.random_signatures import (
    get_random_signature)


class LoggingFn(StorableFn):

    # _excessive_logging_at_init: bool | Joker

    def __init__(self
            , fn: Callable | str
            , excessive_logging: bool|Joker = KEEP_CURRENT
            , portal: LoggingCodePortal | None = None
            ):
        super().__init__(fn=fn, portal=portal)

        if not isinstance(excessive_logging, (bool, Joker)):
            raise TypeError(
                "excessive_logging must be a boolean or Joker, "
                f"got {type(excessive_logging)}")

        if excessive_logging is KEEP_CURRENT and isinstance(fn, LoggingFn):
            excessive_logging = fn._ephemeral_config_params_at_init["excessive_logging"]

        self._ephemeral_config_params_at_init[
            "excessive_logging"] = excessive_logging


    @property
    def excessive_logging(self) -> bool:
        value = self._get_config_setting("excessive_logging", self.portal)
        return bool(value)


    def execute(self,**kwargs):
        with self.portal:
            packed_kwargs = KwArgs(**kwargs).pack()
            fn_call_signature = LoggingFnCallSignature(self, packed_kwargs)
            with LoggingFnExecutionFrame(fn_call_signature) as frame:
                result = super().execute(**kwargs)
                frame._register_execution_result(result)
                return result


    @property
    def portal(self) -> LoggingCodePortal:
        return super().portal


class LoggingFnCallSignature:
    """A signature of a call to a (logging) function.

    This class is used to create a unique identifier for a call to
    a function, consisting of the function itself as well as all its arguments.

    This is a supporting class for the LoggingFnExecutionResultAddr class, and
    Pythagoras' users should not need to interact with it directly.
    """
    _fn_addr: ValueAddr
    _kwargs_addr: ValueAddr

    _fn_name_cache: str | None
    _fn_cache: LoggingFn | None
    _packed_kwargs_cache: PackedKwArgs | None
    _addr_cache: ValueAddr | None

    def __init__(self, fn:LoggingFn, arguments:dict):
        assert isinstance(fn, LoggingFn)
        isinstance(arguments, dict)
        arguments = KwArgs(**arguments)
        with fn.portal:
            self._fn_cache = fn
            self._fn_addr = fn.addr
            self._packed_kwargs_cache = arguments.pack()
            self._kwargs_addr = ValueAddr(self._packed_kwargs_cache)


    @property
    def portal(self):
        return self.fn.portal


    def __getstate__(self):
        """This method is called when the object is pickled."""
        state = dict(
            fn_addr=self._fn_addr
            , kwargs_addr=self._kwargs_addr)
        return state


    def __setstate__(self, state):
        """This method is called when the object is unpickled."""
        self._invalidate_cache()
        self._fn_addr = state["fn_addr"]
        self._kwargs_addr = state["kwargs_addr"]


    def _invalidate_cache(self):
        """Invalidate the function's attribute cache.

        If the function's attribute named ATTR is cached,
        its cached value will be stored in an attribute named _ATTR_cache
        This method should delete all such attributes.
        """
        if hasattr(self, "_fn_cache"):
            del self._fn_cache
        if hasattr(self, "_fn_name_cache"):
            del self._fn_name_cache
        if hasattr(self, "_packed_kwargs_cache"):
            del self._packed_kwargs_cache
        if hasattr(self, "_addr_cache"):
            del self._addr_cache


    @property
    def fn(self) -> LoggingFn:
        if not hasattr(self, "_fn_cache") or self._fn_cache is None:
            self._fn_cache = self.fn_addr.get(expected_type=LoggingFn)
        return self._fn_cache


    @property
    def fn_name(self) -> str:
        if not hasattr(self, "_fn_name_cache") or self._fn_name_cache is None:
            self._fn_name_cache = self.fn.name
        return self._fn_name_cache


    @property
    def fn_addr(self) -> ValueAddr:
        return self._fn_addr


    @property
    def kwargs_addr(self) -> ValueAddr:
        return self._kwargs_addr


    @property
    def packed_kwargs(self) -> PackedKwArgs:
        if (not hasattr(self,"_packed_kwargs_cache")
                or self._packed_kwargs_cache is None):
            with self.portal:
                self._packed_kwargs_cache = self._kwargs_addr.get(
                    expected_type=PackedKwArgs)
        return self._packed_kwargs_cache


    @property
    def excessive_logging(self) -> bool:
        return self.fn.excessive_logging


    def __hash_signature_descriptor__(self) -> str:
        descriptor = self.fn_name
        descriptor += "_" + self.__class__.__name__
        descriptor = descriptor.lower()
        return descriptor


    def execute(self) -> Any:
        return self.fn.execute(**self.packed_kwargs.unpack())


    @property
    def addr(self) -> ValueAddr:
        if hasattr(self, "_addr_cache") and self._addr_cache is not None:
            return self._addr_cache
        with self.portal:
            self._addr_cache = ValueAddr(self)
            return self._addr_cache


    @property
    def execution_attempts(self) -> PersiDict:
        with self.portal as portal:
            attempts_path = self.addr + ["attempts"]
            attempts = portal._run_history.json.get_subdict(attempts_path)
            return attempts


    @property
    def last_execution_attempt(self) -> Any:
        with self.portal:
            attempts = self.execution_attempts
            timeline = attempts.newest_values(1)
            if not len(timeline):
                result = None
            else:
                result = timeline[0]
            return result


    @property
    def execution_results(self) -> PersiDict:
        with self.portal as portal:
            results_path = self.addr + ["results"]
            results = portal._run_history.pkl.get_subdict(results_path)
            return results


    @property
    def last_execution_result(self) -> Any:
        with self.portal:
            results = self.execution_results
            timeline = results.newest_values(1)
            if not len(timeline):
                result = None
            else:
                result = timeline[0]
            return result


    @property
    def execution_outputs(self) -> PersiDict:
        with self.portal as portal:
            outputs_path = self.addr + ["outputs"]
            outputs = portal._run_history.txt.get_subdict(outputs_path)
            return outputs


    @property
    def last_execution_output(self) -> Any:
        with self.portal:
            outputs = self.execution_outputs
            timeline = outputs.newest_values(1)
            if not len(timeline):
                result = None
            else:
                result = timeline[0]
            return result


    @property
    def crashes(self) -> PersiDict:
        with self.portal as portal:
            crashes_path = self.addr + ["crashes"]
            crashes = portal._run_history.json.get_subdict(crashes_path)
            return crashes


    @property
    def last_crash(self) -> Any:
        with self.portal as portal:
            crashes = self.crashes
            timeline = crashes.newest_values(1)
            if not len(timeline):
                result = None
            else:
                result = timeline[0]
            return result


    @property
    def events(self) -> PersiDict:
        with self.portal as portal:
            events_path = self.addr + ["events"]
            events = portal._run_history.json.get_subdict(events_path)
            return events


    @property
    def last_event(self) -> Any:
        with self.portal:
            events = self.events
            timeline = events.newest_values(1)
            if not len(timeline):
                result = None
            else:
                result = timeline[0]
            return result


    @property
    def execution_records(self) -> list[LoggingFnExecutionRecord]:
        with self.portal:
            result = []
            for k in self.execution_attempts:
                run_id = k[-1][:-9]
                result.append(LoggingFnExecutionRecord(self, run_id))
            return result


class LoggingFnExecutionRecord(NotPicklable):
    """ A record of one full function execution session.

    It provides access to all information logged during the
    execution session, which includes information about the execution context
    (environment), function arguments, its output (everything that was
    printed to stdout/stderr during the execution attempt), any crashes
    (exceptions) and events fired, and an actual result of the execution
    created by a 'return' statement within the function code.
    """
    call_signature: LoggingFnCallSignature
    session_id: str
    def __init__(
            self
            , call_signature: LoggingFnCallSignature
            , session_id: str):
        self.call_signature = call_signature
        self.session_id = session_id


    @property
    def portal(self):
        return self.call_signature.portal


    @property
    def output(self) -> str|None:
        with self.portal:
            execution_outputs = self.call_signature.execution_outputs
            for k in execution_outputs:
                if self.session_id in k[-1]:
                    return execution_outputs[k]
            return None


    @property
    def attempt_context(self)-> dict|None:
        with self.portal:
            execution_attempts = self.call_signature.execution_attempts
            for k in execution_attempts:
                if self.session_id in k[-1]:
                    return execution_attempts[k]
            return None


    @property
    def crashes(self) -> list[dict]:
        result = []
        with self.portal:
            crashes = self.call_signature.crashes
            for k in crashes:
                if self.session_id in k[-1]:
                    result.append(crashes[k])
        return result


    @property
    def events(self) -> list[dict]:
        result = []
        with self.portal:
            events = self.call_signature.events
            for k in events:
                if self.session_id in k[-1]:
                    result.append(events[k])
        return result


    @property
    def result(self)->Any:
        with self.portal:
            execution_results = self.call_signature.execution_results
            for k in execution_results:
                if self.session_id in k[-1]:
                    return execution_results[k].get()
            raise ValueError(
                f"Result for session {self.session_id} not found in "
                f"{self.call_signature.fn_name} execution results.")


class LoggingFnExecutionFrame(NotPicklable):
    call_stack: list[LoggingFnExecutionFrame] = []

    session_id: str
    fn_call_addr: ValueAddr
    fn_call_signature: LoggingFnCallSignature
    output_capturer: OutputCapturer | None
    exception_counter: int
    event_counter: int
    context_used: bool

    def __init__(self, fn_call_signature: LoggingFnCallSignature):
        with fn_call_signature.portal:
            self.session_id = "run_"+get_random_signature()
            self.fn_call_signature = fn_call_signature
            self.fn_call_addr = fn_call_signature.addr

            if self.excessive_logging:
                self.output_capturer = OutputCapturer()
            else:
                self.output_capturer = None

            self.exception_counter = 0
            self.event_counter = 0
            self.context_used = False


    @property
    def portal(self) -> LoggingCodePortal:
        return self.fn.portal


    @property
    def fn(self) -> LoggingFn:
        return self.fn_call_signature.fn


    @property
    def fn_name(self) -> str:
        return self.fn_call_signature.fn_name


    @property
    def excessive_logging(self) -> bool:
        return self.fn.excessive_logging


    @property
    def fn_addr(self) -> ValueAddr:
        return self.fn_call_signature.fn_addr


    @property
    def packed_args(self) -> PackedKwArgs:
        return self.fn_call_signature.packed_kwargs


    @property
    def kwargs_addr(self) -> ValueAddr:
        return self.fn_call_signature.kwargs_addr


    def __enter__(self):
        assert not self.context_used, (
            "An instance of PureFnExecutionFrame can be used only once.")
        self.context_used = True
        assert self.exception_counter == 0, (
            "An instance of PureFnExecutionFrame can be used only once.")
        assert self.event_counter == 0, (
            "An instance of PureFnExecutionFrame can be used only once.")
        self.portal.__enter__()
        if isinstance(self.output_capturer, OutputCapturer):
            self.output_capturer.__enter__()
        LoggingFnExecutionFrame.call_stack.append(self)
        self._register_execution_attempt()
        return self


    def _register_execution_attempt(self):
        if not self.excessive_logging:
            return
        execution_attempts = self.fn_call_signature.execution_attempts
        attempt_id = self.session_id+"_attempt"
        execution_attempts[attempt_id] = build_execution_environment_summary()
        self.portal._run_history.py[self.fn_call_signature.addr + ["source"]] = (
            self.fn.source_code)


    def _register_execution_result(self, result: Any):
        if not self.excessive_logging:
            return
        execution_results = self.fn_call_signature.execution_results
        result_id = self.session_id+"_result"
        execution_results[result_id] = ValueAddr(result)


    def __exit__(self, exc_type, exc_value, trace_back):
        log_exception()
        if isinstance(self.output_capturer, OutputCapturer):
            self.output_capturer.__exit__(exc_type, exc_value, traceback)
            output_id = self.session_id+"_output"
            execution_outputs = self.fn_call_signature.execution_outputs
            execution_outputs[output_id] = self.output_capturer.get_output()

        self.portal.__exit__(exc_type, exc_value, traceback)
        LoggingFnExecutionFrame.call_stack.pop()


EXCEPTIONS_TOTAL_TXT = "Exceptions, total"
EXCEPTIONS_TODAY_TXT = "Exceptions, today"
EXCESSIVE_LOGGING_TXT = "Excessive logging"

class LoggingCodePortal(DataPortal):
    """A portal that supports function-level logging for events and exceptions.

    This class extends DataPortal to provide application-level and function-level logging
    capabilities for events and exceptions. 'Application-level' means that
    the events and exceptions are logged into location(s) that is(are) the same
    across the entire application, and does not depend on the specific function
    from which the event or exception is raised.

    The class provides two dictionaries, `_crash_history` and `event_log`,
    to store the exception history and event log respectively.

    Static methods `log_exception` and `log_event` are provided to log
    exceptions and events. These methods are designed to be
    called from anywhere in the application, and they will log the exception
    or event into all the active LoggingPortals. 'Active' LoggingPortals are
    those that have been registered with the current
    stack of nested 'with' statements.

    The class also supports logging uncaught exceptions globally.
    """

    _run_history: OverlappingMultiDict | None
    _crash_history: PersiDict | None
    _event_history: PersiDict | None

    _excessive_logging_at_init: bool | Joker

    def __init__(self, root_dict:PersiDict|str|None = None
            , p_consistency_checks: float|Joker = KEEP_CURRENT
            , excessive_logging: bool|Joker = KEEP_CURRENT
            ):
        super().__init__(root_dict=root_dict
            , p_consistency_checks=p_consistency_checks)
        del root_dict

        if not isinstance(excessive_logging,(Joker,bool)):
            raise TypeError(
                "excessive_logging must be a boolean or Joker, "
                f"got {type(excessive_logging)}")

        self._ephemeral_config_params_at_init["excessive_logging"
            ] = excessive_logging

        crash_history_prototype = self._root_dict.get_subdict("crash_history")
        crash_history_params = crash_history_prototype.get_params()
        crash_history_params.update(
            dict(file_type="json", immutable_items=True , digest_len=0))
        self._crash_history = type(self._root_dict)(**crash_history_params)

        event_history_prototype = self._root_dict.get_subdict("event_history")
        event_history_params = event_history_prototype.get_params()
        event_history_params.update(
            dict(file_type="json", immutable_items=True, digest_len=0))
        self._event_history = type(self._root_dict)(**event_history_params)

        run_history_prototype = self._root_dict.get_subdict("run_history")
        run_history_shared_params = run_history_prototype.get_params()
        dict_type = type(self._root_dict)
        run_history = OverlappingMultiDict(
            dict_type=dict_type
            , shared_subdicts_params=run_history_shared_params
            , json=dict(immutable_items=True)
            , py=dict(base_class_for_values=str, immutable_items=False) # Immutable items????
            , txt=dict(base_class_for_values=str, immutable_items=True)
            , pkl=dict(immutable_items=True)
        )
        self._run_history = run_history

        register_systemwide_uncaught_exception_handlers()


    def __exit__(self, exc_type, exc_val, exc_tb):
        log_exception()
        super().__exit__(exc_type, exc_val, exc_tb)


    @property
    def excessive_logging(self) -> bool:
        return bool(self._get_config_setting("excessive_logging"))


    def describe(self) -> pd.DataFrame:
        """Get a DataFrame describing the portal's current state"""
        all_params = [super().describe()]
        all_params.append(_describe_persistent_characteristic(
            EXCEPTIONS_TOTAL_TXT, len(self._crash_history)))
        all_params.append(_describe_persistent_characteristic(
            EXCEPTIONS_TODAY_TXT
            , len(self._crash_history.get_subdict(current_date_gmt_string()))))
        all_params.append(_describe_runtime_characteristic(
            EXCESSIVE_LOGGING_TXT, self.excessive_logging))

        result = pd.concat(all_params)
        result.reset_index(drop=True, inplace=True)
        return result


    def _clear(self) -> None:
        """Clear the portal's state"""
        self._crash_history = None
        self._event_log = None
        self._run_history = None
        unregister_systemwide_uncaught_exception_handlers()
        super()._clear()


register_parameterizable_class(LoggingCodePortal)


def log_exception() -> None:
    exc_type, exc_value, trace_back = sys.exc_info()
    if not _exception_needs_to_be_processed(
            exc_type, exc_value, trace_back):
        return

    if len(LoggingFnExecutionFrame.call_stack):
        frame = LoggingFnExecutionFrame.call_stack[-1]
        exception_id = frame.session_id + "_crash_"
        exception_id += str(frame.exception_counter)
        frame.exception_counter += 1
    else:
        frame = None
        exception_id = "portal_" + get_random_signature() + "_crash"

    event_body = add_execution_environment_summary(
        exc_type=exc_type, exc_value=exc_value, trace_back=trace_back)
    _mark_exception_as_processed(exc_type, exc_value, trace_back)

    if frame is not None and frame.excessive_logging:
        frame.fn_call_signature.crashes[exception_id] = event_body

    portal = get_active_portal()
    address = (current_date_gmt_string(),exception_id)
    portal._crash_history[address] = event_body


def log_event(*args, **kwargs):
    if len(LoggingFnExecutionFrame.call_stack):
        frame = LoggingFnExecutionFrame.call_stack[-1]
        event_id = frame.session_id + "_event_" + str(frame.event_counter)
        frame.event_counter += 1
    else:
        frame = None
        event_id =  get_random_signature() + "_event"

    event_body = add_execution_environment_summary(args=args, **kwargs)

    if frame is not None:
        frame.fn_call_signature.events[event_id] = event_body

    portal = get_active_portal()
    address = (current_date_gmt_string(),event_id)
    portal._event_history[address] = event_body
    print(f"Event logged: {event_id} ", *args)