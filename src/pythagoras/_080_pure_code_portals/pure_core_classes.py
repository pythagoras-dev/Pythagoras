from __future__ import annotations

import time
from copy import copy
from typing import Callable, Any, List, TypeAlias

import pandas as pd
from sklearn.model_selection import ParameterGrid

from persidict import PersiDict

from .._010_basic_portals.portal_aware_class import _noncurrent_portals
from .._010_basic_portals.portal_aware_dict import PortalAwareDict
from .._070_protected_code_portals import ProtectedCodePortal, ProtectedFn
from .._010_basic_portals.basic_portal_class import (
    _describe_persistent_characteristic)
from .._800_persidict_extensions.first_entry_dict import FirstEntryDict
from .._040_logging_code_portals.logging_portal_core_classes import (
    LoggingFnCallSignature)

from .._030_data_portals import HashAddr, ValueAddr

from .._060_autonomous_code_portals.autonomous_portal_core_classes import (
    AutonomousFn)


from .._040_logging_code_portals.kw_args import KwArgs


ASupportingFunc:TypeAlias = str | AutonomousFn

SupportingFuncs:TypeAlias = ASupportingFunc | List[ASupportingFunc] | None

CACHED_EXECUTION_RESULTS_TXT = "Cached execution results"
EXECUTION_QUEUE_SIZE_TXT = "Execution queue size"

class PureCodePortal(ProtectedCodePortal):

    execution_results: PortalAwareDict | None
    execution_requests: PersiDict | None

    def __init__(self
            , root_dict: PersiDict | str | None = None
            , p_consistency_checks: float | None = None
            , excessive_logging: bool = False
            ):
        super().__init__(root_dict=root_dict
            , p_consistency_checks=p_consistency_checks
            , excessive_logging=excessive_logging)

        results_dict_prototype = self._root_dict.get_subdict(
            "execution_results")
        results_dict_params = results_dict_prototype.get_params()
        results_dict_params.update(immutable_items=True,  file_type = "pkl")
        execution_results = type(self._root_dict)(**results_dict_params)
        execution_results = FirstEntryDict(
            execution_results, p_consistency_checks)
        execution_results = PortalAwareDict(execution_results, portal = self)
        self.execution_results = execution_results

        requests_dict_prototype = self._root_dict.get_subdict(
            "execution_requests")
        requests_dict_params = requests_dict_prototype.get_params()
        requests_dict_params.update(immutable_items=False, file_type="pkl")
        execution_requests = type(self._root_dict)(**requests_dict_params)
        self.execution_requests = execution_requests


    def describe(self) -> pd.DataFrame:
        """Get a DataFrame describing the portal's current state"""
        all_params = [super().describe()]

        all_params.append(_describe_persistent_characteristic(
            CACHED_EXECUTION_RESULTS_TXT, len(self.execution_results)))
        all_params.append(_describe_persistent_characteristic(
            EXECUTION_QUEUE_SIZE_TXT, len(self.execution_requests)))

        result = pd.concat(all_params)
        result.reset_index(drop=True, inplace=True)
        return result

    def _clear(self):
        self.execution_results = None
        self.execution_requests = None
        super()._clear()


