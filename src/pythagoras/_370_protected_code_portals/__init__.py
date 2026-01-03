"""Classes and functions for protected execution of code.

Protected functions execute only when pre-validators pass before execution
and post-validators pass after execution. Validators can be passive
(e.g., check available RAM) or active (e.g., install missing packages).

Main Exports
------------
- ProtectedCodePortal: Portal with pre/post validation hooks.
- ProtectedFn: Function wrapper enforcing validator checks.
- protected: Decorator to create protected functions.
- ValidatorFn: Base class for all validators.
- PreValidatorFn: Base class for pre-execution validators.
- PostValidatorFn: Base class for post-execution validators.
- VALIDATION_SUCCESSFUL: Sentinel indicating successful validation.

Pre-validator Factories
-----------------------
- unused_cpu: Require minimum free CPU cores.
- unused_ram: Require minimum free RAM.
- installed_packages: Ensure packages are installed.
- required_environment_variables: Require environment variables.
"""

from .validation_succesful_const import *
from .protected_portal_core_classes import *
from .protected_decorators import *
from .system_resources_info_getters import *
from .basic_pre_validators import *
from .package_manager import *
