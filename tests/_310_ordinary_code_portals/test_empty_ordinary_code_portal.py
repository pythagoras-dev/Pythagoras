from persidict import PersiDict


from pythagoras._310_ordinary_code_portals import OrdinaryCodePortal
from pythagoras._210_basic_portals.portal_tester import _PortalTester

def test_empty_ordinary_code_portal(tmpdir):
    with _PortalTester(OrdinaryCodePortal, tmpdir) as p:
        assert isinstance(p.portal._root_dict, PersiDict)
        assert p.portal.get_number_of_linked_functions() == 0
        assert p.portal.count_linked_objects() == 0

