import pytest

from pythagoras import pure, installed_packages, _PortalTester, PureCodePortal, unused_ram
from pythagoras._070_protected_code_portals.package_manager import *

@pure(pre_validators = [unused_ram(Gb=1)] )
def very_easy_ram_testing_function():
    pass

def test_easy_ram_requirements(tmpdir):
    with _PortalTester(PureCodePortal,tmpdir):
        very_easy_ram_testing_function()


@pure(pre_validators=[unused_ram(Gb=500)])
def very_unrealistic_ram_needs():
    pass


def test_polars_package(tmpdir):

    with _PortalTester(PureCodePortal, tmpdir):

        with pytest.raises(Exception):
            very_unrealistic_ram_needs()