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
from .._110_supporting_utilities import is_valid_env_name

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
    if pth.is_package_installed(package_name):
        return pth.VALIDATION_SUCCESSFUL

    import importlib
    import os
    import random
    import time

    LOCK_KEY_PREFIX = "package_install_lock"
    LOCK_WAIT_SECONDS = 60.0
    LOCK_TTL_SECONDS = 300.0
    LOCK_SLEEP_MIN = 0.05
    LOCK_SLEEP_MAX = 0.15
    RETRY_WINDOW_SECONDS = 600.0

    def _lock_key(name: str) -> tuple[str, str]:
        return (LOCK_KEY_PREFIX, name)

    def _get_lock_info(portal, name: str) -> dict | None:
        lock_info = portal.local_node_value_store.get(_lock_key(name), None)
        return lock_info if isinstance(lock_info, dict) else None

    def _best_effort_uninstall(name: str) -> None:
        try:
            pth.uninstall_package(name, verify_uninstall=False)
        except Exception:
            pass

    def _clear_install_attempt(portal, key) -> None:
        try:
            portal.local_node_value_store.delete_if_exists(key)
        except Exception:
            pass

    def _acquire_package_install_lock(
            portal,
            name: str,
            *,
            wait_seconds: float = LOCK_WAIT_SECONDS,
            ttl_seconds: float = LOCK_TTL_SECONDS,
            min_sleep: float = LOCK_SLEEP_MIN,
            max_sleep: float = LOCK_SLEEP_MAX,
    ) -> str | None:
        """Best-effort lock using local_node_value_store only."""
        key = _lock_key(name)
        token = f"{os.getpid()}-{time.time()}-{random.random()}"
        deadline = time.time() + wait_seconds

        while time.time() < deadline:
            now = time.time()
            lock_info = _get_lock_info(portal, name)
            if lock_info is None or lock_info.get("expires_at", 0) < now:
                portal.local_node_value_store[key] = {
                    "token": token,
                    "pid": os.getpid(),
                    "acquired_at": now,
                    "expires_at": now + ttl_seconds,
                }
                confirmed = portal.local_node_value_store.get(key, None)
                if confirmed and confirmed.get("token") == token:
                    return token

            time.sleep(min_sleep + random.random() * (max_sleep - min_sleep))

        return None

    def _release_package_install_lock(portal, name: str, token: str | None) -> None:
        """Release a best-effort lock stored in local_node_value_store."""
        if token is None:
            return
        key = _lock_key(name)
        lock_info = _get_lock_info(portal, name)
        if isinstance(lock_info, dict) and lock_info.get("token") == token:
            portal.local_node_value_store.delete_if_exists(key)

    def _refresh_package_install_lock(
            portal, name: str, token: str | None, ttl_seconds: float = LOCK_TTL_SECONDS
    ) -> None:
        """Extend lock TTL if the token still owns it."""
        if token is None:
            return
        key = _lock_key(name)
        lock_info = _get_lock_info(portal, name)
        if isinstance(lock_info, dict) and lock_info.get("token") == token:
            updated = dict(lock_info)
            updated["expires_at"] = time.time() + ttl_seconds
            portal.local_node_value_store[key] = updated

    def _install_and_verify(name: str) -> bool:
        try:
            pth.install_package(name)
        except Exception:
            _best_effort_uninstall(name)
            return False
        if pth.is_package_installed(name):
            return True
        _best_effort_uninstall(name)
        return False

    portal = self.portal
    address = ("installation_attempts", package_name)
    # allow installation retries every 10 minutes
    lock_token = _acquire_package_install_lock(portal, package_name)
    try:
        if lock_token is None:
            return None
        # is_package_installed now verifies importability.
        if pth.is_package_installed(package_name):
            return pth.VALIDATION_SUCCESSFUL
        spec_exists = importlib.util.find_spec(package_name) is not None
        can_attempt_install = (
            address not in portal.local_node_value_store
            or portal.local_node_value_store[address] < time.time() - RETRY_WINDOW_SECONDS
        )
        if spec_exists:
            _best_effort_uninstall(package_name)
            _clear_install_attempt(portal, address)
            can_attempt_install = True
        if not can_attempt_install:
            return None
        portal.local_node_value_store[address] = time.time()
        _refresh_package_install_lock(portal, package_name, lock_token)
        if _install_and_verify(package_name):
            return pth.VALIDATION_SUCCESSFUL
        return None
    finally:
        _release_package_install_lock(portal, package_name, lock_token)

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
        if not is_valid_env_name(name):
            raise ValueError(f"Environment variable name '{name}' "
                "is not a valid environment variable name.")

    validators = []
    for name in names:
        new_validator = SimplePreValidatorFn(_environment_variable_availability_check)
        new_validator = new_validator.fix_kwargs(name=name)
        validators.append(new_validator)
    return validators
