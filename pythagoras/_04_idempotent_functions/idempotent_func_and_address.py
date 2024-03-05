from __future__ import annotations

import time
from typing import Callable, Any

import pythagoras as pth
from pythagoras import get_random_safe_str

from pythagoras._01_foundational_objects.hash_addresses import HashAddress
from pythagoras._01_foundational_objects.value_addresses import ValueAddress

from pythagoras._03_autonomous_functions.autonomous_funcs import (
    AutonomousFunction, register_autonomous_function)

from pythagoras._02_ordinary_functions.ordinary_funcs import (
    OrdinaryFunction)

from pythagoras._03_autonomous_functions.default_island_singleton import (
    DefaultIslandType, DefaultIsland)

from pythagoras._04_idempotent_functions.kw_args import (
    UnpackedKwArgs, PackedKwArgs, SortedKwArgs)
from pythagoras._04_idempotent_functions.process_augmented_func_src import (
    process_augmented_func_src)
from pythagoras._05_events_and_exceptions.context_utils import build_context


class IdempotentFunction(AutonomousFunction):
    augmented_code_checked: bool
    def __init__(self, a_func: Callable | str | OrdinaryFunction
            , island_name:str | None | DefaultIslandType = DefaultIsland):
        super().__init__(a_func, island_name)
        self.augmented_code_checked = False
        register_idempotent_function(self)

    @property
    def decorator(self) -> str:
        decorator_str = "@pth.idempotent("
        decorator_str += f"island_name='{self.island_name}'"
        decorator_str += ")"
        return decorator_str

    def runtime_checks(self):
        super().runtime_checks()
        island_name = self.island_name
        island = pth.all_autonomous_functions[island_name]

        if not self.augmented_code_checked:
            augmented_code = ""
            for f_name in self.dependencies:
                f = island[f_name]
                augmented_code += f.decorator + "\n"
                augmented_code += f.naked_source_code + "\n"
                augmented_code += "\n"

            name = self.name
            if (not hasattr(island[name], "_augmented_source_code")
                or island[name]._augmented_source_code is None):
                island[name]._augmented_source_code = augmented_code
            else:
                assert island[name]._augmented_source_code == augmented_code

            self.augmented_code_checked = True

        return True


    @property
    def augmented_source_code(self) -> str:
        island_name = self.island_name
        island = pth.all_autonomous_functions[island_name]
        assert hasattr(island[self.name], "_augmented_source_code")
        assert island[self.name]._augmented_source_code is not None
        assert self.augmented_code_checked
        return island[self.name]._augmented_source_code


    def __getstate__(self):
        assert self.runtime_checks()
        draft_state = dict(name=self.name
            , naked_source_code=self.naked_source_code
            , island_name=self.island_name
            , augmented_source_code=self.augmented_source_code
            , class_name=self.__class__.__name__)
        state = dict()
        for key in sorted(draft_state):
            state[key] = draft_state[key]
        return state

    def __setstate__(self, state):
        assert len(state) == 5
        assert state["class_name"] == IdempotentFunction.__name__
        self.name = state["name"]
        self.naked_source_code = state["naked_source_code"]
        self.island_name = state["island_name"]
        self.augmented_code_checked = False
        register_idempotent_function(self)

        island_name = self.island_name
        island = pth.all_autonomous_functions[island_name]
        name = self.name
        if island[name]._augmented_source_code is None:
            island[name]._augmented_source_code = state["augmented_source_code"]
            process_augmented_func_src(state["augmented_source_code"])
        else:
            assert state["augmented_source_code"] == (
                island[name]._augmented_source_code)

        self.augmented_code_checked = True


    def execute(self, **kwargs) -> Any:
        packed_kwargs = PackedKwArgs(**kwargs)
        output_address = FuncOutputAddress(self, packed_kwargs)
        _pth_f_addr_ = output_address
        if output_address.ready:
            return output_address.get()
        output_address.request_execution()
        registration_addr = (output_address[0]
            , output_address[1], get_random_safe_str())
        pth.function_execution_attempts[registration_addr] = build_context()
        unpacked_kwargs = UnpackedKwArgs(**packed_kwargs)
        result = super().execute(**unpacked_kwargs)
        pth.function_output_store[output_address] = ValueAddress(result)
        pth.function_execution_requests.delete_if_exists(output_address)
        return result

    def list_execute(self, list_of_kwargs:list[dict]) -> Any:
        assert isinstance(list_of_kwargs, (list, tuple))
        for kwargs in list_of_kwargs:
            assert isinstance(kwargs, dict)
        addrs = []
        for kwargs in list_of_kwargs:
            new_addr = FuncOutputAddress(self, kwargs)
            new_addr.request_execution()
            addrs.append(new_addr)
        addrs_indexed = list(zip(range(len(addrs)), addrs))
        pth.entropy_infuser.shuffle(addrs_indexed)
        results_dict = dict()
        for n, an_addr in addrs_indexed:
            results_dict[n] = an_addr.function.execute(**an_addr.arguments)
        results_list = [results_dict[n] for n in range(len(addrs))]
        return results_list

    def execution_attempts(self, **kwargs) -> list:
        packed_kwargs = PackedKwArgs(**kwargs)
        output_address = FuncOutputAddress(self, packed_kwargs)
        return output_address.execution_attempts


