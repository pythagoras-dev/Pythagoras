"""Tests verifying BasicPortal cannot be pickled."""
from pythagoras._210_basic_portals import BasicPortal
from pythagoras._210_basic_portals import _PortalTester

import pytest


def test_basic_portal_not_picklable():
    """Verify BasicPortal raises TypeError on pickle operations."""
    with _PortalTester(BasicPortal) as tester:
        portal = tester.portal
        with pytest.raises(TypeError, match="BasicPortal cannot be pickled"):
            _ = portal.__getstate__()

        with pytest.raises(TypeError, match="BasicPortal cannot be unpickled"):
            portal.__setstate__({"key": "value"})