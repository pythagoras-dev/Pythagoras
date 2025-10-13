"""Classes to work with pure functions.

A pure function is a protected function that has no side effects and
always returns the same result if it is called multiple times
with the same arguments.

This subpackage defines a decorator which is used to inform Pythagoras that
a function is intended to be pure: @pure().

Pythagoras persistently caches results, produced by a pure function, so that
if the function is called multiple times with the same arguments,
the function is executed only once, and the cached result is returned
for all the subsequent executions.

While caching the results of a pure function, Pythagoras also tracks
changes in the source code of the function. If the source code of a pure
function changes, the function is executed again on the next call.
However, the previously cached results are still available
for the old version of the function. Only changes in the function's
source code are tracked.
"""

from __future__ import annotations

import time
from copy import copy
from typing import Callable, Any, List, TypeAlias

import pandas as pd
# from sklearn.model_selection import ParameterGrid

from persidict import PersiDict, Joker, KEEP_CURRENT

from persidict import WriteOnceDict

from .._010_basic_portals import *
from .._010_basic_portals.basic_portal_core_classes import (
    _describe_persistent_characteristic)

from .._030_data_portals import HashAddr, ValueAddr
from .._040_logging_code_portals import *


from .._070_protected_code_portals import *

ASupportingFunc:TypeAlias = str | AutonomousFn

SupportingFuncs:TypeAlias = ASupportingFunc | List[ASupportingFunc] | None

_CACHED_EXECUTION_RESULTS_TXT = "Cached execution results"
_EXECUTION_QUEUE_SIZE_TXT = "Execution queue size"

class PureCodePortal(ProtectedCodePortal):
    """Portal that manages execution and caching for pure functions.

    The portal extends ProtectedCodePortal with two persistent dictionaries:
    - execution_results: append-only, stores ValueAddr of function outputs
    - execution_requests: mutable, tracks pending execution requests
    """

    _execution_results: PersiDict | None
    _execution_requests: PersiDict | None

    def __init__(self
            , root_dict: PersiDict | str | None = None
            , p_consistency_checks: float | Joker = KEEP_CURRENT
            , excessive_logging: bool | Joker = KEEP_CURRENT
            ):
        """Initialize a PureCodePortal instance.

        Args:
            root_dict: Backing persistent dictionary or path used to create it.
            p_consistency_checks: Probability [0..1] to re-check cached
                results for consistency. KEEP_CURRENT to inherit.
            excessive_logging: Verbosity flag; KEEP_CURRENT to inherit.
        """
        ProtectedCodePortal.__init__(self
            , root_dict=root_dict
            , p_consistency_checks=p_consistency_checks
            , excessive_logging=excessive_logging)

        results_dict_prototype = self._root_dict.get_subdict(
            "execution_results")
        results_dict_params = results_dict_prototype.get_params()
        results_dict_params.update(append_only=True,  serialization_format = "pkl")
        execution_results = type(self._root_dict)(**results_dict_params)
        execution_results = WriteOnceDict(execution_results, 0)
        self._execution_results = execution_results

        requests_dict_prototype = self._root_dict.get_subdict(
            "execution_requests")
        requests_dict_params = requests_dict_prototype.get_params()
        requests_dict_params.update(append_only=False, serialization_format="pkl")
        execution_requests = type(self._root_dict)(**requests_dict_params)
        self._execution_requests = execution_requests


    def _post_init_hook(self) -> None:
        """Hook to be called after all __init__ methods are done"""
        super()._post_init_hook()
        p = self.p_consistency_checks
        self._execution_results._p_consistency_checks = p


    def describe(self) -> pd.DataFrame:
        """Describe the portal state as a DataFrame.

        Returns:
            pandas.DataFrame: Concatenated report that includes base portal
            parameters plus counts of cached execution results and queued
            execution requests.
        """
        all_params = [super().describe()]

        all_params.append(_describe_persistent_characteristic(
            _CACHED_EXECUTION_RESULTS_TXT, len(self._execution_results)))
        all_params.append(_describe_persistent_characteristic(
            _EXECUTION_QUEUE_SIZE_TXT, len(self._execution_requests)))

        result = pd.concat(all_params)
        result.reset_index(drop=True, inplace=True)
        return result

    def _clear(self):
        """Release references to backing dicts and clear base portal state."""
        self._execution_results = None
        self._execution_requests = None
        super()._clear()


