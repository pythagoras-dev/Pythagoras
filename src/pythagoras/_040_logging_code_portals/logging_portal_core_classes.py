from __future__ import annotations

import sys
import traceback
from typing import Callable, Any

import pandas as pd
from parameterizable import NotPicklableClass
from persidict import PersiDict, KEEP_CURRENT, Joker

from .._010_basic_portals import get_active_portal
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
    """A function wrapper that logs executions, outputs, events, and crashes.

    LoggingFn wraps a callable and, when executed within a LoggingCodePortal,
    records execution attempts, results, captured stdout/stderr, raised
    exceptions, and custom events. It also supports an excessive_logging mode
    that enables storing rich per-call artifacts.

    A logging function can only be called with keyword arguments.
    It can't be called with positional arguments.

    Attributes:
        _auxiliary_config_params_at_init (dict): Internal configuration store
            inherited from StorableFn. Includes the 'excessive_logging' flag
            when provided.
    """

    # _excessive_logging_at_init: bool | Joker

    def __init__(self
            , fn: Callable | str
            , excessive_logging: bool|Joker = KEEP_CURRENT
            , portal: LoggingCodePortal | None = None
            ):
        """Initialize a LoggingFn wrapper.

        Args:
            fn: A callable to wrap or a string with a function's source code.
            excessive_logging: If True, capture detailed per-execution
                artifacts (attempt context, outputs, results). If KEEP_CURRENT,
                will inherit the setting from another LoggingFn when cloning.
            portal: Optional LoggingCodePortal to bind this function to. If
                omitted, uses the active portal during execution.

        Raises:
            TypeError: If excessive_logging is not a bool or Joker.
        """
        super().__init__(fn=fn, portal=portal)

        if not isinstance(excessive_logging, (bool, Joker)):
            raise TypeError(
                "excessive_logging must be a boolean or Joker, "
                f"got {type(excessive_logging)}")

        if excessive_logging is KEEP_CURRENT and isinstance(fn, LoggingFn):
            excessive_logging = fn._auxiliary_config_params_at_init["excessive_logging"]

        self._auxiliary_config_params_at_init[
            "excessive_logging"] = excessive_logging


    @property
    def excessive_logging(self) -> bool:
        """Whether rich per-execution logging is enabled for this function.

        Returns:
            bool: True if excessive logging is enabled for this function (from
            its own config or inherited via the portal); False otherwise.
        """
        value = self._get_config_setting("excessive_logging", self.portal)
        return bool(value)


    def get_signature(self, arguments:dict) -> LoggingFnCallSignature:
        """Create a call signature for this function and the given arguments.

        Args:
            arguments: A mapping of keyword arguments for the call. Values may
                be raw or ValueAddr; they will be normalized and packed.

        Returns:
            LoggingFnCallSignature: A signature object uniquely identifying
            the combination of function and arguments.
        """
        return LoggingFnCallSignature(self, arguments)


    def execute(self,**kwargs):
        """Execute the wrapped function and log artifacts via the portal.

        Args:
            **kwargs: Keyword arguments to pass to the wrapped function.

        Returns:
            Any: The result returned by the wrapped function.

        Side Effects:
            - Registers an execution attempt and, if enabled, captures
              stdout/stderr and stores the result and output.
        """
        with self.portal:
            packed_kwargs = KwArgs(**kwargs).pack()
            fn_call_signature = self.get_signature(packed_kwargs)
            with LoggingFnExecutionFrame(fn_call_signature) as frame:
                result = super().execute(**kwargs)
                frame._register_execution_result(result)
                return result


    @property
    def portal(self) -> LoggingCodePortal:
        """The LoggingCodePortal associated with this function.

        Returns:
            LoggingCodePortal: The portal used for storage and logging during
            execution.
        """
        return super().portal


