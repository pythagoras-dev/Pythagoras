from pythagoras import BasicPortal, _PortalTester
from pythagoras._010_basic_portals.portal_aware_classes import find_portal_to_use


def test_portal_nested(tmpdir):

    with _PortalTester():

        portal = BasicPortal(tmpdir)
        portal2 = BasicPortal(tmpdir)
        portal3 = BasicPortal(tmpdir)

        with portal:
            assert find_portal_to_use() == portal
            assert find_portal_to_use(suggested_portal=portal3) == portal3
            with portal2:
                assert find_portal_to_use() == portal2
                assert find_portal_to_use(suggested_portal=portal3) == portal3
                portal4 = BasicPortal(tmpdir)
                with portal3:
                    assert find_portal_to_use() == portal3
                    assert find_portal_to_use(suggested_portal=portal2) == portal2
                    with portal2:
                        assert find_portal_to_use() == portal2
                        assert find_portal_to_use(suggested_portal=portal) == portal
                    assert find_portal_to_use() == portal3
                assert find_portal_to_use(suggested_portal=portal2) == portal2
                assert find_portal_to_use() == portal2
                assert find_portal_to_use(suggested_portal=portal3) == portal3
            assert find_portal_to_use() == portal