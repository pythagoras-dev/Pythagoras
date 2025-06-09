from __future__ import annotations

import sys
import traceback
from typing import Callable, Any

import pandas as pd
from persidict import PersiDict

from src.pythagoras._010_basic_portals.basic_portal_class import \
    _describe_persistent_characteristic, _describe_runtime_characteristic
from src.pythagoras._010_basic_portals.portal_aware_class import find_portal_to_use
from src.pythagoras._030_data_portals import ValueAddr
from src.pythagoras._040_logging_code_portals.exception_processing_tracking import (
    _exception_needs_to_be_processed, _mark_exception_as_processed)
from src.pythagoras._040_logging_code_portals.uncaught_exceptions import \
    unregister_systemwide_uncaught_exception_handlers, \
    register_systemwide_uncaught_exception_handlers
from src.pythagoras._800_persidict_extensions import OverlappingMultiDict
from src.pythagoras._040_logging_code_portals.kw_args import KwArgs, PackedKwArgs
from src.pythagoras._810_output_manipulators import OutputCapturer
from src.pythagoras._010_basic_portals import PortalAwareClass
from src.pythagoras._030_data_portals.data_portal_core_classes import (
    DataPortal, StorableFn)
from src.pythagoras._820_strings_signatures_converters.current_date_gmt_str import (
    current_date_gmt_string)
from src.pythagoras._040_logging_code_portals.execution_environment_summary import (
    build_execution_environment_summary, add_execution_environment_summary)
from src.pythagoras._820_strings_signatures_converters.random_signatures import (
    get_random_signature)


class LoggingFn(StorableFn):

    _excessive_logging:bool|None

    def __init__(self
            , fn: Callable | str
            , excessive_logging: bool|None = None
            , portal: LoggingCodePortal | None = None
            ):
        if isinstance(fn,LoggingFn):
            assert excessive_logging is None
            super().__init__(fn=fn, portal=portal)
            assert hasattr(self,"_excessive_logging")
        else:
            super().__init__(fn=fn, portal=portal)
            self._excessive_logging = excessive_logging


    @property
    def excessive_logging(self) -> bool:
        with self.finally_bound_portal as portal:
            result = self._excessive_logging
            result = (result or portal.excessive_logging)
            return result


    def execute(self,**kwargs):
        with self.finally_bound_portal as portal:
            packed_kwargs = KwArgs(**kwargs).pack(portal)
            fn_call_signature = LoggingFnCallSignature(self, packed_kwargs)
            with LoggingFnExecutionFrame(fn_call_signature) as frame:
                result = super().execute(**kwargs)
                frame._register_execution_result(result)
                return result


    def __getstate__(self):
        state = super().__getstate__()
        # state["_excessive_logging"] = self._excessive_logging
        return state


    def __setstate__(self, state):
        self._invalidate_cache()
        self._excessive_logging = None
        # self._excessive_logging = state["_excessive_logging"]
        super().__setstate__(state)

    def register_in_portal(self):
        if self._portal is None:
            return

        super().register_in_portal()

        excessive_logging = self._excessive_logging
        address = ("excessive_logging", self.hash_signature)
        if excessive_logging is not None:
            self.portal.config_store[address] = excessive_logging
        else:
            if not address in self.portal.config_store:
                excessive_logging = False
            else:
                excessive_logging = self.portal.config_store[address]
        self._excessive_logging = excessive_logging


