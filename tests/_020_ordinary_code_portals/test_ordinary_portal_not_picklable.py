from pythagoras._020_ordinary_code_portals import OrdinaryCodePortal
from pythagoras._010_basic_portals import _PortalTester

import pytest

def test_ordinary_code_portal_not_picklable():
    with _PortalTester(OrdinaryCodePortal) as tester:
        portal = tester.portal
        with pytest.raises(TypeError, match="OrdinaryCodePortal cannot be pickled"):
            _ = portal.__getstate__()

        with pytest.raises(TypeError, match="OrdinaryCodePortal cannot be unpickled"):
            portal.__setstate__({"key": "value"})