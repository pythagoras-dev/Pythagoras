"""Utilities to install and uninstall Python packages at runtime.

This module provides a thin wrapper around pip and the uv tool to install
and uninstall packages from within the running Python process.

Key points:
- By default, uv is preferred as the installer frontend (uv pip ...). If uv
  or pip is not available, the module will attempt to install the missing
  tool as needed.
- For safety, uninstall_package refuses to operate on 'pip' or 'uv' directly.
- Calls are synchronous and raise on non-zero exit status.
"""

import subprocess
import importlib
import sys
from typing import Optional

_uv_and_pip_installation_needed:bool = True

def _install_uv_and_pip() -> None:
    """Ensure the 'uv' and 'pip' frontends are available.

    Behavior:
    - If this helper has already run in the current process and determined
      the tools are present, it returns immediately.
    - Tries to import 'uv'; if missing, installs it using system pip
      (use_uv=False).
    - Tries to import 'pip'; if missing, installs it using uv (use_uv=True).

    This function is an internal helper and is called implicitly by
    install_package() for any package other than 'pip' or 'uv'.
    """
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
    """Install a Python package using uv (default) or pip.

    Parameters:
    - package_name: Name of the package to install. Special cases:
      - 'pip': must be installed using uv (use_uv=True).
      - 'uv' : must be installed using pip (use_uv=False).
    - upgrade: If True, pass "--upgrade" to the installer.
    - version: Optional version pin, e.g. "1.2.3". If provided, constructs
      "package_name==version".
    - use_uv: If True, run as `python -m uv pip install ...`; otherwise use pip.

    Behavior:
    - Ensures both uv and pip are available unless installing one of them.
    - Runs the installer in a subprocess with check=True (raises on failure).
    - Imports the package after installation to verify it is importable.

    Raises:
    - subprocess.CalledProcessError: if the installation command fails.
    - AssertionError: if attempting to install pip with use_uv=False or uv with use_uv=True.
    - ModuleNotFoundError: if the package cannot be imported after installation.
    """

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
    """Uninstall a Python package using uv (default) or pip.

    Parameters:
    - package_name: Name of the package to uninstall. Must not be 'pip' or 'uv'.
    - use_uv: If True, run `python -m uv pip uninstall <name>`; otherwise use pip with "-y".

    Behavior:
    - Runs the uninstaller in a subprocess with check=True.
    - Attempts to import and reload the package after uninstallation. If that
      succeeds, raises an Exception to indicate the package still appears installed.

    Raises:
    - AssertionError: if package_name is 'pip' or 'uv'.
    - subprocess.CalledProcessError: if the uninstall command fails.
    - Exception: if post-uninstall validation indicates the package is still importable.
    """

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