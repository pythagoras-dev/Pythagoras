"""Pure functions with persistent result caching and source tracking.

Pure functions are deterministic and side-effect-free. They accept only
keyword arguments. The @pure() decorator enables persistent caching: repeated
calls with the same arguments return the cached result without re-execution.

Pythagoras tracks source code changes in pure functions. When the
implementation changes, the function re-executes on the next call, but
previously cached results remain available for the old version.

Main Exports
------------
- PureCodePortal: Portal managing execution and caching for pure functions.
- PureFn: Wrapped pure function with caching and address-based retrieval.
- PureFnExecutionResultAddr: Address uniquely identifying a cached result.
- pure: Decorator to create pure functions.

Utilities
---------
- recursive_parameters: Build pre-validators for recursive pure functions.
"""

from .pure_core_classes import *
from .recursion_pre_validator import *
from .pure_decorator import *