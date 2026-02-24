import pythagoras as pth
from pythagoras._210_basic_portals.portal_tester import _PortalTester
from pythagoras._360_pure_code_portals.pure_core_classes import (
    PureCodePortal)


def test_basic_addr(tmpdir):
    # tmpdir = 25*"Q" + str(int(time.time()))
    addr = None
    with _PortalTester(PureCodePortal, tmpdir):
        @pth.autonomous()
        def do_nothing(**kwargs):
            return pth.NO_OBJECTIONS

        @pth.pure(requirements= [do_nothing])
        def do_nothing_pure():
            return 10

        addr = do_nothing_pure.swarm()

    addr._invalidate_cache()

    with _PortalTester(PureCodePortal, tmpdir):
        del do_nothing_pure
        del do_nothing
        result = addr.execute()
        assert result == 10


def test_alternative_extensions(tmpdir):
    # tmpdir = 25 * "Q" + str(int(time.time()))
    with _PortalTester(PureCodePortal, tmpdir):
        @pth.autonomous()
        def do_something_1(**kwargs):
            return pth.NO_OBJECTIONS

        @pth.autonomous()
        def do_something_2(**kwargs):
            return pth.NO_OBJECTIONS


        def my_beloved_function():
            return 10

        mbl_pure_1 = pth.pure(requirements=[do_something_1])(my_beloved_function)
        mbl_pure_2 = pth.pure(requirements=[do_something_2])(my_beloved_function)

        assert mbl_pure_1() == 10
        assert mbl_pure_2() == 10
