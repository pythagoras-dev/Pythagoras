import pytest
import pythagoras as pth
from pythagoras._210_basic_portals.portal_tester import _PortalTester
from pythagoras._360_pure_code_portals.pure_core_classes import (
    PureCodePortal)

from pythagoras._350_protected_code_portals.package_manager import *


def test_real_package_installation_via_guard(tmpdir):
    with _PortalTester(PureCodePortal, tmpdir):

        try:
            uninstall_package("nothing")
        except Exception:
            pass


        with pytest.raises(ImportError):
            package = importlib.import_module("nothing")
            importlib.reload(package)


        @pth.autonomous()
        def check_nothing(**kwargs):
            try:
                import nothing
            except Exception:
                pth.install_package("nothing")
            import nothing
            assert nothing
            return pth.VALIDATION_SUCCESSFUL


        @pth.pure(pre_validators= [check_nothing])
        def do_something():
            return 10

        assert do_something() == 10

        try:
            uninstall_package("nothing")
        except Exception:
            pass

        with pytest.raises(ImportError):
            package = importlib.import_module("nothing")
            importlib.reload(package)



def test_fake_package_installation_via_guard(tmpdir):
    # tmpdir = "FAKE_PACKAGE_INSTALLATION_VIA_GUARD_"+str(int(time.time()))
    with _PortalTester(PureCodePortal, tmpdir):

        try:
            uninstall_package("p1q9m2x8d3h8r56TTT")
        except Exception:
            pass


        @pth.autonomous()
        def check_nonexisting(**kwargs):
            try:
                import p1q9m2x8d3h8r56TTT
            except Exception:
                pth.install_package("p1q9m2x8d3h8r56TTT")
            import p1q9m2x8d3h8r56TTT
            _ = p1q9m2x8d3h8r56TTT
            return pth.VALIDATION_SUCCESSFUL


        @pth.pure(pre_validators= [check_nonexisting])
        def do_weird_thing():
            return 10


        with pytest.raises(Exception):
            do_weird_thing()

        try:
            uninstall_package("p1q9m2x8d3h8r56TTT")
        except Exception:
            pass
