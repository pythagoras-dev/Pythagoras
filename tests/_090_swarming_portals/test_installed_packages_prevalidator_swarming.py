from time import sleep

import pytest

from pythagoras import pure, installed_packages, _PortalTester, SwarmingPortal
from pythagoras._070_protected_code_portals.package_manager import *
from pythagoras.core import get


@pure(pre_validators=installed_packages("polars"))
def very_nothing_swarming_function_with_polars(n:int, m:int):
    print()


def test_polars_package(tmpdir):
    """Test if package installer installs a package.
    """

    with _PortalTester(SwarmingPortal, tmpdir+"qrtr") as t:
        polars_package_name = "polars"

        uninstall_package(polars_package_name, use_uv=False)
        uninstall_package(polars_package_name, use_uv=False)

        with pytest.raises(Exception):
            package = importlib.import_module(polars_package_name)
            importlib.reload(package)

        res = very_nothing_swarming_function_with_polars.swarm(n=1, m=1)
        get(res)

        package = importlib.import_module(polars_package_name)
        importlib.reload(package)

        uninstall_package(polars_package_name, use_uv=False)

        with pytest.raises(ModuleNotFoundError):
            importlib.reload(package)