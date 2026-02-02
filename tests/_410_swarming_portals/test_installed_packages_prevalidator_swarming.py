
import pytest

from pythagoras import pure, installed_packages, _PortalTester, SwarmingPortal
from mixinforge import uninstall_package, is_package_installed
import importlib
from pythagoras.core import get


@pure(pre_validators=installed_packages("polars"))
def very_nothing_swarming_function_with_polars(n:int, m:int):
    print()


def test_polars_package(tmpdir):
    """Test if package installer installs a package.
    """

    with _PortalTester(SwarmingPortal, tmpdir+"qrtr"):
        polars_package_name = "polars"

        uninstall_package(polars_package_name)

        assert not is_package_installed(polars_package_name)

        res = very_nothing_swarming_function_with_polars.swarm(n=1, m=1)
        get(res)

        assert is_package_installed(polars_package_name)

        uninstall_package(polars_package_name)

        assert not is_package_installed(polars_package_name)