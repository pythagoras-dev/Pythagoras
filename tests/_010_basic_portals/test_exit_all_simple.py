from pythagoras import BasicPortal, _PortalTester, get_depth_of_active_portal_stack
from pythagoras._010_basic_portals.basic_portal_core_classes import _clear_all_portals

def test_exit_all_simple(tmpdir):
    with _PortalTester():
        for i in range(3):
            portal = BasicPortal(str(tmpdir)+"_"+str(i))
            portal.__enter__()
        assert get_depth_of_active_portal_stack() == 3
        _clear_all_portals()
        assert get_depth_of_active_portal_stack() == 0
