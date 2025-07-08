import random
import string
import pytest

from pythagoras._070_protected_code_portals.package_manager import *


def test_actual_package():
    """Test if package installer installs a package.
    """
    actual_package_name = "nothing"

    uninstall_package(actual_package_name, use_uv=False)
    uninstall_package(actual_package_name, use_uv=False)

    install_package(actual_package_name, use_uv=False)
    install_package(actual_package_name, use_uv=False)

    package = importlib.import_module(actual_package_name)
    importlib.reload(package)

    uninstall_package(actual_package_name, use_uv=False)

    with pytest.raises(ModuleNotFoundError):
        importlib.reload(package)


def test_nonexisting_package():
    """Test if package installer throws an exception for nonexistent packages.
    """

    nonexisting_package_name = ""
    for i in range(20):
        nonexisting_package_name += random.choice(string.ascii_letters)
        nonexisting_package_name += random.choice(string.digits)

    with pytest.raises(Exception):
        install_package(nonexisting_package_name, use_uv=False)

    uninstall_package(nonexisting_package_name, use_uv=False)