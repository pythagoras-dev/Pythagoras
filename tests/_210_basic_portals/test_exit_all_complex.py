from pythagoras import BasicPortal, _PortalTester, measure_active_portals_stack
from pythagoras._210_basic_portals.basic_portal_core_classes import _clear_all_portals


def test_exit_all_complex(tmpdir):
    with _PortalTester():
        for i in range(3):
            portal = BasicPortal(str(tmpdir)+"_"+str(i))
            portal.__enter__()
        assert measure_active_portals_stack() == 3
        with BasicPortal(str(tmpdir)+"_AAAAA"):
            assert measure_active_portals_stack() == 4
            with BasicPortal(str(tmpdir)+"_BBBBB"):
                assert measure_active_portals_stack() == 5
                with BasicPortal(str(tmpdir)+"_CCCCC"):
                    assert measure_active_portals_stack() == 6
        assert measure_active_portals_stack() == 3
        _clear_all_portals()
        assert measure_active_portals_stack() == 0