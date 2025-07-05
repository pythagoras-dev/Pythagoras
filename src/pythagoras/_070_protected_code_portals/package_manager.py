import subprocess
import importlib
import sys
from typing import Optional

_uv_and_pip_installation_needed:bool = True

def _install_uv_and_pip() -> None:
    global _uv_and_pip_installation_needed
    if not _uv_and_pip_installation_needed:
        return

    try:
        importlib.import_module("uv")
    except:
        install_package("uv", use_uv=False)

    try:
        importlib.import_module("pip")
    except:
        install_package("pip", use_uv=True)


def install_package(package_name:str
        , upgrade:bool=False
        , version:Optional[str]=None
        , use_uv:bool = True
        ) -> None:
    """Install package using pip."""

    if package_name == "pip":
        assert use_uv
    elif package_name == "uv":
        assert not use_uv
    else:
        _install_uv_and_pip()

    if use_uv:
        command = [sys.executable, "-m", "uv", "pip", "install"]
    else:
        command = [sys.executable, "-m", "pip", "install"]

    if upgrade:
        command += ["--upgrade"]

    package_spec = f"{package_name}=={version}" if version else package_name
    command += [package_spec]

    subprocess.run(command, check=True, stdout=subprocess.PIPE
        , stderr=subprocess.STDOUT, text=True)

    importlib.import_module(package_name)


def uninstall_package(package_name:str, use_uv:bool=True)->None:
    """Uninstall package using uv or pip."""

    assert package_name not in ["pip", "uv"]

    if use_uv:
        command = [sys.executable, "-m", "uv", "pip", "uninstall", package_name]
    else:
        command = [sys.executable, "-m", "pip", "uninstall", "-y", package_name]

    subprocess.run(command, check=True, stdout=subprocess.PIPE
        , stderr=subprocess.STDOUT, text=True)

    try:
        package = importlib.import_module(package_name)
        importlib.reload(package)
    except:
        pass
    else:
        raise Exception(
            f"Failed to validate package uninstallation for '{package_name}'. ")