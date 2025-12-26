from pythagoras import BasicPortal, _PortalTester, get_current_portal


def test_portal_nested(tmpdir):

    with _PortalTester():

        portal = BasicPortal(tmpdir)
        portal2 = BasicPortal(tmpdir)
        portal3 = BasicPortal(tmpdir)

        with portal:
            assert get_current_portal() == portal
            with portal2:
                assert get_current_portal() == portal2
                portal4 = BasicPortal(tmpdir)
                with portal3:
                    assert get_current_portal() == portal3
                    with portal2:
                        assert get_current_portal() == portal2
                    assert get_current_portal() == portal3
                assert get_current_portal() == portal2
            assert get_current_portal() == portal