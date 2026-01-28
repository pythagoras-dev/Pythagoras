from pythagoras._210_basic_portals.portal_tester import _PortalTester
from pythagoras._320_logging_code_portals import (
    LoggingCodePortal,make_unique_name)

def test_unique_name_maker(tmpdir):
    with _PortalTester(LoggingCodePortal, tmpdir):
        name = make_unique_name(
            suggested_name="test",existing_names = ["a", "b"])
        assert name == "test"

        name = make_unique_name(
            suggested_name="test",existing_names = ["a", "b", "test"])
        assert name.startswith("test_")
        assert name != "test"