def register_idempotent_function(f: IdempotentFunction) -> None:
    """Register an idempotent function in the Pythagoras system."""
    assert isinstance(f, IdempotentFunction)
    register_autonomous_function(f)
    island_name = f.island_name
    island = pth.all_autonomous_functions[island_name]
    name = f.name
    if not hasattr(island[name], "_augmented_source_code"):
        island[name]._augmented_source_code = None


class FunctionCallSignature:
    def __init__(self,f:IdempotentFunction,arguments:SortedKwArgs):
        assert isinstance(f, IdempotentFunction)
        assert isinstance(arguments, SortedKwArgs)
        self.f_name = f.name
        self.f_addr = ValueAddress(f)
        self.args_addr = ValueAddress(arguments.pack())

class FuncOutputAddress(HashAddress):
    def __init__(self, f: IdempotentFunction, arguments:dict[str, Any]):
        assert isinstance(f, IdempotentFunction)
        arguments = SortedKwArgs(**arguments)
        signature = FunctionCallSignature(f,arguments)
        tmp = ValueAddress(signature)
        super().__init__(tmp.prefix, tmp.hash_value)

    @property
    def ready(self):
        result =  self in pth.function_output_store
        return result

    def request_execution(self):
        if self in pth.function_output_store:
            if self in pth.function_execution_requests:
                del pth.function_execution_requests[self]
        else:
            if self not in pth.function_execution_requests:
                pth.function_execution_requests[self] = True

    def get(self, timeout: int = None):
        """Retrieve value, referenced by the address.

        If the value is not immediately available, backoff exponentially
        till timeout is exceeded. If timeout is None, keep trying forever.
        """
        if self.ready:
            return pth.global_value_store[pth.function_output_store[self]]
        self.request_execution()

        start_time, backoff_period = time.time(), 1.0
        stop_time = (start_time + timeout) if timeout else None
        # start_time, stop_time and backoff_period are in seconds

        while True:
            if self.ready:
                result = pth.global_value_store[pth.function_output_store[self]]
                pth.function_execution_requests.delete_if_exists(self)
                return result
            else:
                time.sleep(backoff_period)
                backoff_period *= 2.0
                backoff_period += pth.entropy_infuser.uniform(-0.5, 0.5)
                if stop_time:
                    current_time = time.time()
                    if current_time + backoff_period > stop_time:
                        backoff_period = stop_time - current_time
                    if current_time > stop_time:
                        raise TimeoutError
                backoff_period = max(1.0, backoff_period)

    @property
    def function(self) -> IdempotentFunction:
        signature_addr = ValueAddress.from_strings(
            prefix=self.prefix, hash_value=self.hash_value)
        signature = signature_addr.get()
        return signature.f_addr.get()

    @property
    def f_name(self) -> str:
        signature_addr = ValueAddress.from_strings(
            prefix=self.prefix, hash_value=self.hash_value)
        signature = signature_addr.get()
        return signature.f_name

    @property
    def island_name(self) -> str:
        return self.function.island_name

    @property
    def arguments(self) -> SortedKwArgs:
        signature_addr = ValueAddress.from_strings(
            prefix=self.prefix, hash_value=self.hash_value)
        signature = signature_addr.get()
        return signature.args_addr.get()

    @property
    def can_be_executed(self) -> bool:
        """Indicates if the function can be executed in the current session.

        Currently, it's just a placeholder that always returns True.

        The function should fe refactored once we start supporting
        VALIDATORS, CORRECTORS and SEQUENCERS
        """
        return True

    @property
    def needs_execution(self) -> bool:
        """Indicates if the function is a good candidate for execution.

        Returns False if the result is already available, or if some other
        process is currently working on it. Otherwise, returns True.
        """
        DEFAULT_EXECUTION_TIME = 10
        MAX_EXECUTION_ATTEMPTS = 5
        # TODO: these should not be constants
        if self.ready:
            return False
        past_attempts = pth.function_execution_attempts.get_subdict(self)
        n_past_attempts = len(past_attempts)
        if n_past_attempts == 0:
            return True
        if n_past_attempts > MAX_EXECUTION_ATTEMPTS:
            #TODO: log this event. Should we have DLQ?
            return False
        most_recent_timestamp = max(
            past_attempts.mtimestamp(a) for a in past_attempts)
        current_timestamp = time.time()
        if (current_timestamp - most_recent_timestamp
                > DEFAULT_EXECUTION_TIME*(2**n_past_attempts)):
            return True
        return False

    @property
    def execution_attempts(self) -> list:
        attempts = pth.function_execution_attempts.get_subdict(self)
        attemps_timed = {-attempts.mtimestamp(a):attempts[a] for a in attempts}
        times = sorted(attemps_timed)
        result = []
        for t in times:
            result.append(attemps_timed[t])
        return result

