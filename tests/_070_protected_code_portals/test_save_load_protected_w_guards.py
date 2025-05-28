import pytest

from src.pythagoras._010_basic_portals.portal_tester import _PortalTester
from src.pythagoras._010_basic_portals.portal_aware_classes import _most_recently_entered_portal
from src.pythagoras._070_protected_code_portals import *

def dummy_good_guard(packed_kwargs, fn_addr):
    return pth.OK

def dummy_bad_guard(packed_kwargs, fn_addr):
    return True

def f(a, b):
    return a + b


def test_load_save_protected_no_guards_no_validators(tmpdir):
    with _PortalTester(ProtectedCodePortal, root_dict=tmpdir) as p:
        f_1 = ProtectedFn(f)
        f_address = ValueAddr(f_1, portal = p.portal)
        f_2 = f_address.get()
        assert f_2(a=1, b=2) == f(a=1, b=2) == 3
        assert f_2.name == f_1.name
        assert f_2.source_code == f_1.source_code
        f_address._invalidate_cache()

    with _PortalTester(ProtectedCodePortal, root_dict=tmpdir):
        del f_address._portal
        f_address._portal = _most_recently_entered_portal()
        f_3 = f_address.get()
        assert f_3(a=1, b=2) == f(a=1, b=2) == 3


def test_load_save_protected_dummy_good_guard(tmpdir):
    for guards in [dummy_good_guard, [dummy_good_guard], [[[dummy_good_guard]]]
            , [dummy_good_guard, dummy_good_guard]]:

        with _PortalTester(ProtectedCodePortal, root_dict=tmpdir) as p:
            f_1 = ProtectedFn(f, guards = guards)
            assert len(f_1.guards) == 1
            f_address = ValueAddr(f_1, portal = p.portal)
            f_2 = f_address.get()
            assert f_2(a=1, b=2) == f(a=1, b=2) == 3
            assert f_2.name == f_1.name
            assert f_2.source_code == f_1.source_code
            f_address._invalidate_cache()

        with _PortalTester(ProtectedCodePortal, root_dict=tmpdir):
            del f_address._portal
            f_address._portal = _most_recently_entered_portal()
            f_3 = f_address.get()
            assert len(f_3.guards) == 1
            assert f_3(a=1, b=2) == f(a=1, b=2) == 3


def test_load_save_protected_dummy_good_guard_autonomous(tmpdir):

    dummy_good_guard_autonomous = autonomous()(dummy_good_guard)
    guards = [dummy_good_guard_autonomous, dummy_good_guard_autonomous]

    with _PortalTester(ProtectedCodePortal, root_dict=tmpdir) as p:
        f_1 = ProtectedFn(f, guards = guards)
        assert len(f_1.guards) == 1
        f_address = ValueAddr(f_1, portal = p.portal)
        f_2 = f_address.get()
        assert f_2(a=1, b=2) == f(a=1, b=2) == 3
        assert f_2.name == f_1.name
        assert f_2.source_code == f_1.source_code
        f_address._invalidate_cache()

    with _PortalTester(ProtectedCodePortal, root_dict=tmpdir):
        del f_address._portal
        f_address._portal = _most_recently_entered_portal()
        f_3 = f_address.get()
        assert len(f_3.guards) == 1
        assert f_3(a=1, b=2) == f(a=1, b=2) == 3


def test_load_save_protected_dummy_bad_guard(tmpdir):
    for guards in [dummy_bad_guard, [[dummy_good_guard], [dummy_bad_guard]]
        ,[dummy_bad_guard, dummy_good_guard]]:
        with _PortalTester(ProtectedCodePortal, root_dict=tmpdir) as p:
            f_1 = ProtectedFn(f, guards = guards)
            f_address = ValueAddr(f_1, portal = p.portal)
            f_2 = f_address.get()
            with pytest.raises(Exception):
                f_1(a=1, b=2)
            with pytest.raises(Exception):
                f_2(a=1, b=2)
            assert f_2.name == f_1.name
            assert f_2.source_code == f_1.source_code
            f_address._invalidate_cache()

        with _PortalTester(ProtectedCodePortal, root_dict=tmpdir):
            del f_address._portal
            f_address._portal = _most_recently_entered_portal()
            f_3 = f_address.get()
            with pytest.raises(Exception):
                f_3(a=1, b=2)


def test_load_save_protected_dummy_bad_guard_autonomous(tmpdir):
    dummy_bad_guard_autonomous = autonomous()(dummy_bad_guard)
    guards = [dummy_bad_guard_autonomous, dummy_bad_guard_autonomous]
    with _PortalTester(ProtectedCodePortal, root_dict=tmpdir) as p:
        f_1 = ProtectedFn(f, guards = guards)
        f_address = ValueAddr(f_1, portal = p.portal)
        f_2 = f_address.get()
        with pytest.raises(Exception):
            f_1(a=1, b=2)
        with pytest.raises(Exception):
            f_2(a=1, b=2)
        assert f_2.name == f_1.name
        assert f_2.source_code == f_1.source_code
        f_address._invalidate_cache()

    with _PortalTester(ProtectedCodePortal, root_dict=tmpdir):
        del f_address._portal
        f_address._portal = _most_recently_entered_portal()
        f_3 = f_address.get()
        with pytest.raises(Exception):
            f_3(a=1, b=2)
