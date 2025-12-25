from pythagoras._010_basic_portals import *
from pythagoras._010_basic_portals import _PortalTester
from pythagoras._010_basic_portals.basic_portal_core_classes import (
    _clear_all_portals, get_nonactive_portals)


def test_portal(tmpdir):
    the_dir = tmpdir
    with _PortalTester():

        portal = BasicPortal(tmpdir.mkdir("awer"))
        assert portal is not None
        assert get_most_recently_created_portal() is portal
        assert get_number_of_known_portals() == 1
        assert get_number_of_portals_in_active_stack() == 0
        assert get_depth_of_active_portal_stack() == 0
        assert get_number_of_linked_portal_aware_objects() == 0

        assert get_current_active_portal() is portal

        assert get_number_of_known_portals() == 1
        assert get_number_of_portals_in_active_stack() == 1
        assert get_depth_of_active_portal_stack() == 1

        portal2 = BasicPortal(tmpdir.mkdir("awasder"))
        portal3 = BasicPortal(tmpdir.mkdir("aadfgggr"))

        assert get_current_active_portal() is portal
        assert get_most_recently_created_portal() is portal3
        assert get_number_of_known_portals() == 3
        assert get_number_of_portals_in_active_stack() == 1
        assert get_depth_of_active_portal_stack() == 1
        assert get_number_of_linked_portal_aware_objects() == 0



def test_clear_all_portals(tmpdir):
    with _PortalTester():
        portal = BasicPortal(tmpdir)
        portal2 = BasicPortal(tmpdir)
        portal3 = BasicPortal(tmpdir)
        _clear_all_portals()
        assert get_most_recently_created_portal() is None
        assert get_number_of_known_portals() == 0
        assert get_number_of_portals_in_active_stack() == 0
        assert get_depth_of_active_portal_stack() == 0
        assert get_number_of_linked_portal_aware_objects() == 0



def test_portal_nested(tmpdir):

    with _PortalTester():

        portal = BasicPortal(tmpdir)
        portal2 = BasicPortal(tmpdir)
        portal3 = BasicPortal(tmpdir)

        assert get_most_recently_created_portal() is portal3

        with portal:
            assert get_current_active_portal() == portal
            assert get_number_of_portals_in_active_stack() == 1
            assert get_depth_of_active_portal_stack() == 1
            assert get_number_of_linked_portal_aware_objects() == 0
            with portal2:
                assert get_current_active_portal() == portal2
                assert get_number_of_portals_in_active_stack() == 2
                assert get_depth_of_active_portal_stack() == 2
                assert get_number_of_linked_portal_aware_objects() == 0
                with portal3:
                    assert get_current_active_portal() == portal3
                    assert get_number_of_portals_in_active_stack() == 3
                    assert get_depth_of_active_portal_stack() == 3
                    assert get_number_of_linked_portal_aware_objects() == 0
                    with portal2:
                        assert get_current_active_portal() == portal2
                        assert get_number_of_portals_in_active_stack() == 3
                        assert get_depth_of_active_portal_stack() == 4
                        assert get_number_of_linked_portal_aware_objects() == 0
                        assert get_most_recently_created_portal() is portal3
                    assert get_current_active_portal() == portal3
                    assert get_number_of_portals_in_active_stack() == 3
                    assert get_depth_of_active_portal_stack() == 3
                    assert get_number_of_linked_portal_aware_objects() == 0
                assert get_current_active_portal() == portal2
                assert get_number_of_portals_in_active_stack() == 2
                assert get_depth_of_active_portal_stack() == 2
                assert get_number_of_linked_portal_aware_objects() == 0
            assert get_current_active_portal() == portal
            assert get_number_of_portals_in_active_stack() == 1
            assert get_depth_of_active_portal_stack() == 1
            assert get_number_of_linked_portal_aware_objects() == 0


def test_get_nonactive_portals(tmpdir):
    """Test get_nonactive_portals returns portals not in active stack."""
    with _PortalTester():
        portal1 = BasicPortal(tmpdir.mkdir("p1"))
        portal2 = BasicPortal(tmpdir.mkdir("p2"))
        portal3 = BasicPortal(tmpdir.mkdir("p3"))
        
        # No portals active initially
        nonactive = get_nonactive_portals()
        assert len(nonactive) == 3
        assert portal1 in nonactive
        assert portal2 in nonactive
        assert portal3 in nonactive
        
        # Activate portal1
        with portal1:
            nonactive = get_nonactive_portals()
            assert len(nonactive) == 2
            assert portal1 not in nonactive
            assert portal2 in nonactive
            assert portal3 in nonactive
            
            # Activate portal2 as well
            with portal2:
                nonactive = get_nonactive_portals()
                assert len(nonactive) == 1
                assert portal1 not in nonactive
                assert portal2 not in nonactive
                assert portal3 in nonactive
        
        # Back to no active portals
        nonactive = get_nonactive_portals()
        assert len(nonactive) == 3