class PureFn(ProtectedFn):

    def __init__(self, fn: Callable | str
                 , guards: list[AutonomousFn] | List[Callable] | None = None
                 , validators: list[AutonomousFn] | List[Callable] | None = None
                 , excessive_logging: bool = False
                 , fixed_kwargs: dict | None = None
                 , portal: PureCodePortal | None = None):
        ProtectedFn.__init__(self
            ,fn=fn
            , portal = portal
            , fixed_kwargs=fixed_kwargs
            , excessive_logging = excessive_logging
            , guards=guards
            , validators=validators)


    def get_address(self, **kwargs) -> PureFnExecutionResultAddr:
        """Get the address of the result of the function with the given arguments."""
        with self.finally_bound_portal as portal:
            packed_kwargs = KwArgs(**kwargs).pack(portal)
            return PureFnExecutionResultAddr(self, packed_kwargs)


    def swarm(self, **kwargs) -> PureFnExecutionResultAddr:
        """ Request execution of the function with the given arguments.

        The function is executed in the background. The result can be
        retrieved later using the returned address.
        """
        with self.finally_bound_portal:
            result_address = self.get_address(**kwargs)
            result_address.request_execution()
            return result_address

    def run(self, **kwargs) -> PureFnExecutionResultAddr:
        """ Execute the function with the given arguments.

        The function is executed immediately. The result can be
        retrieved later using the returned address.
        """
        with self.finally_bound_portal:
            result_address = self.get_address(**kwargs)
            result_address.execute()
            return result_address


    def execute(self, **kwargs) -> Any:
        """ Execute the function with the given arguments.

        The function is executed immediately and the result is returned.
        The result is memoized, so the function is actually executed
        only the first time it's called; subsequent calls return the
        cached result.
        """

        with self.finally_bound_portal as portal:
            packed_kwargs = KwArgs(**kwargs).pack(portal)
            output_address = PureFnExecutionResultAddr(self, packed_kwargs)
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
            result_addr = ValueAddr(result, portal=portal)
            try:
                if conduct_consistency_checks:
                    portal.execution_results._p_consistency_checks = 1
                portal.execution_results[output_address] = result_addr
            finally:
                portal.execution_results._p_consistency_checks = (
                    p_consistency_checks)
            output_address.drop_execution_request()
            return result

    def swarm_list(
            self
            , list_of_kwargs:list[dict]
            ) -> list[PureFnExecutionResultAddr]:
        assert isinstance(list_of_kwargs, (list, tuple))
        for kwargs in list_of_kwargs:
            assert isinstance(kwargs, dict)
        with self.finally_bound_portal:
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
        with self.finally_bound_portal:
            addrs = self.swarm_list(list_of_kwargs)
            addrs_workspace = copy(addrs)
            self.portal.entropy_infuser.shuffle(addrs_workspace)
            for an_addr in addrs_workspace:
                an_addr.execute()
        return addrs

    def swarm_grid(
            self
            , grid_of_kwargs:dict[str, list] # refactor
            ) -> list[PureFnExecutionResultAddr]:
        with self.portal:
            param_list = list(ParameterGrid(grid_of_kwargs))
            addrs = self.swarm_list(param_list)
            return addrs

    def run_grid(
            self
            , grid_of_kwargs:dict[str, list] # refactor
            ) -> list[PureFnExecutionResultAddr]:
        with self.finally_bound_portal:
            param_list = list(ParameterGrid(grid_of_kwargs))
            addrs = self.run_list(param_list)
            return addrs


