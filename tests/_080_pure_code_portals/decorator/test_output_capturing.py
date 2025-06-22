from src.pythagoras._010_basic_portals.portal_tester import _PortalTester
from src.pythagoras._080_pure_code_portals.pure_core_classes import (
    PureCodePortal)
from src.pythagoras._080_pure_code_portals.pure_decorator import pure


def test_print_excessive_logging(tmpdir):
    with _PortalTester(PureCodePortal, tmpdir) as t:

        @pure(excessive_logging=True)
        def f(n:int):
            print(f"<{n}>")

        for i in range(1,7):
            f(n=i)
            f(n=i)
            assert (len(t.portal._run_history.txt) == i)

def test_print_no_logging(tmpdir):
    with _PortalTester(PureCodePortal, tmpdir) as t:

        @pure(excessive_logging=False)
        def f(n:int):
            print(f"<{n}>")

        for i in range(1,7):
            f(n=i)
            f(n=i)
            assert (len(t.portal._run_history.txt) == 0)