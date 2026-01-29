
import pytest

from pythagoras import pure, installed_packages, _PortalTester, PureCodePortal
from pythagoras._350_protected_code_portals.package_manager import *


@pure(pre_validators=installed_packages("polars"))
def very_nothing_function_with_polars():
    print()


def test_polars_package(tmpdir):
    """Test if package installer installs a package.
    """
    with _PortalTester(PureCodePortal, tmpdir+"qrtr"):
        polars_package_name = "polars"

        uninstall_package(polars_package_name)

        with pytest.raises(Exception):
            package = importlib.import_module(polars_package_name)
            importlib.reload(package)

        very_nothing_function_with_polars()

        package = importlib.import_module(polars_package_name)
        importlib.reload(package)

        uninstall_package(polars_package_name)

        with pytest.raises((ImportError, ModuleNotFoundError)):
            importlib.reload(package)