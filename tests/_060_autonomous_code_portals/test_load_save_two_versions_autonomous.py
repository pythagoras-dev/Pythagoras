
from src.pythagoras._010_basic_portals.portal_tester import _PortalTester
from src.pythagoras._030_data_portals import ValueAddr
from src.pythagoras._060_autonomous_code_portals import *

import pytest

@pytest.mark.parametrize("p",[0,0.5,1])
def test_load_save_two_versions_autonomous(tmpdir,p):
    with _PortalTester(
            AutonomousCodePortal
            , root_dict=tmpdir
            , p_consistency_checks=p
            ) as t:
        assert len(t.portal.value_store) == 0
        def f(a, b):
            return a + b

        f_1 = AutonomousFn(f)
        f_1_address = ValueAddr(f_1, portal = t.portal)
        assert len(t.portal.value_store) == 1
        f_1_address._invalidate_cache()

    with _PortalTester(
            AutonomousCodePortal
            , root_dict=tmpdir
            , p_consistency_checks=p
            ) as t:

        def f(a, b):
            return a * b * 2

        f_2 = AutonomousFn(f)
        f_2_address = ValueAddr(f_2, portal = t.portal)
        assert len(t.portal.value_store) == 2
        f_2_address._invalidate_cache()
        f_2_address._invalidate_cache()

    with _PortalTester(
            AutonomousCodePortal
            , root_dict=tmpdir
            , p_consistency_checks=p
            ) as t:

        f_1_address._portal = t.portal
        f_2_address._portal = t.portal

        assert len(t.portal.value_store) == 2

        f_a = f_1_address.get()
        assert f_a(a=1, b=2) == 3

        f_b = f_2_address.get()
        assert f_b(a=1, b=2) == 4