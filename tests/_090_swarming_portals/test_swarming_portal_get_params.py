from pythagoras import SwarmingPortal
from pythagoras import _PortalTester
from parameterizable import get_object_from_portable_params

def test_swarming_portal_get_params(tmpdir):
    with _PortalTester(SwarmingPortal, root_dict = tmpdir) as t:
        portal = t.portal
        params = portal.get_params()
        exportable_params = portal.get_portable_params()

    new_portal = get_object_from_portable_params(exportable_params)
    new_params = new_portal.get_params()
    new_exportable_params = new_portal.get_portable_params()
    assert params == new_params
    assert exportable_params == new_exportable_params



def test_swarming_data_portal_get_params_1(tmpdir):
    with _PortalTester(SwarmingPortal
            , root_dict = tmpdir
            , p_consistency_checks = 0.5
            , max_n_workers = 5) as t:
        portal = t.portal
        params = portal.get_params()
        assert params["p_consistency_checks"] == 0.5
        assert params["max_n_workers"] == 5
        exportable_params = portal.get_portable_params()
        assert exportable_params["max_n_workers"] == 5

    new_portal = get_object_from_portable_params(exportable_params)
    new_params = new_portal.get_params()
    new_exportable_params = new_portal.get_portable_params()
    assert params == new_params
    assert exportable_params == new_exportable_params
