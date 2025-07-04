from pythagoras._010_basic_portals.portal_tester import _PortalTester
from pythagoras._010_basic_portals import get_active_portal
from pythagoras._030_data_portals import ValueAddr
from pythagoras._060_autonomous_code_portals import *

def f(a, b):
    return a + b

def test_load_save_autonomous(tmpdir):
    with _PortalTester(AutonomousCodePortal, root_dict=tmpdir) as p:

        f_1 = AutonomousFn(f)
        f_address = ValueAddr(f_1)

        f_2 = f_address.get()
        assert f_2(a=1, b=2) == f(a=1, b=2) == 3
        assert f_2.name == f_1.name
        assert f_2.source_code == f_1.source_code

        f_naked_source_code = f_1.source_code
        f_name = f_1.name

        f_address._invalidate_cache()

    with _PortalTester(AutonomousCodePortal, root_dict=tmpdir):

        f_3 = f_address.get()
        assert f_3(a=1, b=2) == f(a=1, b=2) == 3
        assert f_3.name == f_name
        assert f_3.source_code == f_naked_source_code

def test_load_save_autonomous_one_fixed_kwarg(tmpdir):
    # tmpdir = "LOAD_SAVE_AUTONOMOUS_ONE_FIXED_KWARG_" + str(int(time.time()))
    with _PortalTester(AutonomousCodePortal, root_dict=tmpdir) as p:
        f_1 = AutonomousFn(fn=f, fixed_kwargs = dict(a=2000) )
        f_1_full = AutonomousFn(fn=f)
        f_address = ValueAddr(f_1)
        f_address_full = ValueAddr(f_1_full)

        f_2 = f_address.get()
        f_2_full = f_address_full.get()
        assert f_2(b=25) == f(a=2000, b=25) == 2025
        assert f_2_full(a=2000, b=25) == f(a=2000, b=25) == 2025
        assert f_2.name == f_1.name
        assert f_2.source_code == f_1.source_code

        f_naked_source_code = f_1.source_code
        f_name = f_1.name

        f_address._invalidate_cache()
        f_address_full._invalidate_cache()
        assert not hasattr(f_address, "_value_cache")
        assert not hasattr(f_address_full, "_value_cache")

    with _PortalTester(AutonomousCodePortal, root_dict=tmpdir):
        f_3 = f_address.get()
        f_3_full = f_address_full.get()
        assert f_3(b=25) == f(a=2000, b=25) == 2025
        assert f_3_full(a=2000, b=25) == f(a=2000, b=25) == 2025
        assert f_3.name == f_name
        assert f_3.source_code == f_naked_source_code


def test_load_save_autonomous_all_fixed_kwargs(tmpdir):
    # tmpdir = "LOAD_SAVE_AUTONOMOUS_ALL_FIXED_KWARGS_" + str(int(time.time()))
    with _PortalTester(AutonomousCodePortal, root_dict=tmpdir) as p:
        f_fixed_a = AutonomousFn(fn=f, fixed_kwargs = dict(a=2000) )
        f_fixed_both_a_b = f_fixed_a.fix_kwargs(b=25)
        assert f_fixed_a(b=0)==f(a=2000, b=0)
        address_fixed_a = ValueAddr(f_fixed_a)
        address_no_args = ValueAddr(f_fixed_both_a_b)

        address_fixed_a._invalidate_cache()

        f_2_fixed_a = address_fixed_a.get()
        f_2_fixed_both_a_b = address_no_args.get()
        assert f_2_fixed_a(b=25) == f(a=2000, b=25) == 2025
        assert f_2_fixed_both_a_b() == f(a=2000, b=25) == 2025
        assert f_2_fixed_both_a_b.name == f_fixed_a.name
        assert f_2_fixed_both_a_b.source_code == f_fixed_a.source_code

        address_fixed_a._invalidate_cache()
        address_no_args._invalidate_cache()

    with _PortalTester(AutonomousCodePortal, root_dict=tmpdir):
        f_3_fixed_a = address_fixed_a.get()
        f_3_fixed_both_a_b = address_no_args.get()
        assert f_3_fixed_a(b=25) == f(a=2000, b=25) == 2025
        assert f_3_fixed_both_a_b() == f(a=2000, b=25) == 2025

