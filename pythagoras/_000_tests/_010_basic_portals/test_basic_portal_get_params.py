from pythagoras import BasicPortal
from pythagoras import _PortalTester
from parameterizable import get_object_from_portable_params

def test_basic_portal_get_params(tmpdir):
    with _PortalTester(BasicPortal, root_dict = tmpdir) as t:
        portal = t.portal
        params = portal.get_params()
        exportable_params = portal.__get_portable_params__()
        new_portal = get_object_from_portable_params(exportable_params)
        new_params = new_portal.get_params()
        new_exportable_params = new_portal.__get_portable_params__()
        assert params == new_params
        assert exportable_params == new_exportable_params

