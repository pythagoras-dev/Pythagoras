from src.pythagoras import SwarmingPortal
from src.pythagoras import _PortalTester
from parameterizable import get_object_from_portable_params

def test_autonomous_portal_get_params(tmpdir):
    with _PortalTester(SwarmingPortal, root_dict = tmpdir) as t:
        portal = t.portal
        params = portal.get_params()
        exportable_params = portal.__get_portable_params__()
        new_portal = get_object_from_portable_params(exportable_params)
        new_params = new_portal.get_params()
        new_exportable_params = new_portal.__get_portable_params__()
        assert params == new_params
        assert exportable_params == new_exportable_params



def test_autonomous_data_portal_get_params_1(tmpdir):
    with _PortalTester(SwarmingPortal
            , root_dict = tmpdir
            , n_background_workers = 5) as t:
        portal = t.portal
        params = portal.get_params()
        assert params["n_background_workers"] == 5
        exportable_params = portal.__get_portable_params__()
        assert exportable_params["n_background_workers"] == 5
        new_portal = get_object_from_portable_params(exportable_params)
        new_params = new_portal.get_params()
        new_exportable_params = new_portal.__get_portable_params__()
        assert params == new_params
        assert exportable_params == new_exportable_params
