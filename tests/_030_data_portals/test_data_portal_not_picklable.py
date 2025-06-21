from src.pythagoras._030_data_portals import DataPortal
from src.pythagoras._010_basic_portals import _PortalTester

import pytest

def test_ordinary_code_portal_not_picklable():
    with _PortalTester(DataPortal) as tester:
        portal = tester.portal
        with pytest.raises(TypeError, match="DataPortal cannot be pickled"):
            _ = portal.__getstate__()

        with pytest.raises(TypeError, match="DataPortal cannot be unpickled"):
            portal.__setstate__({"key": "value"})