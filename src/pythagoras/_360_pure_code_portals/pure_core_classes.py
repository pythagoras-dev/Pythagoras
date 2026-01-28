"""Core classes for pure function execution and result caching.

This module provides the infrastructure for pure functions: protected functions
with no side effects that always return the same result for identical arguments.

Classes:
- PureCodePortal: Portal managing execution and persistent caching for pure functions
- PureFn: Wrapped pure function supporting sync/async execution and result memoization
- PureFnCallSignature: Signature identifying a specific call with its arguments
- PureFnExecutionResultAddr: Address for retrieving results in distributed execution

When a pure function is called multiple times with the same arguments, only the
first invocation executes; subsequent calls return the cached result. Pythagoras
tracks source code changes: when the implementation changes, execution occurs
again on the next call, but previously cached results remain available for the
old version. Only source code changes in the function and its pre/post validators
are tracked, not dependencies or environment.
"""

from __future__ import annotations

import time

from typing import Callable, Any, Final


from persidict import WriteOnceDict

from .._210_basic_portals import *
from .._210_basic_portals.basic_portal_core_classes import (
    _describe_persistent_characteristic)

from .._220_data_portals import HashAddr, ValueAddr

from .._350_protected_code_portals import *
from .._110_supporting_utilities import get_long_infoname

def get_noncurrent_pure_portals() -> list[PureCodePortal]:
    """Get all known PureCodePortals except the currentl one.

    Returns:
        List of all known pure portal instances excluding the current portal.

    Raises:
        TypeError: If any non-current portal is not a PureCodePortal instance.
    """
    return get_noncurrent_portals(PureCodePortal)


_CACHED_EXECUTION_RESULTS_TXT: Final[str] = "Cached execution results"
_EXECUTION_QUEUE_SIZE_TXT: Final[str] = "Execution queue size"

