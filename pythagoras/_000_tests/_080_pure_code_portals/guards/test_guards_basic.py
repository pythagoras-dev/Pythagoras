import pytest, time
import pythagoras as pth
from pythagoras import BasicPortal
from pythagoras._010_basic_portals.portal_tester import _PortalTester
from pythagoras._080_pure_code_portals.pure_core_classes import (
    PureCodePortal)
from pythagoras._080_pure_code_portals.pure_decorator import pure


def test_basic_execution(tmpdir):
    # tmpdir = 25 * "Q" + str(int(time.time()))
    with _PortalTester(PureCodePortal, tmpdir):
        @pth.autonomous()
        def do_nothing(**kwargs):
            return pth.OK

        @pth.pure(guards = [do_nothing])
        def do_nothing_pure():
            return 10


        assert do_nothing_pure() == 10


def test_basic_exception(tmpdir):
    # tmpdir = 25 * "Q" + str(int(time.time()))
    with _PortalTester(PureCodePortal, tmpdir):
        @pth.autonomous()
        def no_go(**kwargs):
            return "some message"

        @pth.pure(guards = [no_go])
        def do_nothing_pure():
            return 10

        with pytest.raises(Exception):
            do_nothing_pure()


