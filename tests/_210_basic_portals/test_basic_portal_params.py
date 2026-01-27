"""Tests for BasicPortal parameter serialization via mixinforge."""
import mixinforge

from pythagoras import _PortalTester, BasicPortal


def test_portal(tmpdir):
    """Verify portal parameters serialize and deserialize correctly."""
    with _PortalTester():

        portal1 = BasicPortal(tmpdir.mkdir("awer"))
        portal1_params = portal1.get_params()
        portal1_params_json = mixinforge.dumpjs(portal1)

        portal2 = mixinforge.loadjs(portal1_params_json)
        portal2_params = portal2.get_params()
        portal1_params_json2 = mixinforge.dumpjs(portal2)

        assert portal1_params == portal2_params
        assert portal1_params_json == portal1_params_json2
