import mixinforge

from pythagoras import _PortalTester, SwarmingPortal


def test_swarming_portal_params(tmpdir):
    with _PortalTester():

        portal1 = SwarmingPortal(root_dict=tmpdir.mkdir("pure"), max_n_workers=0)
        portal1_params = portal1.get_params()
        portal1_params_json = mixinforge.dumpjs(portal1)

        portal2 = mixinforge.loadjs(portal1_params_json)
        portal2_params = portal2.get_params()
        portal1_params_json2 = mixinforge.dumpjs(portal2)

        assert portal1_params == portal2_params
        assert portal1_params_json == portal1_params_json2
    