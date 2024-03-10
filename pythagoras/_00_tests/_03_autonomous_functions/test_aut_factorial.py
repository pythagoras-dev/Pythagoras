
from pythagoras._03_autonomous_functions.autonomous_decorators import autonomous
from pythagoras._07_mission_control.global_state_management import (
    _clean_global_state, initialize, _force_initialize)


def factorial(n:int) -> int:
    if n in [0, 1]:
        return 1
    else:
        return n * factorial(n=n-1)

def test_aut_factorial(tmpdir):
    with _force_initialize(base_dir=tmpdir,n_background_workers=0):
        global factorial
        factorial = autonomous()(factorial)
        assert factorial(n=5) == 120