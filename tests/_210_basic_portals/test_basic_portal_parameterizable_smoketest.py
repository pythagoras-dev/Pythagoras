"""Smoke test for BasicPortal ImmutableParameterizableMixin integration."""
from pythagoras import BasicPortal, _PortalTester
from mixinforge import ImmutableParameterizableMixin


def test_basic_portal_get_params(tmpdir):
    """Verify BasicPortal implements get_params correctly."""
    with _PortalTester(BasicPortal, root_dict = str(tmpdir)) as t:
        portal = t.portal
        assert isinstance(portal, ImmutableParameterizableMixin)
        params = portal.get_params()
        assert "root_dict" in params

