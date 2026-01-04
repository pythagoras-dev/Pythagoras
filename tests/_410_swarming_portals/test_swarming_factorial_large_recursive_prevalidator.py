from pythagoras import _PortalTester, PureCodePortal
from pythagoras.core import *

@pure(pre_validators=[recursive_parameters("n")])
def factorial(n:int) -> int:
    # print(f"{n=}")
    if n in [0, 1]:
        return 1
    else:
        return n * factorial(n=n-1)


def test_swarming_pure_factorial_large(tmpdir):
    # tmpdir = "TEST_PURE_FACTORIAL_LARGE"
    with _PortalTester(SwarmingPortal,tmpdir) as t:
        result_addr = factorial.swarm(n=10)
        assert get(result_addr) == 3628800

        # print(f"{factorial(n=10)=}")
