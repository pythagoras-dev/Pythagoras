from src.pythagoras._010_basic_portals import (
    active_portal
    , number_of_known_portals
    , number_of_active_portals
    , depth_of_active_portal_stack)
from src.pythagoras._030_data_portals import ValueAddr
from src.pythagoras._030_data_portals.data_portal_core_classes import DataPortal

from src.pythagoras._010_basic_portals.portal_tester import _PortalTester


def test_value_address_basic(tmpdir):
    with _PortalTester():
        tmpdir1 = tmpdir + "/test_value_address_basic"
        tmpdir2 = tmpdir + "/hihi"

        portal1 = DataPortal(tmpdir1)
        portal2 = DataPortal(tmpdir2)

        with portal1:
            addr = ValueAddr(10)
            with portal2:
                addr = ValueAddr(10)
                addr = ValueAddr(10)
                addr = ValueAddr(12)

        assert len(portal1._value_store) == 1
        assert len(portal2._value_store) == 2


def test_nested_portals_whitebox(tmpdir):
    with _PortalTester():
        tmpdir1 = tmpdir + "/t1"
        tmpdir2 = tmpdir + "/t2"
        tmpdir3 = tmpdir + "/t3"

        assert number_of_known_portals() == 0
        portal1 = DataPortal(tmpdir1)
        assert number_of_known_portals() == 1
        portal2 = DataPortal(tmpdir2)
        assert number_of_known_portals() == 2
        portal3 = DataPortal(tmpdir3)
        assert number_of_known_portals() == 3
        assert number_of_active_portals() == 0

        with portal1:
            assert number_of_known_portals() == 3
            assert number_of_active_portals() == 1
            assert depth_of_active_portal_stack() == 1
            with portal2:
                assert number_of_known_portals() == 3
                assert number_of_active_portals() == 2
                assert depth_of_active_portal_stack() == 2
                with portal3:
                    assert number_of_known_portals() == 3
                    assert number_of_active_portals() == 3
                    assert depth_of_active_portal_stack() == 3

        with portal1:
            assert number_of_active_portals() == 1
            assert depth_of_active_portal_stack() == 1
            with portal2:
                assert number_of_active_portals() == 2
                assert depth_of_active_portal_stack() == 2
                with portal2:
                    assert number_of_active_portals() == 2
                    assert depth_of_active_portal_stack() == 3
                    with portal3:
                        assert number_of_active_portals() == 3
                        assert depth_of_active_portal_stack() == 4
                        with portal1:
                            assert number_of_active_portals() == 3
                            assert depth_of_active_portal_stack() == 5
                assert number_of_active_portals() == 2
                assert depth_of_active_portal_stack() == 2
            assert number_of_active_portals() == 1
            assert depth_of_active_portal_stack() == 1


def test_find_portal_basic(tmpdir):
    with _PortalTester():
        tmpdir1 = tmpdir + "/t1"
        tmpdir2 = tmpdir + "/t2"
        tmpdir3 = tmpdir + "/t3"

        portal1 = DataPortal(tmpdir1)
        portal2 = DataPortal(tmpdir2)
        portal3 = DataPortal(tmpdir3)

        with portal1:
            assert portal1 is active_portal()
            with portal2:
                assert portal2 is active_portal()
                with portal3:
                    assert portal3 is active_portal()

        with portal1:
            assert portal1 == active_portal()
            with portal2:
                assert portal2 == active_portal()
                with portal2:
                    assert portal2 == active_portal()
                    with portal3:
                        assert portal3 == active_portal()
                        with portal1:
                            assert portal1 == active_portal()
                assert portal2 == active_portal()
            assert portal1 == active_portal()