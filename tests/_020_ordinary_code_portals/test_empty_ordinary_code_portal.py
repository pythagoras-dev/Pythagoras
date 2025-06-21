from persidict import PersiDict

from src.pythagoras import OrdinaryCodePortal
from src.pythagoras._010_basic_portals.portal_tester import _PortalTester

def test_empty_ordinary_code_portal(tmpdir):
    with _PortalTester(OrdinaryCodePortal, tmpdir) as p:
        assert isinstance(p.portal._root_dict, PersiDict)
        assert p.portal.number_of_linked_functions() == 0
        assert p.portal.number_of_linked_objects() == 0