class PureFnExecutionResultAddr(HashAddr):
    """An address of the result of an execution of a pure function.

    This class is used to point to the result of an execution of a pure
    function in a portal. The address is used to request an execution and
    to retrieve the result (if available) from the portal.

    The address also provides access to various logs and records of the
    function execution, such as environmental contexts of the execution attempts,
    outputs printed, exceptions thrown and events emitted.
    """
    _fn_cache: PureFn | None
    _call_signature_cache: LoggingFnCallSignature | None
    _kwargs_cache: KwArgs | None

    _result_cache: Any | None
    _ready_cache: bool | None

    def __init__(self, fn: PureFn, arguments:dict[str, Any]):
        assert isinstance(fn, PureFn)
        with fn.finally_bound_portal as portal:
            self._kwargs_cache = KwArgs(**arguments)
            signature = LoggingFnCallSignature(fn, self._kwargs_cache)
            self._call_signature_cache = signature
            tmp = ValueAddr(signature, portal)
            new_prefix = fn.name +"_result_addr"
            new_hash_signature = tmp.hash_signature
            super().__init__(new_prefix, new_hash_signature, portal=fn.portal)
            self._fn_cache = fn


    def _invalidate_cache(self):
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



    def get_ValueAddr(self):
        with self.portal as portal:
            # prefix = self.fn.name.lower() + "_"
            # prefix += LoggingFnCallSignature.__name__.lower()
            prefix = self.prefix.removesuffix("_result_addr")
            prefix += "_" + LoggingFnCallSignature.__name__.lower()
            return ValueAddr.from_strings(  # TODO: refactor this
                prefix = prefix
                , hash_signature=self.hash_signature
                , portal= portal)


    @property
    def call_signature(self) -> LoggingFnCallSignature:
        if not hasattr(self, "_call_signature_cache") or self._call_signature_cache is None:
            with self.finally_bound_portal:
                self._call_signature_cache = self.get_ValueAddr().get()
        return self._call_signature_cache


    @property
    def fn(self) -> PureFn:
        """Return the function object referenced by the address."""
        if not hasattr(self, "_fn_cache") or self._fn_cache is None:
            with self.finally_bound_portal:
                self._fn_cache = self.call_signature.fn
        return self._fn_cache


    @property
    def kwargs(self) -> KwArgs:
        """Unpacked arguments of the function call, referenced by the address."""
        if not hasattr(self, "_kwargs_cache") or self._kwargs_cache is None:
            with self.finally_bound_portal:
                self._kwargs_cache = self.call_signature.kwargs_addr.get().unpack()
        return self._kwargs_cache


    def __setstate__(self, state):
        self._invalidate_cache()
        self.strings = state["strings"]


    def __getstate__(self):
        state = dict(strings=self.strings)
        return state


    @property
    def _ready_in_current_portal(self):
        """Indicates if the result of the function call is available."""
        if hasattr(self, "_ready_cache"):
            return True
        with self.finally_bound_portal as portal:
            result = (self in portal.execution_results)
            if result:
                self._ready_cache = True
            return result

    @property
    def _ready_in_noncurrent_portals(self) -> bool:
        for portal in _noncurrent_portals():
            with portal:
                if self in portal.execution_results:
                    addr = portal.execution_results[self]
                    data = portal.value_store[addr]
                    with self.portal:
                        self.portal.execution_results[self] = ValueAddr(
                            data, portal=portal)
                        _ = self.fn # needed for cross-portal sync
                        _ = self.kwargs # needed for cross-portal sync
                        # TODO: refactor ( implement self._function_ready ? )
                        # TODO: ( implement self._kwargs_ready ? )

                    self._ready_cache = True
                    return True
        return False

    @property
    def ready(self) -> bool:
        if hasattr(self, "_ready_cache"):
            assert self._ready_cache
            return True
        if self._ready_in_current_portal:
            self._ready_cache = True
            return True
        if self._ready_in_noncurrent_portals:
            self._ready_cache = True
            return True
        return False

    def execute(self):
        """Execute the function and store the result in the portal."""
        if hasattr(self, "_result_cache"):
            return self._result_cache
        with self.finally_bound_portal:
            self._result_cache = self.fn.execute(**self.kwargs)
            return self._result_cache


    def request_execution(self):
        """Request execution of the function, without actually executing it."""
        with self.finally_bound_portal as portal:
            if self.ready:
                self.drop_execution_request()
            else:
                if self not in portal.execution_requests:
                    portal.execution_requests[self] = True


    def drop_execution_request(self):
        """Remove the request for execution of the function."""
        with self.finally_bound_portal as portal:
            portal.execution_requests.delete_if_exists(self)


    @property
    def execution_requested(self):
        """Indicates if the function execution has been requested."""
        with self.finally_bound_portal as portal:
            return self in portal.execution_requests


    def get(self, timeout: int = None):
        """Retrieve value, referenced by the address.

        If the value is not immediately available, backoff exponentially
        till timeout is exceeded. If timeout is None, keep trying forever.

        This method does not actually execute the function, but simply
        retrieves the result of the function execution, if it is available.
        If it is not available, the method waits for the result to become
        available, or until the timeout is exceeded.
        """
        assert timeout is None or timeout >= 0
        if hasattr(self, "_result_cache"):
            return self._result_cache

        with self.finally_bound_portal as portal:

            if self.ready:
                result_addr = portal.execution_results[self]
                self._result_cache = portal.value_store[result_addr]
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
                    result_addr = portal.execution_results[self]
                    self._result_cache = portal.value_store[result_addr]
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
    def can_be_executed(self) -> bool:
        """Indicates if the function can be executed in the current session.

        The function should fe refactored once we start fully supporting
        guards
        """
        with self.finally_bound_portal:
            return self.fn.can_be_executed(self.kwargs)


    @property
    def needs_execution(self) -> bool:
        """Indicates if the function is a good candidate for execution.

        Returns False if the result is already available, or if some other
        process is currently working on it. Otherwise, returns True.
        """
        DEFAULT_EXECUTION_TIME = 10 #TODO: move to portal config
        MAX_EXECUTION_ATTEMPTS = 5
        # TODO: these should not be constants
        if self.ready:
            return False
        with self.finally_bound_portal:
            past_attempts = self.call_signature.execution_attempts
            n_past_attempts = len(past_attempts)
            if n_past_attempts == 0:
                return True
            if n_past_attempts > MAX_EXECUTION_ATTEMPTS:
                #TODO: log this event. Should we have DLQ?
                return False
            most_recent_timestamp = max(
                past_attempts.timestamp(a) for a in past_attempts)
            current_timestamp = time.time()
            if (current_timestamp - most_recent_timestamp
                    > DEFAULT_EXECUTION_TIME*(2**n_past_attempts)):
                return True
            return False