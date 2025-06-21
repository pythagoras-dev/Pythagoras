from src.pythagoras._010_basic_portals import *
from src.pythagoras._010_basic_portals import _PortalTester
from src.pythagoras._010_basic_portals.basic_portal_core_classes_NEW import (
    _clear_all_portals )


def test_portal(tmpdir):
    the_dir = tmpdir
    with _PortalTester():

        portal = BasicPortal(tmpdir.mkdir("awer"))
        assert portal is not None
        assert most_recently_created_portal() is portal
        assert number_of_known_portals() == 1
        assert number_of_active_portals() == 0
        assert depth_of_active_portal_stack() == 0
        assert number_of_linked_portal_aware_objects() == 0

        assert active_portal() is portal

        assert number_of_known_portals() == 1
        assert number_of_active_portals() == 1
        assert depth_of_active_portal_stack() == 1

        portal2 = BasicPortal(tmpdir.mkdir("awasder"))
        portal3 = BasicPortal(tmpdir.mkdir("aadfgggr"))

        assert active_portal() is portal
        assert most_recently_created_portal() is portal3
        assert number_of_known_portals() == 3
        assert number_of_active_portals() == 1
        assert depth_of_active_portal_stack() == 1
        assert number_of_linked_portal_aware_objects() == 0



def test_clear_all_portals(tmpdir):
    with _PortalTester():
        portal = BasicPortal(tmpdir)
        portal2 = BasicPortal(tmpdir)
        portal3 = BasicPortal(tmpdir)
        _clear_all_portals()
        assert most_recently_created_portal() is None
        assert number_of_known_portals() == 0
        assert number_of_active_portals() == 0
        assert depth_of_active_portal_stack() == 0
        assert number_of_linked_portal_aware_objects() == 0



def test_portal_nested(tmpdir):

    with _PortalTester():

        portal = BasicPortal(tmpdir)
        portal2 = BasicPortal(tmpdir)
        portal3 = BasicPortal(tmpdir)

        assert most_recently_created_portal() is portal

        with portal:
            assert active_portal() == portal
            assert number_of_active_portals() == 1
            assert depth_of_active_portal_stack() == 1
            assert number_of_linked_portal_aware_objects() == 0
            with portal2:
                assert active_portal() == portal2
                assert number_of_active_portals() == 2
                assert depth_of_active_portal_stack() == 2
                assert number_of_linked_portal_aware_objects() == 0
                with portal3:
                    assert active_portal() == portal3
                    assert number_of_active_portals() == 3
                    assert depth_of_active_portal_stack() == 3
                    assert number_of_linked_portal_aware_objects() == 0
                    with portal2:
                        assert active_portal() == portal2
                        assert number_of_active_portals() == 3
                        assert depth_of_active_portal_stack() == 4
                        assert number_of_linked_portal_aware_objects() == 0
                        assert most_recently_created_portal() is portal
                    assert active_portal() == portal3
                    assert number_of_active_portals() == 3
                    assert depth_of_active_portal_stack() == 3
                    assert number_of_linked_portal_aware_objects() == 0
                assert active_portal() == portal2
                assert number_of_active_portals() == 2
                assert depth_of_active_portal_stack() == 2
                assert number_of_linked_portal_aware_objects() == 0
            assert active_portal() == portal
            assert number_of_active_portals() == 1
            assert depth_of_active_portal_stack() == 1
            assert number_of_linked_portal_aware_objects() == 0
