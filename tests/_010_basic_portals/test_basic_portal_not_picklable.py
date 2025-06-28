from pythagoras._010_basic_portals import BasicPortal
from pythagoras._010_basic_portals import _PortalTester

import pytest

def test_basic_portal_not_picklable():
    with _PortalTester(BasicPortal) as tester:
        portal = tester.portal
        with pytest.raises(TypeError, match="BasicPortal cannot be pickled"):
            _ = portal.__getstate__()

        with pytest.raises(TypeError, match="BasicPortal cannot be unpickled"):
            portal.__setstate__({"key": "value"})