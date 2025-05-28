from src.pythagoras._010_basic_portals.portal_tester import _PortalTester
from src.pythagoras._080_pure_code_portals.pure_core_classes import (
    PureCodePortal)
from src.pythagoras._080_pure_code_portals.pure_decorator import pure
from src.pythagoras._030_data_portals import ValueAddr


def f1():
    return 0

def f2(f1):
    return f1()*2

def f3(f2, f1):
    return f2(f1=f1)*3

def f4(f3,f2,f1):
    return f3(f2=f2,f1=f1)*4

def test_chained_save_load(tmpdir):
    with _PortalTester(PureCodePortal, tmpdir) as t:

        global f1, f2, f3, f4

        f1 = pure()(f1)
        f2 = pure()(f2)
        f3 = pure()(f3)

        assert f3(f2=f2,f1=f1) == 0
        assert f4(f3=f3,f2=f2,f1=f1) == 0

        address_1 = ValueAddr(f1, t.portal)
        assert address_1.get()() == 0
        address_2 = ValueAddr(f2, t.portal)
        assert address_2.get()(f1=address_1.get()) == 0
        address_3 = ValueAddr(f3, t.portal)
        assert address_3.get()(f1=address_1.get(), f2=address_2.get()) == 0

    address_3._invalidate_cache()
    address_2._invalidate_cache()
    address_1._invalidate_cache()

    with _PortalTester(PureCodePortal, tmpdir) as t:
        del f1, f2, f3, f4

        address_3._portal = t.portal
        address_2._portal = t.portal
        address_1._portal = t.portal
        new_f3 = address_3.get()
        new_f2 = address_2.get()
        new_f1 = address_1.get()
        result_1 = new_f1()
        result_2 = new_f2(f1=new_f1)
        result_3 = new_f3(f1=new_f1, f2=new_f2)
        assert result_1 == result_2 == result_3 == 0
