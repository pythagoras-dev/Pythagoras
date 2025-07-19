from pythagoras import _PortalTester, PureCodePortal
from pythagoras.core import *

@pure(pre_validators=[recursive_parameter("n")])
def factorial(n:int) -> int:
    print(f"{n=}")
    if n in [0, 1]:
        return 1
    else:
        return n * factorial(n=n-1)


def test_pure_factorial_large(tmpdir):
    # tmpdir = "TEST_PURE_FACTORIAL_LARGE"
    with _PortalTester(PureCodePortal
            , tmpdir) as t:

        assert factorial(n=6) == 720

