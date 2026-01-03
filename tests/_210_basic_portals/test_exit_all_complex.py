from pythagoras import BasicPortal, _PortalTester, get_depth_of_active_portal_stack
from pythagoras._210_basic_portals.basic_portal_core_classes import _clear_all_portals


def test_exit_all_complex(tmpdir):
    with _PortalTester():
        for i in range(3):
            portal = BasicPortal(str(tmpdir)+"_"+str(i))
            portal.__enter__()
        assert get_depth_of_active_portal_stack() == 3
        with BasicPortal(str(tmpdir)+"_AAAAA"):
            assert get_depth_of_active_portal_stack() == 4
            with BasicPortal(str(tmpdir)+"_BBBBB"):
                assert get_depth_of_active_portal_stack() == 5
                with BasicPortal(str(tmpdir)+"_CCCCC"):
                    assert get_depth_of_active_portal_stack() == 6
        assert get_depth_of_active_portal_stack() == 3
        _clear_all_portals()
        assert get_depth_of_active_portal_stack() == 0