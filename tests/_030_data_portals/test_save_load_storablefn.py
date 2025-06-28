import pytest

from pythagoras._010_basic_portals.portal_tester import _PortalTester
from pythagoras._030_data_portals import *


def f():
    return 42

@pytest.mark.parametrize("p",[1,0.5,0])
def test_value_address_storablefn(tmpdir,p):
    # tmpdir = 3*"VALUE_ADDRESS_STORABLEFN_" + str(int(time.time())) + "_" + str(p)

    with (_PortalTester(DataPortal,tmpdir, p_consistency_checks=p) as t):
        portal = t.portal
        global f

        f_new = StorableFn(f)

        assert f_new() == 42

        # assert f_new._linked_portal is None

        hash_id = f_new.hash_signature

        f_new_addr =  ValueAddr(f_new)

        f_new_restored = f_new_addr.get()
        assert f_new_restored() == 42

        f_new_addr._invalidate_cache()

        assert f_new_addr.hash_signature == hash_id

        f_new_restored = f_new_addr.get()
        assert f_new_restored() == 42
        # assert f_new_restored._linked_portal is None

        assert id(f_new) != id(f_new_restored)

        assert len(portal._value_store) == 1
        assert portal.get_number_of_linked_functions() == 0
        assert len(portal.get_linked_functions()) == 0

        # f_new.portal = portal
        # assert f_new.portal is f_new_restored.portal
        # # assert f_new._linked_portal is portal
        # assert f_new_restored._linked_portal is portal
        #
        # assert len(portal._value_store) == 1
        # assert portal.get_number_of_linked_functions() == 1
        # assert len(portal.get_linked_functions()) == 1




