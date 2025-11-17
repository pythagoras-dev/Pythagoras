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
"""

from .._070_protected_code_portals import SimplePreValidatorFn
from .validation_succesful_const import ValidationSuccessFlag


def _at_least_X_CPU_cores_free_check(n: int) -> ValidationSuccessFlag | None:
    """Pass if at least ``n`` logical CPU cores are currently free.

    This is a lightweight runtime check based on a heuristic estimation of
    unused logical CPU capacity (see pth.get_unused_cpu_cores).

    Args:
        n (int): Minimum number of free logical CPU cores required.

    Returns:
        ValidationSuccessFlag | None: VALIDATION_SUCCESSFUL if the estimated
        number of free cores is >= n (within a small 0.1 tolerance);
        otherwise None.

    Notes:
        - The tolerance (0.1) helps account for fluctuations in the estimator.
        - Uses instantaneous/short-horizon metrics; momentary spikes may affect
          the outcome.
    """
    cores = pth.get_unused_cpu_cores()
    if cores >= n - 0.1:
        return pth.VALIDATION_SUCCESSFUL


def unused_cpu(cores: int) -> SimplePreValidatorFn:
    """Create a validator that requires at least the given free CPU cores.

    Args:
        cores (int): Minimum number of free logical CPU cores required (> 0).

    Returns:
        SimplePreValidatorFn: A pre-validator that succeeds only when
        the system has at least ``cores`` free logical CPU cores.

    Raises:
        TypeError: If ``cores`` is not an integer.
        ValueError: If ``cores`` is not greater than 0.
    """
    if not isinstance(cores, int):
        raise TypeError("cores must be an int")
    if cores <= 0:
        raise ValueError("cores must be > 0")
    return SimplePreValidatorFn(_at_least_X_CPU_cores_free_check).fix_kwargs(n=cores)


def _at_least_X_G_RAM_free_check(x: int) -> ValidationSuccessFlag | None:
    """Pass if at least ``x`` GiB of RAM are currently available.

    The check uses pth.get_unused_ram_mb() divided by 1024 to obtain gibibytes
    (GiB) and compares with a small tolerance.

    Args:
        x (int): Minimum amount of free RAM in GiB required.

    Returns:
        ValidationSuccessFlag | None: VALIDATION_SUCCESSFUL if the estimated
        free RAM in GiB is >= x (within a 0.1 tolerance); otherwise None.
    """
    ram = pth.get_unused_ram_mb() / 1024
    if ram >= x - 0.1:
        return pth.VALIDATION_SUCCESSFUL


def unused_ram(Gb: int) -> SimplePreValidatorFn:
    """Create a validator that requires at least the given free RAM (GiB).

    Args:
        Gb (int): Minimum free memory required in GiB (> 0).

    Returns:
        SimplePreValidatorFn: A pre-validator that succeeds only when
        the system has at least ``Gb`` GiB of RAM available.

    Raises:
        TypeError: If ``Gb`` is not an integer.
        ValueError: If ``Gb`` is not greater than 0.
    """
    if not isinstance(Gb, int):
        raise TypeError("Gb must be an int")
    if Gb <= 0:
        raise ValueError("Gb must be > 0")
    return SimplePreValidatorFn(_at_least_X_G_RAM_free_check).fix_kwargs(x=Gb)


def _check_python_package_and_install_if_needed(
        package_name: str) -> ValidationSuccessFlag | None:
    """Ensure a Python package is importable, attempting installation if not.

    This validator tries to import the given package. If import fails, it will
    throttle installation attempts to at most once every 10 minutes per
    (node, package) pair and then invoke pth.install_package(package_name).

    Args:
        package_name (str): The importable package/module name to check.

    Returns:
        ValidationSuccessFlag | None: VALIDATION_SUCCESSFUL if the package is
        already importable or was successfully installed; otherwise None.

    Notes:
        - The function relies on names injected by the portal: ``self`` (the
          validator instance) and ``pth`` (pythagoras package).
        - Throttling key is a tuple of (node_signature, package_name,
          "installation_attempt") stored in portal._config_settings.
        - Installation is performed synchronously and may take time.
    """
    if not isinstance(package_name, str):
        raise TypeError("package_name must be a str")
    import importlib, time
    try:
        importlib.import_module(package_name)
        return pth.VALIDATION_SUCCESSFUL
    except:
        portal = self.portal
        address = (pth.get_node_signature()
                    , package_name
                    , "installation_attempt")
        # allow installation retries every 10 minutes
        if (not address in portal._config_settings
                or portal._config_settings[address] < time.time() - 600):
            portal._config_settings[address] = time.time()
            pth.install_package(package_name)
            return pth.VALIDATION_SUCCESSFUL


def installed_packages(*args) -> list[SimplePreValidatorFn]:
    """Create validators ensuring each named package is available.

    For each provided package name, this returns a SimplePreValidatorFn that
    checks the package is importable and installs it if needed (with throttling).

    Args:
        *args: One or more package names as strings.

    Returns:
        list[SimplePreValidatorFn]: A list of pre-validators, one per package
        name, preserving the original order.

    Raises:
        TypeError: If any of the provided arguments is not a string.
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

    This validator checks whether an environment variable with the specified
    name exists in the current process environment.

    Args:
        name: The name of the environment variable to check.

    Returns:
        VALIDATION_SUCCESSFUL if the environment variable is set
        (regardless of its value); otherwise None.

    Notes:
        - Only the presence of the variable is checked, not its value.
    """
    import os
    if name in os.environ:
        return pth.VALIDATION_SUCCESSFUL
    
def required_environment_variables(*names) -> list[SimplePreValidatorFn]:
    """Create validators ensuring each named environment variable is set.

    For each provided environment variable name, this returns a
    SimplePreValidatorFn that checks the variable exists in the process
    environment.

    Args:
        *names: One or more environment variable names as strings.

    Returns:
        A list of pre-validators, one per environment variable name.

    Raises:
        TypeError: If any of the provided arguments is not a string.
        ValueError: If any of the provided names is not a valid environment variable name.

    Examples:
        To require that both API_KEY and DATABASE_URL are set:

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