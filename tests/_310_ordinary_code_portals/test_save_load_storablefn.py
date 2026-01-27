
from pythagoras._210_basic_portals.portal_tester import _PortalTester
from pythagoras._220_data_portals import *
from pythagoras._310_ordinary_code_portals import OrdinaryCodePortal, OrdinaryFn


def f():
    return 42

def test_value_address_storablefn(tmpdir):
    # tmpdir = 3*"VALUE_ADDRESS_STORABLEFN_" + str(int(time.time())) + "_" + str(p)

    with (_PortalTester(OrdinaryCodePortal,tmpdir) as t):
        portal = t.portal
        global f

        f_new = OrdinaryFn(f)

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

        assert len(portal.global_value_store) == 1
        assert portal.get_number_of_linked_functions() == 0
        assert len(portal.get_linked_functions()) == 0

        # f_new.portal = portal
        # assert f_new.portal is f_new_restored.portal
        # # assert f_new._linked_portal is portal
        # assert f_new_restored._linked_portal is portal
        #
        # assert len(portal.global_value_store) == 1
        # assert portal.get_number_of_linked_functions() == 1
        # assert len(portal.get_linked_functions()) == 1




