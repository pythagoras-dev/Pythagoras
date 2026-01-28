import pytest

from pythagoras._210_basic_portals.portal_tester import _PortalTester
from pythagoras._350_protected_code_portals import *

def dummy_good_guard(packed_kwargs, fn_addr):
    return pth.VALIDATION_SUCCESSFUL

def dummy_bad_guard(packed_kwargs, fn_addr):
    return True

def guard_returns_false(packed_kwargs, fn_addr):
    return False

def guard_returns_one(packed_kwargs, fn_addr):
    return 1

def guard_returns_string(packed_kwargs, fn_addr):
    return "success"

def f(a, b):
    return a + b


def test_load_save_protected_no_guards_no_validators(tmpdir):
    with _PortalTester(ProtectedCodePortal, root_dict=tmpdir):
        f_1 = ProtectedFn(f)
        f_address = ValueAddr(f_1)
        f_2 = f_address.get()
        assert f_2(a=1, b=2) == f(a=1, b=2) == 3
        assert f_2.name == f_1.name
        assert f_2.source_code == f_1.source_code
        f_address._invalidate_cache()

    with _PortalTester(ProtectedCodePortal, root_dict=tmpdir):
        f_3 = f_address.get()
        assert f_3(a=1, b=2) == f(a=1, b=2) == 3


def test_load_save_protected_dummy_good_guard(tmpdir):
    for guards in [dummy_good_guard, [dummy_good_guard], [[[dummy_good_guard]]]
            , [dummy_good_guard, dummy_good_guard]]:

        with _PortalTester(ProtectedCodePortal, root_dict=tmpdir):
            f_1 = ProtectedFn(f, pre_validators= guards)
            assert len(f_1.pre_validators) == 1
            f_address = ValueAddr(f_1)
            f_2 = f_address.get()
            assert f_2(a=1, b=2) == f(a=1, b=2) == 3
            assert f_2.name == f_1.name
            assert f_2.source_code == f_1.source_code
            f_address._invalidate_cache()

        with _PortalTester(ProtectedCodePortal, root_dict=tmpdir):
            f_3 = f_address.get()
            assert len(f_3.pre_validators) == 1
            assert f_3(a=1, b=2) == f(a=1, b=2) == 3


def test_load_save_protected_dummy_good_guard_autonomous(tmpdir):

    with _PortalTester(ProtectedCodePortal, root_dict=tmpdir):

        dummy_good_guard_autonomous = autonomous()(dummy_good_guard)
        guards = [dummy_good_guard_autonomous, dummy_good_guard_autonomous]

        f_1 = ProtectedFn(f, pre_validators= guards)
        assert len(f_1.pre_validators) == 1
        f_address = ValueAddr(f_1)
        f_2 = f_address.get()
        assert f_2(a=1, b=2) == f(a=1, b=2) == 3
        assert f_2.name == f_1.name
        assert f_2.source_code == f_1.source_code
        f_address._invalidate_cache()

    with _PortalTester(ProtectedCodePortal, root_dict=tmpdir):
        f_3 = f_address.get()
        assert len(f_3.pre_validators) == 1
        assert f_3(a=1, b=2) == f(a=1, b=2) == 3


def test_load_save_protected_dummy_bad_guard(tmpdir):
    for guards in [dummy_bad_guard, [[dummy_good_guard], [dummy_bad_guard]]
        ,[dummy_bad_guard, dummy_good_guard]]:
        with _PortalTester(ProtectedCodePortal, root_dict=tmpdir):
            f_1 = ProtectedFn(f, pre_validators= guards)
            f_address = ValueAddr(f_1)
            f_2 = f_address.get()
            with pytest.raises(Exception):
                f_1(a=1, b=2)
            with pytest.raises(Exception):
                f_2(a=1, b=2)
            assert f_2.name == f_1.name
            assert f_2.source_code == f_1.source_code
            f_address._invalidate_cache()

        with _PortalTester(ProtectedCodePortal, root_dict=tmpdir):
            f_3 = f_address.get()
            with pytest.raises(Exception):
                f_3(a=1, b=2)


def test_load_save_protected_dummy_bad_guard_autonomous(tmpdir):

    with _PortalTester(ProtectedCodePortal, root_dict=tmpdir):
        dummy_bad_guard_autonomous = autonomous()(dummy_bad_guard)
        guards = [dummy_bad_guard_autonomous, dummy_bad_guard_autonomous]

        f_1 = ProtectedFn(f, pre_validators= guards)
        f_address = ValueAddr(f_1)
        f_2 = f_address.get()
        with pytest.raises(Exception):
            f_1(a=1, b=2)
        with pytest.raises(Exception):
            f_2(a=1, b=2)
        assert f_2.name == f_1.name
        assert f_2.source_code == f_1.source_code
        f_address._invalidate_cache()

    with _PortalTester(ProtectedCodePortal, root_dict=tmpdir):
        f_3 = f_address.get()
        with pytest.raises(Exception):
            f_3(a=1, b=2)


def test_validator_return_values_treated_as_failure(tmpdir):
    """
    Test that truthy values other than VALIDATION_SUCCESSFUL are treated as
    validation failure.

    This is intentional design: validators must return VALIDATION_SUCCESSFUL
    (the sentinel singleton) to pass, or None to fail. Returning True, False,
    1, 0, strings, or any other value is treated as failure because the check
    uses identity comparison (``is VALIDATION_SUCCESSFUL``), not truthiness.

    This test explicitly documents this behavior to prevent confusion, as many
    developers naturally expect validators to return boolean True/False.
    """
    with _PortalTester(ProtectedCodePortal, root_dict=tmpdir):
        # Test that returning True is treated as failure
        f_true = ProtectedFn(f, pre_validators=[guard_returns_false])
        with pytest.raises(Exception):
            f_true(a=1, b=2)

        # Test that returning False is treated as failure
        f_false = ProtectedFn(f, pre_validators=[guard_returns_false])
        with pytest.raises(Exception):
            f_false(a=1, b=2)

        # Test that returning 1 (truthy) is treated as failure
        f_one = ProtectedFn(f, pre_validators=[guard_returns_one])
        with pytest.raises(Exception):
            f_one(a=1, b=2)

        # Test that returning a string is treated as failure
        f_string = ProtectedFn(f, pre_validators=[guard_returns_string])
        with pytest.raises(Exception):
            f_string(a=1, b=2)

        # Confirm that VALIDATION_SUCCESSFUL works correctly
        f_good = ProtectedFn(f, pre_validators=[dummy_good_guard])
        assert f_good(a=1, b=2) == 3
