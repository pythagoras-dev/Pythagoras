import parameterizable

from pythagoras import _PortalTester, DataPortal, LoggingCodePortal, SafeCodePortal, AutonomousCodePortal


def test_portal(tmpdir):
    the_dir = tmpdir
    with _PortalTester():

        portal1 = AutonomousCodePortal(tmpdir.mkdir("edede"))
        portal1_params = portal1.get_params()
        portal1_params_json = parameterizable.dumps(portal1)

        portal2 = parameterizable.loads(portal1_params_json)
        portal2_params = portal2.get_params()
        portal1_params_json2 = parameterizable.dumps(portal2)

        assert portal1_params == portal2_params
        assert portal1_params_json == portal1_params_json2
    