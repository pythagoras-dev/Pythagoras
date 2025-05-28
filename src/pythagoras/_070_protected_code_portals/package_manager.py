import subprocess
import importlib
import sys
from typing import Optional

def install_package(package_name:str
        , upgrade:bool=False
        , version:Optional[str]=None
        ) -> None:
    """Install package using pip."""
    command = [sys.executable, "-m", "pip", "install"]

    if upgrade:
        command += ["--upgrade"]

    package_spec = f"{package_name}=={version}" if version else package_name
    command += [package_spec]

    subprocess.run(command, check=True, stdout=subprocess.PIPE
        , stderr=subprocess.STDOUT, text=True)

    importlib.import_module(package_name)

def uninstall_package(package_name:str)->None:
    """Uninstall package using pip."""

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