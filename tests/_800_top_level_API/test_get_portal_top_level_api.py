
from pythagoras.core import get_portal
from pythagoras import SwarmingPortal, _PortalTester


def test_get_portal(tmpdir):
    with _PortalTester():
        tmpdir = str(tmpdir)
        portal = get_portal(tmpdir)
        assert isinstance(portal, SwarmingPortal)