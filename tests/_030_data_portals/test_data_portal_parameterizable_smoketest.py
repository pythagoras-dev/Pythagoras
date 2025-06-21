from src.pythagoras._030_data_portals import (
    DataPortal)
from src.pythagoras import _PortalTester
from parameterizable import smoketest_parameterizable_class


def test_basic_portal_get_params(tmpdir):
    with _PortalTester(DataPortal, root_dict = tmpdir) as t:
        smoketest_parameterizable_class(DataPortal)