class LoggingFnCallSignature(PortalAwareClass):
    """A signature of a call to a (logging) function.

    This class is used to create a unique identifier for a call to
    a function, consisting of the function itself as well as all its arguments.

    This is a supporting class for the LoggingFnExecutionResultAddr class, and
    Pythagoras' users should not need to interact with it directly.
    """
    _fn: LoggingFn | None
    _fn_name: str
    _fn_addr: ValueAddr
    _packed_kwargs: PackedKwArgs | None
    _kwargs_addr: ValueAddr

    def __init__(self, fn:LoggingFn, arguments:dict):
        assert isinstance(fn, LoggingFn)
        isinstance(arguments, dict)
        arguments = KwArgs(**arguments)
        with fn.finally_bound_portal as portal:
            self._fn = fn
            self._fn_addr = fn.addr
            self._packed_kwargs = arguments.pack(portal)
            self._kwargs_addr = ValueAddr(self._packed_kwargs, portal=portal)
            # PortalAwareClass.__init__(self, portal=portal)


    @property
    def _portal(self):
        return self.fn.portal


    @_portal.setter
    def _portal(self,value):
        self.fn.portal = value


    def __getstate__(self):
        state = dict(
            _fn_name=self._fn_name
            , _fn_addr=self._fn_addr
            , _kwargs_addr=self._kwargs_addr)
        return state


    def __setstate__(self, state):
        self._fn_name = state["_fn_name"]
        self._fn_addr = state["_fn_addr"]
        self._kwargs_addr = state["_kwargs_addr"]
        self._packed_kwargs = self._kwargs_addr.get(expected_type=PackedKwArgs)
        self._fn = self.fn_addr.get(expected_type=LoggingFn)


    @property
    def fn(self) -> LoggingFn:
        if not hasattr(self, "_fn") or self._fn is None:
            self._fn = self.fn_addr.get(expected_type=LoggingFn)
        return self._fn


    @property
    def fn_name(self) -> str:
        if not hasattr(self, "_fn_name") or self._fn_name is None:
            self._fn_name = self.fn.name
        return self._fn_name


    @property
    def fn_addr(self) -> ValueAddr:
        return self._fn_addr


    @property
    def kwargs_addr(self) -> ValueAddr:
        return self._kwargs_addr


    @property
    def packed_kwargs(self) -> PackedKwArgs:
        if (not hasattr(self,"_packed_kwargs")
                or self._packed_kwargs is None):
            self._packed_kwargs = self._kwargs_addr.get(
                expected_type=PackedKwArgs)
        return self._packed_kwargs


    @property
    def excessive_logging(self) -> bool:
        return self.fn.excessive_logging


    def __hash_signature_prefix__(self) -> str:
        prefix = self.fn_name
        prefix += "_" + self.__class__.__name__
        prefix = prefix.lower()
        return prefix


    def execute(self) -> Any:
        return self.fn.execute(**self.packed_kwargs.unpack())


    @property
    def addr(self) -> ValueAddr:
        return ValueAddr(self, portal=self.finally_bound_portal)


    @property
    def execution_attempts(self) -> PersiDict:
        with self.finally_bound_portal as portal:
            attempts_path = self.addr + ["attempts"]
            attempts = portal.run_history.json.get_subdict(attempts_path)
            return attempts


    @property
    def last_execution_attempt(self) -> Any:
        with self.finally_bound_portal:
            attempts = self.execution_attempts
            timeline = attempts.newest_values()
            if not len(timeline):
                result = None
            else:
                result = timeline[0]
            return result


    @property
    def execution_results(self) -> PersiDict:
        with self.finally_bound_portal as portal:
            results_path = self.addr + ["results"]
            results = portal.run_history.pkl.get_subdict(results_path)
            return results


    @property
    def last_execution_result(self) -> Any:
        with self.finally_bound_portal:
            results = self.execution_results
            timeline = results.newest_values()
            if not len(timeline):
                result = None
            else:
                result = timeline[0]
            return result


    @property
    def execution_outputs(self) -> PersiDict:
        with self.finally_bound_portal as portal:
            outputs_path = self.addr + ["outputs"]
            outputs = portal.run_history.txt.get_subdict(outputs_path)
            return outputs

    @property
    def last_execution_output(self) -> Any:
        with self.finally_bound_portal:
            outputs = self.execution_outputs
            timeline = outputs.newest_values()
            if not len(timeline):
                result = None
            else:
                result = timeline[0]
            return result


    @property
    def crashes(self) -> PersiDict:
        with self.finally_bound_portal as portal:
            crashes_path = self.addr + ["crashes"]
            crashes = portal.run_history.json.get_subdict(crashes_path)
            return crashes


    @property
    def last_crash(self) -> Any:
        with self.finally_bound_portal as portal:
            crashes = self.crashes
            timeline = crashes.newest_values()
            if not len(timeline):
                result = None
            else:
                result = timeline[0]
            return result


    @property
    def events(self) -> PersiDict:
        with self.finally_bound_portal as portal:
            events_path = self.addr + ["events"]
            events = portal.run_history.json.get_subdict(events_path)
            return events


    @property
    def last_event(self) -> Any:
        with self.finally_bound_portal as portal:
            events = self.events
            timeline = events.newest_values()
            if not len(timeline):
                result = None
            else:
                result = timeline[0]
            return result

    @property
    def execution_records(self) -> list[LoggingFnExecutionRecord]:
        with self.finally_bound_portal:
            result = []
            for k in self.execution_attempts:
                run_id = k[-1][:-9]
                result.append(LoggingFnExecutionRecord(self, run_id))
            return result


