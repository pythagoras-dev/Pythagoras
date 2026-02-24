"""Classes and functions for guarded execution of code.

Guarded functions execute only when requirements pass before execution
and result checks pass after execution. Requirements can be passive
(e.g., check available RAM) or active (e.g., install missing packages).

Main Exports
------------
- GuardedCodePortal: Portal with requirement/result check hooks.
- GuardedFn: Function wrapper enforcing extension checks.
- guarded: Decorator to create guarded functions.
- ExtensionFn: Base class for all extensions.
- RequirementFn: Base class for pre-execution requirements.
- ResultCheckFn: Base class for post-execution result checks.
- NO_OBJECTIONS: Sentinel indicating a successful check.
- MAX_REQUIREMENT_ITERATIONS: Maximum retry iterations for requirements.

Requirement Factories
---------------------
- unused_cpu: Require minimum free CPU cores.
- unused_ram: Require minimum free RAM.
- installed_packages: Ensure packages are installed.
- required_environment_variables: Require environment variables.
"""

from .no_objections_const import *
from .guarded_portal_core_classes import *
from .guarded_decorators import *
from .system_resources_info_getters import *
from .basic_requirements import *