class PureFnCallSignature(ProtectedFnCallSignature):
    """A signature of a call to a pure function"""
    _fn_cache: PureFn | None
    _execution_results_addr_cache: PureFnExecutionResultAddr | None

    def __init__(self, fn: PureFn, arguments: dict):
        """Create a signature object for a specific PureFn call.

        Args:
            fn: The pure function being called.
            arguments: Keyword arguments for the call.
        """
        if not isinstance(fn, PureFn):
            raise TypeError(f"fn must be a PureFn instance, got {type(fn).__name__}")
        if not isinstance(arguments, dict):
            raise TypeError(f"arguments must be a dict, got {type(arguments).__name__}")
        super().__init__(fn, arguments)

    @property
    def fn(self) -> PureFn:
        """Return the function object referenced by the signature."""
        return super().fn

    @property
    def execution_results_addr(self) -> PureFnExecutionResultAddr:
        """Return the address of the execution results of the function call."""
        if not hasattr(self, "_execution_results_addr_cache"):
            self._execution_results_addr_cache = PureFnExecutionResultAddr(
                fn=self.fn, arguments=self.packed_kwargs)
        return self._execution_results_addr_cache


class PureFn(ProtectedFn):
    """Wrapper around a callable that provides pure-function semantics.

    A PureFn executes inside a PureCodePortal, caches results by call
    signature, and exposes convenience APIs to request execution, run
    immediately, and retrieve results via address objects.
    """

    def __init__(self, fn: Callable | str
                 , pre_validators: list[AutonomousFn] | List[Callable] | None = None
                 , post_validators: list[AutonomousFn] | List[Callable] | None = None
                 , excessive_logging: bool | Joker = KEEP_CURRENT
                 , fixed_kwargs: dict | None = None
                 , portal: PureCodePortal | None = None):
        """Construct a PureFn.

        Args:
            fn: Target callable.
            pre_validators: Optional list of pre-execution validators.
            post_validators: Optional list of post-execution validators.
            excessive_logging: Verbosity flag; KEEP_CURRENT to inherit.
            fixed_kwargs: Mapping of argument names to fixed values injected
                into each call.
            portal: Optional PureCodePortal to bind this PureFn to.
        """
        ProtectedFn.__init__(self
                             , fn=fn
                             , portal = portal
                             , fixed_kwargs=fixed_kwargs
                             , excessive_logging = excessive_logging
                             , pre_validators=pre_validators
                             , post_validators=post_validators)


    def get_address(self, **kwargs) -> PureFnExecutionResultAddr:
        """Build an address object for a call with the given arguments.

        Args:
            **kwargs: Keyword arguments to pass to the function.

        Returns:
            PureFnExecutionResultAddr: Address referencing the (cached or
            future) result corresponding to the provided arguments.
        """
        with self.portal:
            packed_kwargs = KwArgs(**kwargs).pack()
            return PureFnExecutionResultAddr(self, packed_kwargs)


    def get_signature(self, arguments: dict) -> PureFnCallSignature:
        """Build a call signature for the given arguments.

        Args:
            arguments: Keyword arguments for a potential call.

        Returns:
            PureFnCallSignature: The signature object identifying the call.
        """
        return PureFnCallSignature(self, arguments)


    def swarm(self, **kwargs) -> PureFnExecutionResultAddr:
        """Request background function execution for the given arguments.

        The function is not executed immediately; instead, an execution request
        is recorded in the portal. The returned address can later be used to
        check readiness or retrieve the value.

        Args:
            **kwargs: Keyword arguments to pass to the underlying function.

        Returns:
            PureFnExecutionResultAddr: Address that identifies the pending (or
            already cached) execution result for these arguments.
        """
        with self.portal:
            result_address = self.get_address(**kwargs)
            result_address.request_execution()
            return result_address

    def run(self, **kwargs) -> PureFnExecutionResultAddr:
        """Execute immediately and return the result address.

        The function is executed synchronously within the current process.

        Args:
            **kwargs: Keyword arguments to pass to the underlying function.

        Returns:
            PureFnExecutionResultAddr: Address of the computed value (which can
            be used to fetch logs/metadata or the value again if needed).
        """
        with self.portal:
            result_address = self.get_address(**kwargs)
            result_address.execute()
            return result_address


    def execute(self, **kwargs) -> Any:
        """Execute the function with the given arguments and return the result.

        The function is executed immediately and its result is memoized by the
        portal. Subsequent calls with identical arguments return the cached
        value (optionally performing consistency checks depending on the
        portal's p_consistency_checks setting).

        Args:
            **kwargs: Keyword arguments to pass to the underlying function.

        Returns:
            Any: The computed result value.
        """

        with self.portal as portal:
            packed_kwargs = KwArgs(**kwargs).pack()
            output_address = PureFnExecutionResultAddr(
                fn=self, arguments=packed_kwargs)
            random_x = portal.entropy_infuser.random()
            p_consistency_checks = portal.p_consistency_checks
            conduct_consistency_checks = False
            if output_address.ready:
                if p_consistency_checks in [None,0]:
                    return output_address.get()
                if not random_x < p_consistency_checks:
                    return output_address.get()
                conduct_consistency_checks = True
            else:
                output_address.request_execution()
            unpacked_kwargs = KwArgs(**packed_kwargs).unpack()
            result = super().execute(**unpacked_kwargs)
            result_addr = ValueAddr(result)
            try:
                if conduct_consistency_checks:
                    portal._execution_results._p_consistency_checks = 1
                portal._execution_results[output_address] = result_addr
            finally:
                portal._execution_results._p_consistency_checks = (
                    p_consistency_checks)
            output_address.drop_execution_request()
            return result


    def swarm_list(
            self
            , list_of_kwargs:list[dict]
            ) -> list[PureFnExecutionResultAddr]:
        """Queue background execution for a batch of argument sets.

        Args:
            list_of_kwargs: A list of keyword-argument mappings. Each mapping
                represents one call to the function.

        Returns:
            list[PureFnExecutionResultAddr]: Addresses for all requested
            executions, in the same order as the input list.
        """
        if not isinstance(list_of_kwargs, (list, tuple)):
            raise TypeError(f"list_of_kwargs must be a list or tuple, got {type(list_of_kwargs).__name__}")
        for kwargs in list_of_kwargs:
            if not isinstance(kwargs, dict):
                raise TypeError(f"Each item in list_of_kwargs must be a dict, got {type(kwargs).__name__}")
        with self.portal:
            list_to_return = []
            list_to_swarm = []
            for kwargs in list_of_kwargs:
                new_addr = PureFnExecutionResultAddr(self, kwargs)
                list_to_return.append(new_addr)
                list_to_swarm.append(new_addr)
            self.portal.entropy_infuser.shuffle(list_to_swarm)
            for an_addr in list_to_swarm:
                an_addr.request_execution()
        return list_to_return


    def run_list(
            self
            , list_of_kwargs:list[dict]
            ) -> list[PureFnExecutionResultAddr]:
        """Execute a batch of calls immediately and return their addresses.

        Execution is performed in a shuffled order.

        Args:
            list_of_kwargs: A list of keyword-argument mappings for each call.

        Returns:
            list[PureFnExecutionResultAddr]: Addresses for the executed calls,
            in the same order as the input list.
        """
        with self.portal:
            addrs = self.swarm_list(list_of_kwargs)
            addrs_workspace = copy(addrs)
            self.portal.entropy_infuser.shuffle(addrs_workspace)
            for an_addr in addrs_workspace:
                an_addr.execute()
        return addrs


    # def swarm_grid(
    #         self
    #         , grid_of_kwargs:dict[str, list] # refactor
    #         ) -> list[PureFnExecutionResultAddr]:
    #     with self.portal:
    #         param_list = list(ParameterGrid(grid_of_kwargs))
    #         addrs = self.swarm_list(param_list)
    #         return addrs
    #
    #
    # def run_grid(
    #         self
    #         , grid_of_kwargs:dict[str, list] # refactor
    #         ) -> list[PureFnExecutionResultAddr]:
    #     with self.portal:
    #         param_list = list(ParameterGrid(grid_of_kwargs))
    #         addrs = self.run_list(param_list)
    #         return addrs


    @property
    def portal(self) -> PureCodePortal:
        """Active PureCodePortal used for this function execution.

        Returns:
            PureCodePortal: The portal that governs execution and persistence
            for this PureFn (falls back to the current active portal if this
            function isn't explicitly bound).
        """
        return super().portal


