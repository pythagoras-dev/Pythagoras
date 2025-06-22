from src.pythagoras._010_basic_portals.basic_portal_core_classes import (
    BasicPortal)
from src.pythagoras import _PortalTester
from parameterizable import smoketest_parameterizable_class


def test_basic_portal_get_params(tmpdir):
    with _PortalTester(BasicPortal, root_dict = tmpdir) as t:
        smoketest_parameterizable_class(BasicPortal)