class LoggingFnExecutionRecord(PortalAwareClass):
    """ A record of a full function execution session.

    It provides access to all information, logged during the
    execution session, which includes information about the execution context
    (environment), function arguments, its output (everything that was
    printed to stdout/stderr during the execution attempt), any crashes
    (exceptions) and events fired, and an actual result of the execution
    (created by a 'return' statement within the function code).
    """
    call_signature: LoggingFnCallSignature
    session_id: str
    def __init__(
            self
            , call_signature: LoggingFnCallSignature
            , session_id: str):
        self.call_signature = call_signature
        self.session_id = session_id


    def __getstate__(self):
        assert False

    def __setstate__(self, state):
        assert False

    @property
    def _portal(self):
        return self.call_signature.portal


    @_portal.setter
    def _portal(self,value):
        self.call_signature.portal = value


    @property
    def output(self) -> str|None:
        with self.finally_bound_portal:
            execution_outputs = self.call_signature.execution_outputs
            for k in execution_outputs:
                if self.session_id in k[-1]:
                    return execution_outputs[k]
            return None

    @property
    def attempt_context(self)-> dict|None:
        with self.finally_bound_portal:
            execution_attempts = self.call_signature.execution_attempts
            for k in execution_attempts:
                if self.session_id in k[-1]:
                    return execution_attempts[k]
            return None

    @property
    def crashes(self) -> list[dict]:
        result = []
        with self.finally_bound_portal:
            crashes = self.call_signature.crashes
            for k in crashes:
                if self.session_id in k[-1]:
                    result.append(crashes[k])
        return result

    @property
    def events(self) -> list[dict]:
        result = []
        with self.finally_bound_portal:
            events = self.call_signature.events
            for k in events:
                if self.session_id in k[-1]:
                    result.append(events[k])
        return result

    @property
    def result(self)->Any:
        with self.finally_bound_portal:
            execution_results = self.call_signature.execution_results
            for k in execution_results:
                if self.session_id in k[-1]:
                    return execution_results[k].get()
            assert False, "Result not found"

    @property
    def packed_kwargs(self)-> PackedKwArgs:
        with self.finally_bound_portal:
            return self.call_signature.packed_kwargs


class LoggingFnExecutionFrame(PortalAwareClass):
    session_id: str
    fn_call_addr: ValueAddr
    fn_call_signature: LoggingFnCallSignature
    output_capturer: OutputCapturer | None
    exception_counter: int
    event_counter: int
    context_used: bool

    def __init__(self, fn_call_signature: LoggingFnCallSignature):
        portal = fn_call_signature.finally_bound_portal
        self.session_id = "run_"+get_random_signature()
        self.fn_call_signature = fn_call_signature
        self.fn_call_addr = ValueAddr(fn_call_signature, portal=portal)
        # super().__init__(portal=portal)

        if self.excessive_logging:
            self.output_capturer = OutputCapturer()
        else:
            self.output_capturer = None

        self.exception_counter = 0
        self.event_counter = 0
        self.context_used = False


    @property
    def _portal(self) -> LoggingCodePortal:
        return self.fn.portal

    @_portal.setter
    def _portal(self,value):
        self.fn.portal = value


    def __setstate__(self, state):
        def __getstate__(self):
            raise NotImplementedError(
                "LoggingFnExecutionFrame objects can't be pickled/unpickled.")


    def __getstate__(self):
        raise NotImplementedError(
            "LoggingFnExecutionFrame objects can't be pickled/unpickled.")


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
        self.finally_bound_portal.__enter__()
        if isinstance(self.output_capturer, OutputCapturer):
            self.output_capturer.__enter__()
        LoggingCodePortal.call_stack.append(self)
        self._register_execution_attempt()
        return self


    def _register_execution_attempt(self):
        if not self.excessive_logging:
            return
        execution_attempts = self.fn_call_signature.execution_attempts
        attempt_id = self.session_id+"_attempt"
        execution_attempts[attempt_id] = build_execution_environment_summary()
        self.portal.run_history.py[self.fn_call_addr + ["source"]] = (
            self.fn.source_code)


    def _register_execution_result(self, result: Any):
        if not self.excessive_logging:
            return
        execution_results = self.fn_call_signature.execution_results
        result_id = self.session_id+"_result"
        execution_results[result_id] = ValueAddr(result, portal=self.portal)


    def __exit__(self, exc_type, exc_value, trace_back):
        log_exception()
        if isinstance(self.output_capturer, OutputCapturer):
            self.output_capturer.__exit__(exc_type, exc_value, traceback)
            output_id = self.session_id+"_output"
            execution_outputs = self.fn_call_signature.execution_outputs
            execution_outputs[output_id] = self.output_capturer.get_output()

        self.portal.__exit__(exc_type, exc_value, traceback)
        LoggingCodePortal.call_stack.pop()


class NeedsRandomization(str):
    """A string that needs to be randomized"""
    pass

