from src.pythagoras._040_logging_code_portals import LoggingCodePortal
from src.pythagoras import _PortalTester
from parameterizable import smoketest_parameterizable_class


def test_basic_portal_get_params(tmpdir):
    with _PortalTester(LoggingCodePortal, root_dict = tmpdir) :
        smoketest_parameterizable_class(LoggingCodePortal)

