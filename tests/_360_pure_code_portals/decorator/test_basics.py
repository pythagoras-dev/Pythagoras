from pythagoras._210_basic_portals.portal_tester import _PortalTester
from pythagoras._360_pure_code_portals.pure_core_classes import (
    PureCodePortal, PureFn)
from pythagoras._360_pure_code_portals.pure_decorator import pure


def test_basics_pure_decorator(tmpdir):
    # tmpdir = "BASICS_PURE_DECORATOR_"*2+ str(time.time())
    with _PortalTester(PureCodePortal, tmpdir) as t:
        def f_ab(a, b):
            return a + b

        result = f_ab(a=1,b=2)
        f_1 = pure()(f_ab)
        #
        assert isinstance(f_1, PureFn)
        for i in range(3):
            assert f_1(a=1,b=2) == result

        assert len(t.portal._run_history.txt) == 0


def test_basics_pure_decorator_log_everything(tmpdir):
    # tmpdir = "BASICS_PURE_DECORATOR_LOG_EVERYTHING_"*2+ str(time.time())
    with _PortalTester(PureCodePortal, tmpdir) as t:
        def f_ab(a, b):
            return a + b

        result = f_ab(a=1,b=2)
        f_1 = pure(excessive_logging=True)(f_ab)
        #
        assert isinstance(f_1, PureFn)
        for i in range(3):
            assert f_1(a=1,b=2) == result

        assert len(t.portal._run_history.txt) == 1