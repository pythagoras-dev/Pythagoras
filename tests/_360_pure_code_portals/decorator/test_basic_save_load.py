from pythagoras._220_data_portals import ValueAddr
from pythagoras._210_basic_portals.portal_tester import _PortalTester
from pythagoras._360_pure_code_portals.pure_core_classes import (
    PureCodePortal)
from pythagoras._360_pure_code_portals.pure_decorator import pure


def my_function():
    return 2024

def test_basic_save_load_pure_decorator_fn(tmpdir):
    # tmpdir = "BASICS_PURE_DECORATOR_FN_"*2+ str(int(time.time()))
    with _PortalTester(PureCodePortal, tmpdir) as t:

        global my_function

        my_function = pure()(my_function)

        assert len(t.portal._execution_results) == 0
        assert my_function() == 2024
        assert len(t.portal._execution_results) == 1

        address = None

        assert len(t.portal.global_value_store) == 4

        for i in range(3):
            address = ValueAddr(my_function)
        for i in range(3):
            assert address.get()() == 2024

        assert len(t.portal.global_value_store) == 4
        assert len(t.portal._execution_results) == 1