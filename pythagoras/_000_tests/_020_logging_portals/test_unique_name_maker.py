from pythagoras._010_basic_portals.portal_tester import _PortalTester
from pythagoras._020_logging_portals.logging_portals import (
    LoggingPortal)

def test_unique_name_maker(tmpdir):
    with _PortalTester(LoggingPortal, tmpdir) as p:
        name = LoggingPortal.make_unique_name(
            desired_name="test",existing_names = ["a","b"])
        assert name == "test"

        name = LoggingPortal.make_unique_name(
            desired_name="test",existing_names = ["a","b","test"])
        assert name.startswith("test_")
        assert name != "test"