class PureFnExecutionResultAddr(HashAddr):
    """An address of a (future) result of pure function execution.

    This class is used to point to the result of an execution of a pure
    function in a portal. The address is used to request an execution or
    to retrieve the result (if available) from the portal.

    The address also provides access to various logs and records of the
    function execution, such as environmental contexts of the execution attempts,
    outputs printed, exceptions thrown, and events emitted.
    """
    _fn_cache: PureFn | None
    _call_signature_cache: PureFnCallSignature | None
    _kwargs_cache: KwArgs | None

    _result_cache: Any | None
    _ready_cache: bool | None

    def __init__(self, fn: PureFn, arguments:dict[str, Any]):
        """Create an address for a pure-function execution result.

        Args:
            fn: The PureFn whose execution result is addressed.
            arguments: The keyword arguments for the call (packed dict).
        """
        if not isinstance(fn, PureFn):
            raise TypeError(f"fn must be a PureFn instance, got {type(fn).__name__}")
        with fn.portal as portal:
            self._kwargs_cache = KwArgs(**arguments)
            self._fn_cache = fn
            signature = PureFnCallSignature(fn, self._kwargs_cache)
            self._call_signature_cache = signature
            tmp = ValueAddr(signature)
            new_descriptor = fn.name +"_result_addr"
            new_hash_signature = tmp.hash_signature
            super().__init__(new_descriptor, new_hash_signature)


    def _invalidate_cache(self):
        """Invalidate the object's attribute cache.

        If the object's attribute named ATTR is cached,
        its cached value will be stored in an attribute named _ATTR_cache
        This method should delete all such attributes.
        """
        if hasattr(self, "_ready_cache"):
            del self._ready_cache
        if hasattr(self, "_result_cache"):
            del self._result_cache
        if hasattr(self, "_fn_cache"):
            del self._fn_cache
        if hasattr(self, "_kwargs_cache"):
            del self._kwargs_cache
        if hasattr(self, "_call_signature_cache"):
            del self._call_signature_cache
        super()._invalidate_cache()


    def get_ValueAddr(self):
        descriptor = self.descriptor.removesuffix("_result_addr")
        descriptor += "_" + PureFnCallSignature.__name__.lower()
        return ValueAddr.from_strings(  # TODO: refactor this
            descriptor= descriptor
            , hash_signature=self.hash_signature)


    @property
    def call_signature(self) -> PureFnCallSignature:
        """The PureFnCallSignature for this address' call."""
        if (not hasattr(self, "_call_signature_cache")
            or self._call_signature_cache is None):
            self._call_signature_cache = self.get_ValueAddr().get()
        return self._call_signature_cache


    @property
    def fn(self) -> PureFn:
        """Return the function object referenced by the address."""
        if not hasattr(self, "_fn_cache") or self._fn_cache is None:
            self._fn_cache = self.call_signature.fn
        return self._fn_cache


    @property
    def kwargs(self) -> KwArgs:
        """Unpacked arguments of the function call, referenced by the address."""
        if not hasattr(self, "_kwargs_cache") or self._kwargs_cache is None:
            with self.fn.portal:
                self._kwargs_cache = self.call_signature.kwargs_addr.get().unpack()
        return self._kwargs_cache


    def __setstate__(self, state):
        """This method is called when the object is unpickled."""
        self._invalidate_cache()
        self.strings = state["strings"]


    def __getstate__(self):
        """This method is called when the object is pickled."""
        state = dict(strings=self.strings)
        return state


    @property
    def _ready_in_active_portal(self):
        """Indicates if the result of the function call is available."""
        result = (self in get_active_portal()._execution_results)
        if result:
            self._ready_cache = True
        return result

    @property
    def _ready_in_nonactive_portals(self) -> bool:
        """Try importing a ready result from non-active portals.

        If another known portal already has the execution result, copy the
        corresponding key/value into the active portal's stores.

        Returns:
            bool: True if the value was found in a non-active portal and
            imported; False otherwise.
        """
        for another_portal in get_nonactive_portals():
            with another_portal:
                if self in another_portal._execution_results:
                    addr = another_portal._execution_results[self]
                    with self.fn.portal as active_portal:
                        active_portal._execution_results[self] = addr
                        if not addr in active_portal._value_store:
                            data = another_portal._value_store[addr]
                            self._result_cache = data
                            active_portal._value_store[addr] = data
                    return True
        return False

    @property
    def ready(self) -> bool:
        """Whether the execution result is already available.

        Returns:
            bool: True if the result is present in the active portal (or can
            be imported from a known non-active portal); False otherwise.
        """
        if hasattr(self, "_ready_cache"):
            if not self._ready_cache:
                raise RuntimeError(f"Internal inconsistency: _ready_cache is set but False for address {self}")
            return True
        with self.fn.portal:
            if self._ready_in_active_portal:
                self._ready_cache = True
                return True
            if self._ready_in_nonactive_portals:
                self._ready_cache = True
                return True
        return False


    def execute(self):
        """Execute the function and store the result in the portal.

        Returns:
            Any: The computed result of the underlying pure function call.
        """
        if hasattr(self, "_result_cache"):
            return self._result_cache
        with self.fn.portal:
            self._result_cache = self.fn.execute(**self.kwargs)
            return self._result_cache


    def request_execution(self):
        """Request execution of the function, without actually executing it."""
        with self.fn.portal as portal:
            if self.ready:
                self.drop_execution_request()
            else:
                portal._execution_requests[self] = True


    def drop_execution_request(self):
        """Remove the request for execution from all known portals"""
        for portal in get_all_known_portals():
            with portal:
                portal._execution_requests.delete_if_exists(self)


    @property
    def execution_requested(self):
        """Whether execution for this call has been requested.

        Returns:
            bool: True if there's a pending execution request in the active
            portal or any known non-active portal (also synchronizes the
            request into the active portal); False otherwise.
        """
        with self.fn.portal as active_portal:
            if self in active_portal._execution_requests:
                return True
            for another_portal in get_nonactive_portals():
                if self in another_portal._execution_requests:
                    active_portal._execution_requests[self] = True
                    return True
        return False


    def get(self, timeout: int = None):
        """Retrieve the value referenced by this address, waiting if needed.

        The method does not execute the function itself. If the value is not
        immediately available, it requests execution and waits with
        exponential backoff until the result arrives or the timeout elapses.

        Args:
            timeout: Optional maximum number of seconds to wait. If None,
                tries/waits indefinitely.

        Returns:
            Any: The value produced by the pure function call.

        Raises:
            TimeoutError: If the timeout elapses before the value becomes
                available.
        """
        if timeout is not None and timeout < 0:
            raise ValueError(f"timeout must be None or non-negative, got {timeout}")
        if hasattr(self, "_result_cache"):
            return self._result_cache

        with self.fn.portal as portal:

            if self.ready:
                result_addr = portal._execution_results[self]
                self._result_cache = portal._value_store[result_addr]
                return self._result_cache

            self.request_execution()

            start_time, backoff_period = time.time(), 1.0
            if timeout is not None:
                stop_time = start_time + timeout
            else:
                stop_time = None
            # start_time, stop_time and backoff_period are in seconds

            while True:
                if self.ready:
                    result_addr = portal._execution_results[self]
                    self._result_cache = portal._value_store[result_addr]
                    self.drop_execution_request()
                    return self._result_cache
                else:
                    time.sleep(backoff_period)
                    backoff_period *= 2.0
                    backoff_period += portal.entropy_infuser.uniform(-0.5, 0.5)
                    if stop_time:
                        current_time = time.time()
                        if current_time + backoff_period > stop_time:
                            backoff_period = stop_time - current_time
                        if current_time > stop_time:
                            raise TimeoutError
                    backoff_period = max(1.0, backoff_period)


    @property
    def can_be_executed(self) -> PureFnCallSignature | ValidationSuccessFlag | None:
        """Whether execution is currently feasible.

        This checks pre-validators/guards for the underlying pure function and
        returns a directive for the protected execution pipeline.

        Returns:
            PureFnCallSignature | ValidationSuccessFlag | None: If a dependent
            call must be executed first, returns its call signature; if checks
            pass immediately, returns VALIDATION_SUCCESSFUL; otherwise None to
            indicate that the execution is not possible.
        """
        with self.fn.portal:
            return self.fn.can_be_executed(self.kwargs)


    @property
    def needs_execution(self) -> bool:
        """Indicates if the function is a good candidate for execution.

        Returns False if the result is already available, or if some other
        process is currently working on it, or if there were too many
        past attempts to execute it. Otherwise, returns True.
        """
        _DEFAULT_EXECUTION_TIME = 10 #TODO: move to portal config
        _MAX_EXECUTION_ATTEMPTS = 5
        # TODO: these should not be constants
        if self.ready:
            return False
        with self.fn.portal:
            past_attempts = self.call_signature.execution_attempts
            n_past_attempts = len(past_attempts)
            if n_past_attempts == 0:
                return True
            if n_past_attempts > _MAX_EXECUTION_ATTEMPTS:
                #TODO: log this event. Should we have DLQ?
                return False
            most_recent_timestamp = max(
                past_attempts.timestamp(a) for a in past_attempts)
            current_timestamp = time.time()
            if (current_timestamp - most_recent_timestamp
                    > _DEFAULT_EXECUTION_TIME*(2**n_past_attempts)):
                return True
            return False