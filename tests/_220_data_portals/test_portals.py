from pythagoras._210_basic_portals import (
    get_current_portal
    , count_known_portals
    , count_active_portals
    , measure_active_portals_stack)
from pythagoras._220_data_portals import ValueAddr
from pythagoras._220_data_portals.data_portal_core_classes import DataPortal

from pythagoras._210_basic_portals.portal_tester import _PortalTester


def test_value_address_basic(tmpdir):
    with _PortalTester():
        tmpdir1 = tmpdir + "/test_value_address_basic"
        tmpdir2 = tmpdir + "/hihi"

        portal1 = DataPortal(tmpdir1)
        portal2 = DataPortal(tmpdir2)

        with portal1:
            _addr = ValueAddr(10)
            with portal2:
                _addr = ValueAddr(10)
                _addr = ValueAddr(10)
                _addr = ValueAddr(12)

        assert len(portal1.global_value_store) == 1
        assert len(portal2.global_value_store) == 2


def test_nested_portals_whitebox(tmpdir):
    with _PortalTester():
        tmpdir1 = tmpdir + "/t1"
        tmpdir2 = tmpdir + "/t2"
        tmpdir3 = tmpdir + "/t3"

        assert count_known_portals() == 0
        portal1 = DataPortal(tmpdir1)
        assert count_known_portals() == 1
        portal2 = DataPortal(tmpdir2)
        assert count_known_portals() == 2
        portal3 = DataPortal(tmpdir3)
        assert count_known_portals() == 3
        assert count_active_portals() == 0

        with portal1:
            assert count_known_portals() == 3
            assert count_active_portals() == 1
            assert measure_active_portals_stack() == 1
            with portal2:
                assert count_known_portals() == 3
                assert count_active_portals() == 2
                assert measure_active_portals_stack() == 2
                with portal3:
                    assert count_known_portals() == 3
                    assert count_active_portals() == 3
                    assert measure_active_portals_stack() == 3

        with portal1:
            assert count_active_portals() == 1
            assert measure_active_portals_stack() == 1
            with portal2:
                assert count_active_portals() == 2
                assert measure_active_portals_stack() == 2
                with portal2:
                    assert count_active_portals() == 2
                    assert measure_active_portals_stack() == 3
                    with portal3:
                        assert count_active_portals() == 3
                        assert measure_active_portals_stack() == 4
                        with portal1:
                            assert count_active_portals() == 3
                            assert measure_active_portals_stack() == 5
                assert count_active_portals() == 2
                assert measure_active_portals_stack() == 2
            assert count_active_portals() == 1
            assert measure_active_portals_stack() == 1


def test_find_portal_basic(tmpdir):
    with _PortalTester():
        tmpdir1 = tmpdir + "/t1"
        tmpdir2 = tmpdir + "/t2"
        tmpdir3 = tmpdir + "/t3"

        portal1 = DataPortal(tmpdir1)
        portal2 = DataPortal(tmpdir2)
        portal3 = DataPortal(tmpdir3)

        with portal1:
            assert portal1 is get_current_portal()
            with portal2:
                assert portal2 is get_current_portal()
                with portal3:
                    assert portal3 is get_current_portal()

        with portal1:
            assert portal1 == get_current_portal()
            with portal2:
                assert portal2 == get_current_portal()
                with portal2:
                    assert portal2 == get_current_portal()
                    with portal3:
                        assert portal3 == get_current_portal()
                        with portal1:
                            assert portal1 == get_current_portal()
                assert portal2 == get_current_portal()
            assert portal1 == get_current_portal()