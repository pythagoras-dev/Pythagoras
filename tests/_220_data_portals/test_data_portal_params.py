import mixinforge

from pythagoras import _PortalTester, DataPortal

from multiprocessing import get_context


def test_date_portal_params(tmpdir):
    with _PortalTester():

        portal1 = DataPortal(tmpdir.mkdir("awer"))
        portal1_params = portal1.get_params()
        portal1_params_json = mixinforge.dumpjs(portal1)

        portal2 = mixinforge.loadjs(portal1_params_json)
        portal2_params = portal2.get_params()
        portal1_params_json2 = mixinforge.dumpjs(portal2)

        assert portal1_params == portal2_params
        assert portal1_params_json == portal1_params_json2


def test_data_portal_params_multiprocessing(tmpdir):
    with _PortalTester():
        portal = DataPortal(tmpdir.mkdir("awer"))
        assert len(portal.global_value_store) == 0
        portal_params_json = mixinforge.dumpjs(portal)
        ctx = get_context("spawn")
        p = ctx.Process(target=_update_data_portal_in_a_subprocess
                    , args=(portal_params_json,))
        p.start()
        p.join()
        assert len(portal.global_value_store) == 1


def _update_data_portal_in_a_subprocess(portal_init_params):
    portal = mixinforge.loadjs(portal_init_params)
    portal.global_value_store["abcd"] = 1234