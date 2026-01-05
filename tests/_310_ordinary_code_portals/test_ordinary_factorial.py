from pythagoras._210_basic_portals.portal_tester import _PortalTester
from pythagoras._310_ordinary_code_portals import OrdinaryCodePortal, ordinary


def factorial(n:int) -> int:
    if n in [0, 1]:
        return 1
    else:
        return n * factorial(n=n-1)

def test_ordinary_factorial(tmpdir):
    with _PortalTester(OrdinaryCodePortal
            , root_dict=tmpdir):
        global factorial
        factorial = ordinary()(factorial)
        assert factorial(n=5) == 120