class AlreadyRandomized(str):
    """A string that has already been randomized"""
    pass



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

    The class provides two dictionaries, `crash_history` and `event_log`,
    to store the exceptions history and event log respectively.

    Static methods `log_exception` and `log_event` are provided to log
    exceptions and events. These methods are designed to be
    called from anywhere in the application, and they will log the exception
    or event into all the active LoggingPortals. 'Active' LoggingPortals are
    those that have been registered with the current
    stack of nested 'with' statements.

    The class also supports logging uncaught exceptions globally.
    """

    exception_handlers_registered: bool = False

    call_stack: list[LoggingFnExecutionFrame] = []

    run_history: OverlappingMultiDict | None
    crash_history: PersiDict | None
    event_history: PersiDict | None

    _excessive_logging: bool | None

    def __init__(self, root_dict:PersiDict|str|None = None
            , p_consistency_checks: float|None = None
            , excessive_logging: bool|None = None
            ):
        super().__init__(root_dict=root_dict
            , p_consistency_checks=p_consistency_checks)
        del root_dict

        excessive_logging_addr = ("excessive_logging", "everything")
        if excessive_logging is not None:
            excessive_logging = bool(excessive_logging)
            self.config_store[excessive_logging_addr] = excessive_logging
        else:
            if not excessive_logging_addr in self.config_store:
                excessive_logging = False
            else:
                excessive_logging = self.config_store[excessive_logging_addr]
        self._excessive_logging = excessive_logging

        crash_history_prototype = self._root_dict.get_subdict("crash_history")
        crash_history_params = crash_history_prototype.get_params()
        crash_history_params.update(
            dict(file_type="json", immutable_items=True , digest_len=0))
        self.crash_history = type(self._root_dict)(**crash_history_params)

        event_history_prototype = self._root_dict.get_subdict("event_history")
        event_history_params = event_history_prototype.get_params()
        event_history_params.update(
            dict(file_type="json", immutable_items=True, digest_len=0))
        self.event_history = type(self._root_dict)(**event_history_params)

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
        self.run_history = run_history

        if not LoggingCodePortal.exception_handlers_registered:
            register_systemwide_uncaught_exception_handlers()
        LoggingCodePortal.exception_handlers_registered = True


    def __exit__(self, exc_type, exc_val, exc_tb):
        log_exception()
        super().__exit__(exc_type, exc_val, exc_tb)


    @property
    def excessive_logging(self) -> bool:
        return self._excessive_logging
        # excessive_logging_addr = ("excessive_logging", "everything")
        # return self.config_store[excessive_logging_addr]


    def describe(self) -> pd.DataFrame:
        """Get a DataFrame describing the portal's current state"""
        all_params = [super().describe()]
        all_params.append(_describe_persistent_characteristic(
            EXCEPTIONS_TOTAL_TXT, len(self.crash_history)))
        all_params.append(_describe_persistent_characteristic(
            EXCEPTIONS_TODAY_TXT
            , len(self.crash_history.get_subdict(current_date_gmt_string()))))
        all_params.append(_describe_runtime_characteristic(
            EXCESSIVE_LOGGING_TXT, self.excessive_logging))

        result = pd.concat(all_params)
        result.reset_index(drop=True, inplace=True)
        return result


    def _clear(self) -> None:
        """Clear the portal's state"""
        self.crash_history = None
        self.event_log = None
        self.run_history = None
        super()._clear()


    @classmethod
    def _clear_all(cls) -> None:
        """Remove all information about all the portals from the system."""
        if LoggingCodePortal.exception_handlers_registered:
            unregister_systemwide_uncaught_exception_handlers()
        LoggingCodePortal.exception_handlers_registered = False
        LoggingCodePortal.call_stack = []
        super()._clear_all()



def log_exception() -> None:
    exc_type, exc_value, trace_back = sys.exc_info()
    if not _exception_needs_to_be_processed(
            exc_type, exc_value, trace_back):
        return

    if len(LoggingCodePortal.call_stack):
        frame = LoggingCodePortal.call_stack[-1]
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

    portal = find_portal_to_use(expected_type=LoggingCodePortal)
    address = (current_date_gmt_string(),exception_id)
    portal.crash_history[address] = event_body


def log_event(*args, **kwargs):
    if len(LoggingCodePortal.call_stack):
        frame = LoggingCodePortal.call_stack[-1]
        event_id = frame.session_id + "_event_" + str(frame.event_counter)
        frame.event_counter += 1
    else:
        frame = None
        event_id =  get_random_signature() + "_event"

    event_body = add_execution_environment_summary(args=args, **kwargs)

    if frame is not None:
        frame.fn_call_signature.events[event_id] = event_body

    portal = find_portal_to_use(expected_type=LoggingCodePortal)
    address = (current_date_gmt_string(),event_id)
    portal.event_history[address] = event_body
    print(f"Event logged: {event_id} ", *args)