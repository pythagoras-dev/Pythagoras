import parameterizable

from pythagoras import _PortalTester, DataPortal

from multiprocessing import get_context


def test_date_portal_params(tmpdir):
    the_dir = tmpdir
    with _PortalTester():

        portal1 = DataPortal(tmpdir.mkdir("awer"))
        portal1_params = portal1.get_params()
        portal1_params_json = parameterizable.dumpjs(portal1)

        portal2 = parameterizable.loadjs(portal1_params_json)
        portal2_params = portal2.get_params()
        portal1_params_json2 = parameterizable.dumpjs(portal2)

        assert portal1_params == portal2_params
        assert portal1_params_json == portal1_params_json2


def test_data_portal_params_multiprocessing(tmpdir):
    with _PortalTester():
        portal = DataPortal(tmpdir.mkdir("awer"))
        assert len(portal._value_store) == 0
        portal_params_json = parameterizable.dumpjs(portal)
        ctx = get_context("spawn")
        p = ctx.Process(target=_update_data_portal_in_a_subprocess
                    , args=(portal_params_json,))
        p.start()
        p.join()
        assert len(portal._value_store) == 1


def _update_data_portal_in_a_subprocess(portal_init_params):
    portal = parameterizable.loadjs(portal_init_params)
    portal._value_store["abcd"] = 1234