class PureCodePortal(ProtectedCodePortal):
    """Portal managing execution and persistent caching for pure functions.

    Extends ProtectedCodePortal with two persistent dictionaries for distributed
    coordination:
    - execution_results: Append-only cache of HashAddr for function outputs
    - execution_requests: Mutable queue tracking pending execution requests
    """

    _execution_results: PersiDict | None
    _execution_requests: PersiDict | None

    def __init__(self
            , root_dict: PersiDict | str | None = None
            , excessive_logging: bool | Joker = KEEP_CURRENT
            ):
        """Initialize a PureCodePortal instance.

        Args:
            root_dict: Backing persistent dictionary or filesystem path.
            excessive_logging: Enable verbose logging, or KEEP_CURRENT to inherit.
        """
        ProtectedCodePortal.__init__(self
            , root_dict=root_dict
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


    def __post_init__(self) -> None:
        """Finalize initialization after all __init__ methods complete."""
        super().__post_init__()


    def describe(self) -> pd.DataFrame:
        """Describe the portal state as a DataFrame.

        Returns:
            DataFrame containing base portal parameters, cached result count,
            and queued execution request count.
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
        """Release backing dictionary references and clear base portal state.

        Warning:
            Portal becomes unusable after calling this method.
        """
        self._execution_results = None
        self._execution_requests = None
        super()._clear()


class PureFnCallSignature(ProtectedFnCallSignature):
    """Signature identifying a specific call to a pure function.

    Combines the function identity with its argument values to create
    a unique key for result caching and retrieval.
    """

    def __init__(self, fn: PureFn, arguments: dict):
        """Create a call signature for a PureFn invocation.

        Args:
            fn: Pure function being invoked.
            arguments: Keyword arguments passed to the function.
        """
        if not isinstance(fn, PureFn):
            raise TypeError(f"fn must be a PureFn instance, got {get_long_infoname(fn)}")
        if not isinstance(arguments, dict):
            raise TypeError(f"arguments must be a dict, got {get_long_infoname(arguments)}")
        super().__init__(fn, arguments)

    @cached_property
    def fn(self) -> PureFn:
        """Pure function referenced by this signature."""
        return super().fn

    @cached_property
    def execution_results_addr(self) -> PureFnExecutionResultAddr:
        """Address where execution results are stored."""
        return PureFnExecutionResultAddr(self.fn, self.packed_kwargs)


class PureFn(ProtectedFn):
    """Callable wrapper providing pure-function semantics with result caching.

    Executes within a PureCodePortal, persistently caches results indexed by
    call signature, and provides APIs for synchronous execution, background
    requests, and address-based retrieval.
    """

    def __init__(self, fn: Callable | str
                 , pre_validators: list[AutonomousFn] | list[Callable] | None = None
                 , post_validators: list[AutonomousFn] | list[Callable] | None = None
                 , excessive_logging: bool | Joker | ReuseFlag = KEEP_CURRENT
                 , fixed_kwargs: dict | None = None
                 , portal: PureCodePortal | None |ReuseFlag = None):
        """Construct a PureFn wrapper.

        Args:
            fn: Target callable to wrap.
            pre_validators: Optional validators run before execution.
            post_validators: Optional validators run after execution.
            excessive_logging: Controls verbose logging behavior. Can be:

                - True/False to explicitly enable/disable
                - KEEP_CURRENT to inherit from context
                - USE_FROM_OTHER to copy the setting from ``fn`` when ``fn``
                  is an existing PureFn

            fixed_kwargs: Argument name-value pairs injected into every call.
            portal: Portal for caching and execution. Can be:

                - A PureCodePortal instance to link directly
                - USE_FROM_OTHER to inherit the portal from ``fn`` when ``fn``
                  is an existing PureFn
                - None to infer a suitable portal when the function is executed
        """
        super().__init__(fn=fn
                         , portal = portal
                         , fixed_kwargs=fixed_kwargs
                         , excessive_logging = excessive_logging
                         , pre_validators=pre_validators
                         , post_validators=post_validators)


    def get_address(self, **kwargs) -> PureFnExecutionResultAddr:
        """Build an address for the result of a call with the given arguments.

        Args:
            **kwargs: Keyword arguments for the function call.

        Returns:
            Address referencing the result (cached or pending) for these arguments.
        """
        with self.portal:
            packed_kwargs = KwArgs(**kwargs).pack()
            return PureFnExecutionResultAddr(self, packed_kwargs)


    def get_signature(self, arguments: dict) -> PureFnCallSignature:
        """Build a call signature for the given arguments.

        Args:
            arguments: Keyword arguments for the function call.

        Returns:
            Signature object uniquely identifying this call.
        """
        return PureFnCallSignature(self, arguments)


    def swarm(self, **kwargs) -> PureFnExecutionResultAddr:
        """Request background execution without blocking.

        Records an execution request in the portal for external workers to process.
        The function does not execute immediately.

        Args:
            **kwargs: Keyword arguments for the function call.

        Returns:
            Address identifying the pending or cached result.
        """
        with self.portal:
            result_address = self.get_address(**kwargs)
            result_address.request_execution()
            return result_address

    def run(self, **kwargs) -> PureFnExecutionResultAddr:
        """Execute synchronously and return the result address.

        Args:
            **kwargs: Keyword arguments for the function call.

        Returns:
            Address of the computed result.
        """
        with self.portal:
            result_address = self.get_address(**kwargs)
            result_address.execute()
            return result_address


    def execute(self, **kwargs) -> Any:
        """Execute the function and return the result value.

        Returns the cached result if available, otherwise executes and caches.

        Args:
            **kwargs: Keyword arguments for the function call.

        Returns:
            The computed or cached result value.
        """

        with self.portal as portal:
            packed_kwargs = KwArgs(**kwargs).pack()
            output_address = PureFnExecutionResultAddr(
                fn=self, arguments=packed_kwargs)
            if output_address.ready:
                return output_address.get()
            output_address.request_execution()
            unpacked_kwargs = KwArgs(**packed_kwargs).unpack()
            result = super().execute(**unpacked_kwargs)
            result_addr = ValueAddr(result)
            portal._execution_results[output_address] = result_addr
            output_address.drop_execution_request()
            return result


    def swarm_list(
            self
            , list_of_kwargs:list[dict]
            ) -> list[PureFnExecutionResultAddr]:
        """Queue background execution for multiple argument sets.

        Args:
            list_of_kwargs: List of keyword-argument dicts, one per call.

        Returns:
            Result addresses in the same order as input.
        """
        if not isinstance(list_of_kwargs, (list, tuple)):
            raise TypeError(f"list_of_kwargs must be a list or tuple, got {get_long_infoname(list_of_kwargs)}")
        for kwargs in list_of_kwargs:
            if not isinstance(kwargs, dict):
                raise TypeError(f"Each item in list_of_kwargs must be a dict, got {get_long_infoname(kwargs)}")
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
        """Execute multiple calls synchronously in shuffled order.

        Args:
            list_of_kwargs: List of keyword-argument dicts, one per call.

        Returns:
            Result addresses in the same order as input.
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
        """PureCodePortal governing execution and persistence.

        Either the function's linked portal or the current active portal if not explicitly bound.
        """
        return super().portal


class PureFnExecutionResultAddr(HashAddr):
    """Address referencing a pure function execution result (cached or pending).

    Used to request execution, retrieve results, check availability, and access
    execution metadata such as logs, exceptions, and environmental contexts.
    """

    _DESCRIPTOR_SUFFIX:str = "_result_addr"

    _result_cache: Any | None
    _ready_cache: bool | None

    def __init__(self, fn: PureFn, arguments:dict[str, Any]):
        """Create an address for a pure function execution result.

        Args:
            fn: Pure function whose result is addressed.
            arguments: Keyword arguments for the call.
        """
        if not isinstance(fn, PureFn):
            raise TypeError(f"fn must be a PureFn instance, got {get_long_infoname(fn)}")
        with fn.portal:
            kwargs = KwArgs(**arguments)
            signature = PureFnCallSignature(fn, kwargs)
            self._set_cached_properties(call_signature = signature
                    , fn = fn, kwargs = kwargs)
            tmp = ValueAddr(signature)
            new_descriptor = fn.name +self._DESCRIPTOR_SUFFIX
            new_hash_signature = tmp.hash_signature
            super().__init__(new_descriptor, new_hash_signature)


    def _invalidate_cache(self):
        """Invalidate cached attribute values.

        Clears all cached properties.
        """
        if hasattr(self, "_ready_cache"):
            del self._ready_cache
        if hasattr(self, "_result_cache"):
            del self._result_cache
        super()._invalidate_cache()


    def get_ValueAddr(self):
        """Convert this result address to a ValueAddr for the call signature.

        Returns:
            ValueAddr pointing to the PureFnCallSignature that produced this result.
        """
        descriptor = self.descriptor.removesuffix(self._DESCRIPTOR_SUFFIX)
        descriptor += "_" + PureFnCallSignature.__name__.lower()
        return ValueAddr.from_strings(  # TODO: refactor this
            descriptor= descriptor
            , hash_signature=self.hash_signature)


    @cached_property
    def call_signature(self) -> PureFnCallSignature:
        """Call signature for this address."""
        return self.get_ValueAddr().get()


    @cached_property
    def fn(self) -> PureFn:
        """Pure function referenced by this address."""
        return self.call_signature.fn


    @cached_property
    def kwargs(self) -> KwArgs:
        """Unpacked keyword arguments for this call."""
        return self.call_signature.kwargs_addr.get().unpack()


    def __setstate__(self, state):
        """Restore object state during unpickling."""
        self._invalidate_cache()
        self.strings = state["strings"]


    def __getstate__(self):
        """Prepare object state for pickling."""
        state = dict(strings=self.strings)
        return state


    @property
    def _ready_in_current_portal(self):
        """Check if result is available in the current portal."""
        result = (self in get_current_portal()._execution_results)
        if result:
            self._ready_cache = True
        return result

    @property
    def _ready_in_noncurrent_portals(self) -> bool:
        """Import result from other portals if available.

        Searches known non-current portals and copies the result into the
        current portal if found.

        Returns:
            True if the result was found and imported; False otherwise.
        """
        for another_portal in get_noncurrent_pure_portals():
            with another_portal:
                if self in another_portal._execution_results:
                    addr = another_portal._execution_results[self]
                    with self.fn.portal as active_portal:
                        active_portal._execution_results[self] = addr
                        if addr not in active_portal.global_value_store:
                            data = another_portal.global_value_store[addr]
                            self._result_cache = data
                            active_portal.global_value_store[addr] = data
                    return True
        return False

    @property
    def ready(self) -> bool:
        """Whether the execution result is available.

        Returns:
            True if the result exists in current or any known portal; False otherwise.
        """
        if hasattr(self, "_ready_cache"):
            if not self._ready_cache:
                raise RuntimeError(f"Internal inconsistency: _ready_cache is set but False for address {self}")
            return True
        with self.fn.portal:
            if self._ready_in_current_portal:
                self._ready_cache = True
                return True
            if self._ready_in_noncurrent_portals:
                self._ready_cache = True
                return True
        return False


    def execute(self):
        """Execute the function and store the result.

        Returns:
            The computed result value.
        """
        if hasattr(self, "_result_cache"):
            return self._result_cache
        with self.fn.portal:
            self._result_cache = self.fn.execute(**self.kwargs)
            return self._result_cache


    def request_execution(self):
        """Request execution without blocking.

        Records a request in the current portal for external workers to process.
        """
        with self.fn.portal as portal:
            if self.ready:
                self.drop_execution_request()
            else:
                portal._execution_requests[self] = True


    def drop_execution_request(self):
        """Remove execution request from all known portals."""
        for portal in get_known_portals():
            with portal:
                portal._execution_requests.delete_if_exists(self)


    @property
    def execution_requested(self):
        """Whether execution has been requested.

        Checks the current and all known portals, synchronizing requests
        into the current portal if found elsewhere.

        Returns:
            True if a pending execution request exists; False otherwise.
        """
        with self.fn.portal as current_portal:
            if self in current_portal._execution_requests:
                return True
            for another_portal in get_noncurrent_pure_portals():
                if self in another_portal._execution_requests:
                    current_portal._execution_requests[self] = True
                    # TODO: Review how timestamps should work here
                    return True
        return False


    def get(self, timeout: int = None):
        """Retrieve the result value, waiting with exponential backoff if needed.

        Does not execute the function directly; requests execution and waits
        for an external worker to compute the result.

        Args:
            timeout: Maximum wait time in seconds, or None to wait indefinitely.

        Returns:
            The computed result value.

        Raises:
            TimeoutError: If timeout expires before result becomes available.
        """
        if timeout is not None and timeout < 0:
            raise ValueError(f"timeout must be None or non-negative, got {timeout}")
        if hasattr(self, "_result_cache"):
            return self._result_cache

        with self.fn.portal as portal:

            if self.ready:
                result_addr = portal._execution_results[self]
                self._result_cache = portal.global_value_store[result_addr]
                return self._result_cache

            self.request_execution()

            start_time, backoff_period = time.time(), 1.0
            if timeout is not None:
                stop_time = start_time + timeout
            else:
                stop_time = None
            # Times are in seconds; backoff uses exponential growth with jitter

            while True:
                if self.ready:
                    result_addr = portal._execution_results[self]
                    self._result_cache = portal.global_value_store[result_addr]
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
        """Whether execution can proceed.

        Checks pre-validators and returns execution readiness status.

        Returns:
            VALIDATION_SUCCESSFUL if ready; a dependent call signature if waiting
            on another execution; None if execution is not possible.
        """
        with self.fn.portal:
            return self.fn.can_be_executed(self.kwargs)


    @property
    def needs_execution(self) -> bool:
        """Whether this call is a good candidate for execution.

        Returns False if the result is cached, another worker is processing it,
        or too many attempts have failed. Uses exponential backoff to avoid
        repeatedly executing failing calls.

        Returns:
            True if execution should be attempted; False otherwise.
        """
        _DEFAULT_EXECUTION_TIME = 10  # TODO: move to portal config
        _MAX_EXECUTION_ATTEMPTS = 5   # TODO: move to portal config

        if self.ready:
            return False
        with self.fn.portal:
            past_attempts = self.call_signature.execution_attempts
            n_past_attempts = len(past_attempts)
            if n_past_attempts == 0:
                return True
            if n_past_attempts > _MAX_EXECUTION_ATTEMPTS:
                # TODO: log this event. Should we have a dead-letter queue?
                return False
            most_recent_timestamp = max(
                past_attempts.timestamp(a) for a in past_attempts)
            current_timestamp = time.time()
            if (current_timestamp - most_recent_timestamp
                    > _DEFAULT_EXECUTION_TIME*(2**n_past_attempts)):
                return True
            return False