class   LoggingFnCallSignature:
    """A signature of a call to a logging function.

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
        if not isinstance(fn, LoggingFn):
            raise TypeError(f"fn must be an instance of LoggingFn, got {type(fn).__name__}")
        isinstance(arguments, dict)
        arguments = KwArgs(**arguments)
        with fn.portal:
            self._fn_cache = fn
            self._fn_addr = fn.addr
            self._packed_kwargs_cache = arguments.pack()
            self._kwargs_addr = ValueAddr(self._packed_kwargs_cache)


    @property
    def portal(self):
        """Portal associated with the underlying function.

        Returns:
            LoggingCodePortal: The portal used to store and retrieve logging
            artifacts for this call signature.
        """
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
        """Resolve and cache the wrapped LoggingFn instance.

        Returns:
            LoggingFn: The function associated with this call signature.
        """
        if not hasattr(self, "_fn_cache") or self._fn_cache is None:
            self._fn_cache = self.fn_addr.get(expected_type=LoggingFn)
        return self._fn_cache


    @property
    def fn_name(self) -> str:
        """Name of the wrapped function.

        Returns:
            str: The function's name, cached after first access.
        """
        if not hasattr(self, "_fn_name_cache") or self._fn_name_cache is None:
            self._fn_name_cache = self.fn.name
        return self._fn_name_cache


    @property
    def fn_addr(self) -> ValueAddr:
        """Address of the wrapped LoggingFn in the portal storage.

        Returns:
            ValueAddr: The persisted address pointing to the LoggingFn.
        """
        return self._fn_addr


    @property
    def kwargs_addr(self) -> ValueAddr:
        """Address of the packed keyword arguments in portal storage.

        Returns:
            ValueAddr: The persisted address pointing to the packed kwargs.
        """
        return self._kwargs_addr


    @property
    def packed_kwargs(self) -> PackedKwArgs:
        """Packed keyword arguments for this call signature.

        Returns:
            PackedKwArgs: The packed kwargs, fetched from storage if not cached.
        """
        if (not hasattr(self,"_packed_kwargs_cache")
                or self._packed_kwargs_cache is None):
            with self.portal:
                self._packed_kwargs_cache = self._kwargs_addr.get(
                    expected_type=PackedKwArgs)
        return self._packed_kwargs_cache


    @property
    def excessive_logging(self) -> bool:
        """Whether excessive logging is enabled for the underlying function.

        Returns:
            bool: True if excessive logging is enabled, False otherwise.
        """
        return self.fn.excessive_logging


    def __hash_signature_descriptor__(self) -> str:
        """Descriptor string contributing to the address hash.

        Returns:
            str: A lowercase string combining the function name and this class
            name, used as part of the address hashing scheme.
        """
        descriptor = self.fn_name
        descriptor += "_" + self.__class__.__name__
        descriptor = descriptor.lower()
        return descriptor


    def execute(self) -> Any:
        """Execute the underlying function with stored arguments.

        Returns:
            Any: The function's return value.
        """
        return self.fn.execute(**self.packed_kwargs.unpack())


    @property
    def addr(self) -> ValueAddr:
        """Address uniquely identifying this call signature.

        Returns:
            ValueAddr: Address of the LoggingFnCallSignature persisted in portal.
        """
        if hasattr(self, "_addr_cache") and self._addr_cache is not None:
            return self._addr_cache
        with self.portal:
            self._addr_cache = ValueAddr(self)
            return self._addr_cache


    @property
    def execution_attempts(self) -> PersiDict:
        """Timeline of execution attempts metadata for this call.

        Returns:
            PersiDict: Append-only JSON sub-dictionary keyed by timestamped IDs.
        """
        with self.portal as portal:
            attempts_path = self.addr + ["attempts"]
            attempts = portal._run_history.json.get_subdict(attempts_path)
            return attempts


    @property
    def last_execution_attempt(self) -> Any:
        """Most recent execution attempt metadata, if any.

        Returns:
            Any: Latest attempt metadata dict, or None if no attempts exist.
        """
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
        """Timeline of execution results for this call.

        Returns:
            PersiDict: Append-only PKL sub-dictionary storing returned values.
        """
        with self.portal as portal:
            results_path = self.addr + ["results"]
            results = portal._run_history.pkl.get_subdict(results_path)
            return results


    @property
    def last_execution_result(self) -> Any:
        """Most recent execution result, if any.

        Returns:
            Any: Latest return value, or None if no results exist.
        """
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
        """Timeline of captured stdout/stderr/logging output for this call.

        Returns:
            PersiDict: Append-only TXT sub-dictionary of captured output strings.
        """
        with self.portal as portal:
            outputs_path = self.addr + ["outputs"]
            outputs = portal._run_history.txt.get_subdict(outputs_path)
            return outputs


    @property
    def last_execution_output(self) -> Any:
        """Most recent captured combined output, if any.

        Returns:
            Any: Latest captured output string, or None if no outputs exist.
        """
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
        """Timeline of crashes (exceptions) observed during this call.

        Returns:
            PersiDict: Append-only JSON sub-dictionary of exception payloads.
        """
        with self.portal as portal:
            crashes_path = self.addr + ["crashes"]
            crashes = portal._run_history.json.get_subdict(crashes_path)
            return crashes


    @property
    def last_crash(self) -> Any:
        """Most recent crash payload, if any.

        Returns:
            Any: Latest exception payload dict, or None if no crashes exist.
        """
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
        """Timeline of user events emitted during this call.

        Returns:
            PersiDict: Append-only JSON sub-dictionary of event payloads.
        """
        with self.portal as portal:
            events_path = self.addr + ["events"]
            events = portal._run_history.json.get_subdict(events_path)
            return events


    @property
    def last_event(self) -> Any:
        """Most recent user event payload, if any.

        Returns:
            Any: Latest event payload dict, or None if no events exist.
        """
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
        """All execution sessions derived from attempts for this call.

        Returns:
            list[LoggingFnExecutionRecord]: Records constructed from stored
            attempt IDs for convenient access to artifacts per run session.
        """
        with self.portal:
            result = []
            for k in self.execution_attempts:
                run_id = k[-1][:-9]
                result.append(LoggingFnExecutionRecord(self, run_id))
            return result


class LoggingFnExecutionRecord(NotPicklableClass):
    """Record of a single function execution session.

    Provides convenient accessors to all artifacts logged for one particular
    execution of a LoggingFn: environment context, captured output, crashes,
    events, and the returned result value.

    Attributes:
        call_signature (LoggingFnCallSignature): The function-call identity
            this record belongs to.
        session_id (str): Unique identifier for the execution session ("run_*"),
            shared by all artifacts emitted during this run.
    """
    call_signature: LoggingFnCallSignature
    session_id: str
    def __init__(
            self
            , call_signature: LoggingFnCallSignature
            , session_id: str):
        """Construct an execution record.

        Args:
            call_signature: The call signature the record is associated with.
            session_id: The unique ID of the execution session.
        """
        self.call_signature = call_signature
        self.session_id = session_id


    @property
    def portal(self):
        """LoggingCodePortal used to resolve underlying artifacts.

        Returns:
            LoggingCodePortal: The portal associated with the call signature.
        """
        return self.call_signature.portal


    @property
    def output(self) -> str|None:
        """Combined stdout/stderr/logging output captured for the session.

        Returns:
            str | None: The captured text output, or None when no output
            was recorded for this session.
        """
        with self.portal:
            execution_outputs = self.call_signature.execution_outputs
            for k in execution_outputs:
                if self.session_id in k[-1]:
                    return execution_outputs[k]
            return None


    @property
    def attempt_context(self)-> dict|None:
        """Environment/context snapshot captured at attempt start.

        Returns:
            dict | None: The environment summary dict for this session, or
            None if not present (e.g., excessive logging disabled).
        """
        with self.portal:
            execution_attempts = self.call_signature.execution_attempts
            for k in execution_attempts:
                if self.session_id in k[-1]:
                    return execution_attempts[k]
            return None


    @property
    def crashes(self) -> list[dict]:
        """All exceptions recorded during the session.

        Returns:
            list[dict]: A list of exception payload dicts in chronological order.
        """
        result = []
        with self.portal:
            crashes = self.call_signature.crashes
            for k in crashes:
                if self.session_id in k[-1]:
                    result.append(crashes[k])
        return result


    @property
    def events(self) -> list[dict]:
        """All events recorded during the session.

        Returns:
            list[dict]: A list of event payload dicts in chronological order.
        """
        result = []
        with self.portal:
            events = self.call_signature.events
            for k in events:
                if self.session_id in k[-1]:
                    result.append(events[k])
        return result


    @property
    def result(self)->Any:
        """Return value produced by the function in this session.

        Returns:
            Any: The object returned by the wrapped function for the run.

        Raises:
            ValueError: If there is no stored result for this session ID.
        """
        with self.portal:
            execution_results = self.call_signature.execution_results
            for k in execution_results:
                if self.session_id in k[-1]:
                    return execution_results[k].get()
            raise ValueError(
                f"Result for session {self.session_id} not found in "
                f"{self.call_signature.fn_name} execution results.")


class LoggingFnExecutionFrame(NotPicklableClass):
    """Context manager managing a single function execution with logging.

    When used as a context, optionally captures stdout/stderr/logging,
    registers attempt metadata, stores results and output, and routes
    exceptions/events to both per-call artifacts and portal-level histories.

    Attributes:
        call_stack (list[LoggingFnExecutionFrame]): Class-level stack of active
            frames (last item is the current execution frame).
    """
    call_stack: list[LoggingFnExecutionFrame] = []

    session_id: str
    fn_call_addr: ValueAddr
    fn_call_signature: LoggingFnCallSignature
    output_capturer: OutputCapturer | None
    exception_counter: int
    event_counter: int
    context_used: bool

    def __init__(self, fn_call_signature: LoggingFnCallSignature):
        """Initialize the execution frame for a specific function call.

        Args:
            fn_call_signature: The call signature identifying the function and
                its (packed) arguments.
        """
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
        """Portal associated with the current execution frame.

        Returns:
            LoggingCodePortal: The portal used for logging within this frame.
        """
        return self.fn.portal


    @property
    def fn(self) -> LoggingFn:
        """The LoggingFn being executed in this frame.

        Returns:
            LoggingFn: The wrapped function object.
        """
        return self.fn_call_signature.fn


    @property
    def fn_name(self) -> str:
        """Name of the function being executed.

        Returns:
            str: The wrapped function's name.
        """
        return self.fn_call_signature.fn_name


    @property
    def excessive_logging(self) -> bool:
        """Whether the frame should capture detailed artifacts.

        Returns:
            bool: True if excessive logging is enabled for the function.
        """
        return self.fn.excessive_logging


    @property
    def fn_addr(self) -> ValueAddr:
        """Address of the wrapped function in storage.

        Returns:
            ValueAddr: The persisted address of the LoggingFn.
        """
        return self.fn_call_signature.fn_addr


    @property
    def packed_args(self) -> PackedKwArgs:
        """Packed keyword arguments used for this execution.

        Returns:
            PackedKwArgs: The packed argument mapping.
        """
        return self.fn_call_signature.packed_kwargs


    @property
    def kwargs_addr(self) -> ValueAddr:
        """Address of the packed arguments in storage.

        Returns:
            ValueAddr: The persisted address of the packed kwargs.
        """
        return self.fn_call_signature.kwargs_addr


    def __enter__(self):
        """Enter the execution frame context.

        Performs sanity checks, enters the portal context, optionally starts
        capturing output, pushes the frame onto the call stack, and registers
        an execution attempt if excessive logging is enabled.

        Returns:
            LoggingFnExecutionFrame: This frame instance for use as a context var.
        """
        if self.context_used:
            raise RuntimeError(f"An instance of PureFnExecutionFrame can be used only once.")
        self.context_used = True
        if self.exception_counter != 0:
            raise RuntimeError(f"An instance of PureFnExecutionFrame can be used only once.")
        if self.event_counter != 0:
            raise RuntimeError(f"An instance of PureFnExecutionFrame can be used only once.")
        self.portal.__enter__()
        if isinstance(self.output_capturer, OutputCapturer):
            self.output_capturer.__enter__()
        LoggingFnExecutionFrame.call_stack.append(self)
        self._register_execution_attempt()
        return self


    def _register_execution_attempt(self):
        """Record an execution attempt with environment and source snapshot.

        No-op when excessive logging is disabled.
        """
        if not self.excessive_logging:
            return
        execution_attempts = self.fn_call_signature.execution_attempts
        attempt_id = self.session_id+"_attempt"
        execution_attempts[attempt_id] = build_execution_environment_summary()
        self.portal._run_history.py[self.fn_call_signature.addr + ["source"]] = (
            self.fn.source_code)


    def _register_execution_result(self, result: Any):
        """Store the function's return value into the results timeline.

        Args:
            result: The value returned by the wrapped function.

        Notes:
            No-op when excessive logging is disabled.
        """
        if not self.excessive_logging:
            return
        execution_results = self.fn_call_signature.execution_results
        result_id = self.session_id+"_result"
        execution_results[result_id] = ValueAddr(result)


    def __exit__(self, exc_type, exc_value, trace_back):
        """Exit the execution frame context.

        Ensures the current exception (if any) is logged, finalizes output
        capture and stores it, pops the frame from the call stack, and exits
        the underlying portal context.

        Args:
            exc_type: Exception class raised within the context, if any.
            exc_value: Exception instance raised within the context, if any.
            trace_back: Traceback object associated with the exception, if any.
        """
        log_exception()
        if isinstance(self.output_capturer, OutputCapturer):
            self.output_capturer.__exit__(exc_type, exc_value, traceback)
            output_id = self.session_id+"_output"
            execution_outputs = self.fn_call_signature.execution_outputs
            execution_outputs[output_id] = self.output_capturer.get_output()

        self.portal.__exit__(exc_type, exc_value, traceback)
        LoggingFnExecutionFrame.call_stack.pop()


_EXCEPTIONS_TOTAL_TXT = "Exceptions, total"
_EXCEPTIONS_TODAY_TXT = "Exceptions, today"
_EXCESSIVE_LOGGING_TXT = "Excessive logging"

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
        """Construct a LoggingCodePortal.

        Args:
            root_dict: PersiDict instance or filesystem path serving as the
                storage root. When None, a default in-memory or configured
                PersiDict is used by the base DataPortal.
            p_consistency_checks: Probability [0..1] to run consistency checks
                on storage operations; KEEP_CURRENT inherits existing setting.
            excessive_logging: If True, functions executed via this portal will
                store detailed artifacts (attempts/results/outputs). If
                KEEP_CURRENT, the setting is inherited when cloning or
                otherwise unspecified.

        Raises:
            TypeError: If excessive_logging is not a bool or Joker.
        """
        super().__init__(root_dict=root_dict
            , p_consistency_checks=p_consistency_checks)
        del root_dict

        if not isinstance(excessive_logging,(Joker,bool)):
            raise TypeError(
                "excessive_logging must be a boolean or Joker, "
                f"got {type(excessive_logging)}")

        self._auxiliary_config_params_at_init["excessive_logging"
            ] = excessive_logging

        crash_history_prototype = self._root_dict.get_subdict("crash_history")
        crash_history_params = crash_history_prototype.get_params()
        crash_history_params.update(
            dict(serialization_format="json", append_only=True , digest_len=0))
        self._crash_history = type(self._root_dict)(**crash_history_params)

        event_history_prototype = self._root_dict.get_subdict("event_history")
        event_history_params = event_history_prototype.get_params()
        event_history_params.update(
            dict(serialization_format="json", append_only=True, digest_len=0))
        self._event_history = type(self._root_dict)(**event_history_params)

        run_history_prototype = self._root_dict.get_subdict("run_history")
        run_history_shared_params = run_history_prototype.get_params()
        dict_type = type(self._root_dict)
        run_history = OverlappingMultiDict(
            dict_type=dict_type
            , shared_subdicts_params=run_history_shared_params
            , json=dict(append_only=True)
            , py=dict(base_class_for_values=str, append_only=False) # Immutable items????
            , txt=dict(base_class_for_values=str, append_only=True)
            , pkl=dict(append_only=True)
        )
        self._run_history = run_history

        register_systemwide_uncaught_exception_handlers()


    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the portal context, ensuring any active exception is logged.

        Args:
            exc_type: Exception class raised within the portal context, if any.
            exc_val: Exception instance, if any.
            exc_tb: Traceback object, if any.
        """
        log_exception()
        super().__exit__(exc_type, exc_val, exc_tb)


    @property
    def excessive_logging(self) -> bool:
        """Whether this portal captures detailed per-call artifacts.

        Returns:
            bool: True if excessive logging is enabled, False otherwise.
        """
        return bool(self._get_config_setting("excessive_logging"))


    def describe(self) -> pd.DataFrame:
        """Summarize the portal's current persistent and runtime state.

        Returns:
            pandas.DataFrame: A table with key characteristics, including
            total crashes logged, today's crashes, and whether excessive
            logging is enabled, combined with the base DataPortal summary.
        """
        all_params = [super().describe()]
        all_params.append(_describe_persistent_characteristic(
            _EXCEPTIONS_TOTAL_TXT, len(self._crash_history)))
        all_params.append(_describe_persistent_characteristic(
            _EXCEPTIONS_TODAY_TXT
            , len(self._crash_history.get_subdict(current_date_gmt_string()))))
        all_params.append(_describe_runtime_characteristic(
            _EXCESSIVE_LOGGING_TXT, self.excessive_logging))

        result = pd.concat(all_params)
        result.reset_index(drop=True, inplace=True)
        return result


    def _clear(self) -> None:
        """Clear the portal's internal state and unregister handlers.

        Side Effects:
            - Drops references to crash/event/run histories.
            - Unregisters global uncaught exception handlers.
        """
        self._crash_history = None
        self._event_log = None
        self._run_history = None
        unregister_systemwide_uncaught_exception_handlers()
        super()._clear()


def log_exception() -> None:
    """Log the currently handled exception to the active LoggingCodePortal.

    Captures the exception from sys.exc_info(), enriches it with execution
    environment context, and stores it in the portal-level crash history. If
    called during a function execution with excessive logging enabled, also
    stores the event under the function's per-call crash log.

    Returns:
        None
    """
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
    """Record an application event to the active LoggingCodePortal.

    Adds environment context and optional positional messages to the event
    payload. When called during a function execution, also attaches the event
    to that call's event log.

    Args:
        *args: Optional positional messages to include in the event payload.
        **kwargs: Key-value pairs forming the body of the event.

    Returns:
        None
    """
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