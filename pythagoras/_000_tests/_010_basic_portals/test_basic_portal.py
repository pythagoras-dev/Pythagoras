from pythagoras import BasicPortal
from pythagoras import _PortalTester
from pythagoras._010_basic_portals.portal_aware_classes import (
    _noncurrent_portals, _most_recently_entered_portal, _entered_portals)


def test_portal(tmpdir):
    the_dir = tmpdir
    with _PortalTester():

        portal = BasicPortal(tmpdir.mkdir("awer"))
        assert portal is not None
        assert _most_recently_entered_portal() is None
        assert len(_noncurrent_portals()) == 1
        assert len(_noncurrent_portals(expected_type=BasicPortal)) == 1
        assert _entered_portals() == []

        portal2 = BasicPortal(tmpdir.mkdir("awasder"))
        portal3 = BasicPortal(tmpdir.mkdir("aadfgggr"))
        assert portal is not None
        assert _most_recently_entered_portal() is None
        assert len(_noncurrent_portals()) == 3
        assert len(_noncurrent_portals(expected_type=BasicPortal)) == 3
        assert _entered_portals() == []


def test_clean_all(tmpdir):
    with _PortalTester():
        portal = BasicPortal(tmpdir)
        portal2 = BasicPortal(tmpdir)
        portal3 = BasicPortal(tmpdir)
        BasicPortal._clear_all()
        assert _most_recently_entered_portal() is None
        assert len(_noncurrent_portals()) == 0
        assert _entered_portals() == []


# def test_portal_nested(tmpdir):
#
#     with _PortalTester():
#
#         portal = BasicPortal(tmpdir)
#         portal2 = BasicPortal(tmpdir)
#         portal3 = BasicPortal(tmpdir)
#
#         with portal:
#             assert portal.current_portal() == portal
#             assert get_current_portal() == portal
#             assert len(portal.noncurrent_portals()) == 2
#             assert portal.active_portals() == [portal]
#             with portal2:
#                 assert portal.current_portal() == portal2
#                 assert get_current_portal() == portal2
#                 assert len(portal.noncurrent_portals()) == 2
#                 assert portal.active_portals() == [portal2, portal]
#                 with portal3:
#                     assert portal.current_portal() == portal3
#                     assert get_current_portal() == portal3
#                     assert len(portal.noncurrent_portals()) == 2
#                     assert portal.active_portals() == [portal3, portal2, portal]
#                     with portal2:
#                         assert portal.current_portal() == portal2
#                         assert get_current_portal() == portal2
#                         assert len(portal.noncurrent_portals()) == 2
#                         assert portal.active_portals() == [portal2, portal3, portal]
#                     assert portal.current_portal() == portal3
#                     assert get_current_portal() == portal3
#                     assert len(portal.noncurrent_portals()) == 2
#                     assert portal.active_portals() == [portal3, portal2, portal]
#                 assert portal.current_portal() == portal2
#                 assert get_current_portal() == portal2
#                 assert len(portal.noncurrent_portals()) == 2
#                 assert portal.active_portals() == [portal2, portal]
#             assert portal.current_portal() == portal
#             assert get_current_portal() == portal
#             assert len(portal.noncurrent_portals()) == 2
#             assert portal.active_portals() == [portal]
