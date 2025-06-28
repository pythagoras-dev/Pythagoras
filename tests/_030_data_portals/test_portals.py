from pythagoras._010_basic_portals import (
    get_active_portal
    , get_number_of_known_portals
    , get_number_of_portals_in_active_stack
    , get_depth_of_active_portal_stack)
from pythagoras._030_data_portals import ValueAddr
from pythagoras._030_data_portals.data_portal_core_classes import DataPortal

from pythagoras._010_basic_portals.portal_tester import _PortalTester


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

        assert get_number_of_known_portals() == 0
        portal1 = DataPortal(tmpdir1)
        assert get_number_of_known_portals() == 1
        portal2 = DataPortal(tmpdir2)
        assert get_number_of_known_portals() == 2
        portal3 = DataPortal(tmpdir3)
        assert get_number_of_known_portals() == 3
        assert get_number_of_portals_in_active_stack() == 0

        with portal1:
            assert get_number_of_known_portals() == 3
            assert get_number_of_portals_in_active_stack() == 1
            assert get_depth_of_active_portal_stack() == 1
            with portal2:
                assert get_number_of_known_portals() == 3
                assert get_number_of_portals_in_active_stack() == 2
                assert get_depth_of_active_portal_stack() == 2
                with portal3:
                    assert get_number_of_known_portals() == 3
                    assert get_number_of_portals_in_active_stack() == 3
                    assert get_depth_of_active_portal_stack() == 3

        with portal1:
            assert get_number_of_portals_in_active_stack() == 1
            assert get_depth_of_active_portal_stack() == 1
            with portal2:
                assert get_number_of_portals_in_active_stack() == 2
                assert get_depth_of_active_portal_stack() == 2
                with portal2:
                    assert get_number_of_portals_in_active_stack() == 2
                    assert get_depth_of_active_portal_stack() == 3
                    with portal3:
                        assert get_number_of_portals_in_active_stack() == 3
                        assert get_depth_of_active_portal_stack() == 4
                        with portal1:
                            assert get_number_of_portals_in_active_stack() == 3
                            assert get_depth_of_active_portal_stack() == 5
                assert get_number_of_portals_in_active_stack() == 2
                assert get_depth_of_active_portal_stack() == 2
            assert get_number_of_portals_in_active_stack() == 1
            assert get_depth_of_active_portal_stack() == 1


def test_find_portal_basic(tmpdir):
    with _PortalTester():
        tmpdir1 = tmpdir + "/t1"
        tmpdir2 = tmpdir + "/t2"
        tmpdir3 = tmpdir + "/t3"

        portal1 = DataPortal(tmpdir1)
        portal2 = DataPortal(tmpdir2)
        portal3 = DataPortal(tmpdir3)

        with portal1:
            assert portal1 is get_active_portal()
            with portal2:
                assert portal2 is get_active_portal()
                with portal3:
                    assert portal3 is get_active_portal()

        with portal1:
            assert portal1 == get_active_portal()
            with portal2:
                assert portal2 == get_active_portal()
                with portal2:
                    assert portal2 == get_active_portal()
                    with portal3:
                        assert portal3 == get_active_portal()
                        with portal1:
                            assert portal1 == get_active_portal()
                assert portal2 == get_active_portal()
            assert portal1 == get_active_portal()