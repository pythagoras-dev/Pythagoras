import pytest

from src.pythagoras._010_basic_portals.portal_tester import _PortalTester
from src.pythagoras._030_data_portals import *


def f():
    return 42

@pytest.mark.parametrize("p",[1,0.5,0])
def test_value_address_storablefn(tmpdir,p):
    # tmpdir = 3*"VALUE_ADDRESS_STORABLEFN_" + str(int(time.time())) + "_" + str(p)


    with _PortalTester(DataPortal,tmpdir, p_consistency_checks=p) as t:
        portal = t.portal
        global f

        f_new = StorableFn(f)

        assert f_new._portal is None

        assert f_new() == 42

        assert f_new._portal is portal

        hash_id = f_new.hash_signature

        f_new_addr =  ValueAddr(f_new, portal = portal)
        f_new_addr._invalidate_cache()

        assert f_new_addr.hash_signature == hash_id

        f_new_restored = f_new_addr.get()

        assert f_new_restored() == 42

        assert id(f_new) != id(f_new_restored)

        assert len(portal.value_store) == 1
        assert len(portal.known_functions_ids) == 2
        assert len(portal.known_functions) == 1

