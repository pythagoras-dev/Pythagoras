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
from functools import lru_cache
from typing import Optional


def _run(command: list[str], timeout: int = 300) -> None:
    """Execute subprocess command with timeout enforcement.

    Args:
        command: Command and arguments to execute.
        timeout: Maximum execution time in seconds.

    Raises:
        RuntimeError: If command times out or returns non-zero exit code.
    """
    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE
            , stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, text=True
            , timeout=timeout)
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(
            f"Command timed out after {timeout}s: {' '.join(command)}") from e
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Command failed: {' '.join(command)}\n{e.stdout}") from e


@lru_cache(maxsize=1) # ensure only one call to _install_uv_and_pip
def _install_uv_and_pip() -> None:
    """Ensure both uv and pip package managers are available.

    Installs missing package managers using the available one: uv via pip,
    pip via uv. Subsequent calls return immediately due to caching.

    Note:
        This internal helper is called automatically by install_package for
        any package except pip or uv themselves.
    """
    try:
        importlib.import_module("uv")
    except ModuleNotFoundError:
        install_package("uv", use_uv=False)

    try:
        importlib.import_module("pip")
    except ModuleNotFoundError:
        install_package("pip", use_uv=True)


def install_package(package_name: str,
        upgrade: bool = False,
        version: str | None = None,
        use_uv: bool = True,
        import_name: str | None = None,
        verify_import: bool = True
        ) -> None:
    """Install a Python package using uv or pip.

    Installs packages from PyPI using uv (default) or pip as the installer
    frontend. Automatically ensures both tools are available before
    installation. Supports packages with mismatched PyPI and import names.

    Args:
        package_name: PyPI package name. Special constraints apply to pip
            (requires use_uv=True) and uv (requires use_uv=False).
        upgrade: Whether to upgrade if already installed.
        version: Version constraint like "1.2.3" for pinned installation.
        use_uv: Whether to use uv instead of pip as installer.
        import_name: Module name for import verification when it differs
            from package_name (e.g., "PIL" for "Pillow").
        verify_import: Whether to verify package is importable after
            installation. Disable for CLI-only tools.

    Raises:
        ValueError: If package_name or version are invalid, or if attempting
            to install pip with use_uv=False or uv with use_uv=True.
        RuntimeError: If installation command fails.
        ModuleNotFoundError: If verify_import is True and import fails.

    Example:
        >>> install_package("requests")
        >>> install_package("Pillow", import_name="PIL")
        >>> install_package("black", verify_import=False)
    """
    if not package_name or not isinstance(package_name, str):
        raise ValueError("package_name must be a non-empty string")

    if version is not None and not isinstance(version, str):
        raise ValueError("version must be a string")

    if (import_name is not None
            and (not isinstance(import_name, str)
                    or len(import_name)==0)):
        raise ValueError("import_name must be a non-empty string")

    if package_name == "pip" and not use_uv:
        raise ValueError("pip must be installed using uv (use_uv=True)")
    elif package_name == "uv" and use_uv:
        raise ValueError("uv must be installed using pip (use_uv=False)")
    elif package_name not in ("pip", "uv"):
        _install_uv_and_pip()

    if use_uv:
        command = [sys.executable, "-m", "uv", "pip", "install"]
    else:
        command = [sys.executable, "-m", "pip", "install", "--no-input"]

    if upgrade:
        command.append("--upgrade")

    package_spec = f"{package_name}=={version}" if version else package_name
    command.append(package_spec)

    _run(command)

    if verify_import:
        module_to_import = import_name if import_name is not None else package_name
        importlib.import_module(module_to_import)


def uninstall_package(package_name:str, use_uv:bool=True, import_name: str|None = None)->None:
    """Uninstall a Python package using uv or pip.

    Removes packages and verifies they are no longer importable. Protected
    packages (pip, uv) cannot be uninstalled to maintain package management
    capabilities.

    Args:
        package_name: Package to uninstall. Cannot be pip or uv.
        use_uv: Whether to use uv instead of pip as uninstaller.
        import_name: Module name for verification when it differs from
            package_name.

    Raises:
        ValueError: If attempting to uninstall pip or uv.
        RuntimeError: If uninstall command fails or package remains
            importable after uninstallation.
    """

    if package_name in ["pip", "uv"]:
        raise ValueError(f"Cannot uninstall '{package_name}' "
                         "- it's a protected package")

    _install_uv_and_pip()

    if use_uv:
        command = [sys.executable, "-m", "uv", "pip", "uninstall", package_name]
    else:
        command = [sys.executable, "-m", "pip", "uninstall", "-y", package_name]

    _run(command)

    importlib.invalidate_caches()
    module_to_check = import_name if import_name else package_name
    if module_to_check in sys.modules:
        del sys.modules[module_to_check]

    try:
        package = importlib.import_module(module_to_check)
        importlib.reload(package)
        raise RuntimeError(
            f"Package '{package_name}' (module '{module_to_check}') "
            "still importable after uninstallation")
    except ModuleNotFoundError:
        pass



