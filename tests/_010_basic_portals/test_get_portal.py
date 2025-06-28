from pythagoras import BasicPortal, _PortalTester
from pythagoras._010_basic_portals.basic_portal_core_classes import (
    get_active_portal)


def test_portal_nested(tmpdir):

    with _PortalTester():

        portal = BasicPortal(tmpdir)
        portal2 = BasicPortal(tmpdir)
        portal3 = BasicPortal(tmpdir)

        with portal:
            assert get_active_portal() == portal
            with portal2:
                assert get_active_portal() == portal2
                portal4 = BasicPortal(tmpdir)
                with portal3:
                    assert get_active_portal() == portal3
                    with portal2:
                        assert get_active_portal() == portal2
                    assert get_active_portal() == portal3
                assert get_active_portal() == portal2
            assert get_active_portal() == portal