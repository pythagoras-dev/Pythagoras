import pytest

from pythagoras.___04_idempotent_functions.idempotent_decorator import idempotent
from pythagoras.___04_idempotent_functions.idempotent_func_address_context import (
    IdempotentFnExecutionResultAddr)
from pythagoras.___07_mission_control.global_state_management import (
    _force_initialize)


def factorial(n:int) -> int:
    if n in [0, 1]:
        return 1
    else:
        return n * factorial(n=n-1)

def test_idp_factorial(tmpdir):
    with _force_initialize(base_dir=tmpdir,n_background_workers=0):

        global factorial
        factorial = idempotent()(factorial)

        addr_5 = IdempotentFnExecutionResultAddr(a_fn=factorial, arguments=dict(n=5))

        with pytest.raises(TimeoutError):
            addr_5.get(timeout=2)

        function = addr_5.function
        arguments = addr_5.arguments
        name = addr_5.fn_name
        assert name == "factorial"
        assert function(**arguments) == 120



