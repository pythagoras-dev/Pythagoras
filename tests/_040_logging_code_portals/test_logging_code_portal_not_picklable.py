from pythagoras._040_logging_code_portals import LoggingCodePortal
from pythagoras._010_basic_portals import _PortalTester

import pytest

def test_ordinary_code_portal_not_picklable():
    with _PortalTester(LoggingCodePortal) as tester:
        portal = tester.portal
        with pytest.raises(TypeError, match="LoggingCodePortal cannot be pickled"):
            _ = portal.__getstate__()

        with pytest.raises(TypeError, match="LoggingCodePortal cannot be unpickled"):
            portal.__setstate__({"key": "value"})