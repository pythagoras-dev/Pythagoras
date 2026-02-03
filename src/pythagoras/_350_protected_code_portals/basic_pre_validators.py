"""Basic pre-validation utilities for protected code portals.

This module contains small, composable validators used by protected portals
before executing user functions. Each public factory returns a
SimplePreValidatorFn configured with fixed arguments, so validators can be
attached declaratively to protected functions.

Execution context:
- When executed by a portal, validator functions run with two names injected
  into their global namespace: `self` (the ValidatorFn instance) and `pth`
  (the pythagoras package). This allows them to access portal services such as
  system introspection and package management.

Conventions:
- Return ValidationSuccessFlag (VALIDATION_SUCCESSFUL) to indicate the check
  passed; return None to indicate the check did not pass.
  Do NOT return True/False, 1/0, strings, or other truthy/falsy values. These
  are treated as validation FAILURE, not success. Only VALIDATION_SUCCESSFUL
  (the sentinel singleton) indicates success. The validation check uses
  identity comparison (``is VALIDATION_SUCCESSFUL``), not truthiness.
"""

from typing import TYPE_CHECKING

from .._350_protected_code_portals import SimplePreValidatorFn
from .validation_succesful_const import ValidationSuccessFlag

# The validator functions below use `pth` and `self` which are injected into
# their global namespace at runtime by the portal framework (see module docstring).
# These TYPE_CHECKING declarations make the names visible to static analysis tools
# (ruff, mypy, IDEs) without importing anything at runtime.
if TYPE_CHECKING:
    import pythagoras as pth
    self = None


def _at_least_X_CPU_cores_free_check(n: int) -> ValidationSuccessFlag | None:
    """Pass if at least the specified logical CPU cores are currently free.

    Args:
        n: Minimum number of free logical CPU cores required.

    Returns:
        VALIDATION_SUCCESSFUL if estimated free cores >= n (within 0.1
        tolerance); otherwise None.

    Note:
        Uses instantaneous metrics; momentary spikes may affect the outcome.
    """
    cores = pth.get_unused_cpu_cores()
    if cores >= n - 0.1:
        return pth.VALIDATION_SUCCESSFUL


def unused_cpu(cores: int) -> SimplePreValidatorFn:
    """Create a validator that requires at least the given free CPU cores.

    Args:
        cores: Minimum number of free logical CPU cores required (must be > 0).

    Returns:
        A pre-validator that succeeds only when the system has at least
        the specified free logical CPU cores.

    Raises:
        TypeError: If cores is not an integer.
        ValueError: If cores is not greater than 0.
    """
    if isinstance(cores, bool) or not isinstance(cores, int):
        raise TypeError("cores must be an int")
    if cores <= 0:
        raise ValueError("cores must be > 0")
    return SimplePreValidatorFn(_at_least_X_CPU_cores_free_check).fix_kwargs(n=cores)


def _at_least_X_G_RAM_free_check(x: int) -> ValidationSuccessFlag | None:
    """Pass if at least the specified GiB of RAM are currently available.

    Args:
        x: Minimum amount of free RAM in GiB required.

    Returns:
        VALIDATION_SUCCESSFUL if estimated free RAM >= x (within 0.1
        tolerance); otherwise None.
    """
    ram = pth.get_unused_ram_mb() / 1024
    if ram >= x - 0.1:
        return pth.VALIDATION_SUCCESSFUL


def unused_ram(Gb: int) -> SimplePreValidatorFn:
    """Create a validator that requires at least the given free RAM (GiB).

    Args:
        Gb: Minimum free memory required in GiB (must be > 0).

    Returns:
        A pre-validator that succeeds only when the system has at least
        the specified GiB of RAM available.

    Raises:
        TypeError: If Gb is not an integer.
        ValueError: If Gb is not greater than 0.
    """
    if isinstance(Gb, bool) or not isinstance(Gb, int):
        raise TypeError("Gb must be an int")
    if Gb <= 0:
        raise ValueError("Gb must be > 0")
    return SimplePreValidatorFn(_at_least_X_G_RAM_free_check).fix_kwargs(x=Gb)


def _check_python_package_and_install_if_needed(
        package_name: str) -> ValidationSuccessFlag | None:
    """Ensure a Python package is importable, attempting installation if not.

    Tries to import the package. If import fails, attempts installation with
    throttling (at most once every 10 minutes per node and package).

    Args:
        package_name: The importable package/module name to check.

    Returns:
        VALIDATION_SUCCESSFUL if the package is already importable or was
        successfully installed; otherwise None.

    Note:
        Assumes package names and import names are the same.
    """
    if not isinstance(package_name, str):
        raise TypeError("package_name must be a str")
    import importlib
    import time
    try:
        importlib.import_module(package_name)
        return pth.VALIDATION_SUCCESSFUL
    except Exception:
        portal = self.portal
        address = ("installation_attempts", package_name)
        # allow installation retries every 10 minutes
        if (address not in portal.local_node_value_store
                or portal.local_node_value_store[address] < time.time() - 600):
            portal.local_node_value_store[address] = time.time()
            pth.install_package(package_name)
            if pth.is_package_installed(package_name):
                return pth.VALIDATION_SUCCESSFUL
            return None


def installed_packages(*args) -> list[SimplePreValidatorFn]:
    """Create validators ensuring each named package is available.

    Args:
        *args: One or more package names as strings.

    Returns:
        A list of pre-validators, one per package name, preserving order.

    Raises:
        TypeError: If any argument is not a string.

    Note:
        Assumes package names and import names are the same.
    """
    validators = []
    for package_name in args:
        if not isinstance(package_name, str):
            raise TypeError("All package names must be strings")
        # TODO: check if the package is available on pypi.org
        new_validator = SimplePreValidatorFn(_check_python_package_and_install_if_needed)
        new_validator = new_validator.fix_kwargs(package_name=package_name)
        validators.append(new_validator)
    return validators


def _environment_variable_availability_check(name: str) -> ValidationSuccessFlag | None:
    """Pass if the given environment variable is set.

    Args:
        name: The name of the environment variable to check.

    Returns:
        VALIDATION_SUCCESSFUL if the environment variable is set
        (regardless of its value); otherwise None.
    """
    import os
    if name in os.environ:
        return pth.VALIDATION_SUCCESSFUL
    
def required_environment_variables(*names) -> list[SimplePreValidatorFn]:
    """Create validators ensuring each named environment variable is set.

    Args:
        *names: One or more environment variable names as strings.

    Returns:
        A list of pre-validators, one per environment variable name.

    Raises:
        TypeError: If any argument is not a string.
        ValueError: If any name is empty or contains invalid characters.

    Example:
        >>> validators = required_environment_variables("API_KEY", "DATABASE_URL")
    """

    for name in names:
        if not isinstance(name, str):
            raise TypeError("All environment variable names must be strings")
        if len(name)==0:
            raise ValueError("Environment variable name cannot be empty")
        if not all(c.isalnum() or c == '_' for c in name):
            raise ValueError(f"Environment variable name '{name}' "
                f"can only contain letters, numbers, and underscores")

    validators = []
    for name in names:
        new_validator = SimplePreValidatorFn(_environment_variable_availability_check)
        new_validator = new_validator.fix_kwargs(name=name)
        validators.append(new_validator)
    return validators