from src.pythagoras._010_basic_portals.portal_tester import _PortalTester
from src.pythagoras._010_basic_portals.portal_aware_class_OLD import _most_recently_entered_portal
from src.pythagoras._030_data_portals import ValueAddr
from src.pythagoras._060_autonomous_code_portals import *

def f(a, b):
    return a + b

def test_load_save_autonomous(tmpdir):

    with _PortalTester(AutonomousCodePortal, root_dict=tmpdir) as p:

        f_1 = AutonomousFn(f)
        f_address = ValueAddr(f_1, portal = p.portal)

        f_2 = f_address.get()
        assert f_2(a=1, b=2) == f(a=1, b=2) == 3
        assert f_2.name == f_1.name
        assert f_2.source_code == f_1.source_code

        f_naked_source_code = f_1.source_code
        f_name = f_1.name

        f_address._invalidate_cache()


    with _PortalTester(AutonomousCodePortal, root_dict=tmpdir):

        del f_address._portal

        f_address._portal = _most_recently_entered_portal()

        f_3 = f_address.get()
        assert f_3(a=1, b=2) == f(a=1, b=2) == 3
        assert f_3.name == f_name
        assert f_3.source_code == f_naked_source_code

def test_load_save_autonomous_one_fixed_kwarg(tmpdir):
    # tmpdir = "LOAD_SAVE_AUTONOMOUS_ONE_FIXED_KWARG_" + str(int(time.time()))
    with _PortalTester(AutonomousCodePortal, root_dict=tmpdir) as p:
        f_1 = AutonomousFn(fn=f, fixed_kwargs = dict(a=2000) )
        f_1_full = AutonomousFn(fn=f)
        f_address = ValueAddr(f_1, portal=p.portal)
        f_address_full = ValueAddr(f_1_full, portal=p.portal)

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

    with _PortalTester(AutonomousCodePortal, root_dict=tmpdir):
        del f_address._portal
        del f_address_full._portal

        f_address._portal = _most_recently_entered_portal()
        f_address_full._portal = _most_recently_entered_portal()

        f_3 = f_address.get()
        f_3_full = f_address_full.get()
        assert f_3(b=25) == f(a=2000, b=25) == 2025
        assert f_3_full(a=2000, b=25) == f(a=2000, b=25) == 2025
        assert f_3.name == f_name
        assert f_3.source_code == f_naked_source_code


def test_load_save_autonomous_all_fixed_kwargs(tmpdir):
    # tmpdir = "LOAD_SAVE_AUTONOMOUS_ALL_FIXED_KWARGS_" + str(int(time.time()))
    with _PortalTester(AutonomousCodePortal, root_dict=tmpdir) as p:
        f_1 = AutonomousFn(fn=f, fixed_kwargs = dict(a=2000) )
        f_1_no_args = f_1.fix_kwargs(b=25)
        f_address = ValueAddr(f_1, portal=p.portal)
        f_address_no_args = ValueAddr(f_1_no_args, portal=p.portal)

        f_2 = f_address.get()
        f_2_no_args = f_address_no_args.get()
        assert f_2(b=25) == f(a=2000, b=25) == 2025
        assert f_2_no_args() == f(a=2000, b=25) == 2025
        assert f_2_no_args.name == f_1.name
        assert f_2_no_args.source_code == f_1.source_code

        f_address._invalidate_cache()
        f_address_no_args._invalidate_cache()

    with _PortalTester(AutonomousCodePortal, root_dict=tmpdir):
        del f_address._portal
        del f_address_no_args._portal

        f_address._portal = _most_recently_entered_portal()
        f_address_no_args._portal = _most_recently_entered_portal()

        f_3 = f_address.get()
        f_3_no_args = f_address_no_args.get()
        assert f_3(b=25) == f(a=2000, b=25) == 2025
        assert f_3_no_args() == f(a=2000, b=25) == 2025

