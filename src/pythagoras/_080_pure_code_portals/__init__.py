"""Pure functions with persistent result caching and source tracking.

Pure functions are protected autonomous functions with no side effects that
always return the same result for identical arguments. They accept only
keyword arguments and don't depend on external imports or definitions.

Key components:
- @pure() decorator: Marks functions as pure and enables persistent caching
- PureCodePortal: Portal managing execution and caching for pure functions
- PureFn: Wrapped pure function supporting sync/async execution patterns
- PureFnExecutionResultAddr: Address-based retrieval for distributed execution

The @pure() decorator enables persistent caching: when a pure function is
called multiple times with the same arguments, only the first invocation
executes; subsequent calls return the cached result.

Pythagoras tracks source code changes in pure functions. When the
implementation changes, the function re-executes on the next call, but
previously cached results remain available for the old version. Only
source code changes are tracked, not external dependencies.

For recursive functions, use recursive_parameters() to create pre-validators
that optimize execution by ensuring prerequisites are computed
in the correct order.
"""

from .pure_core_classes import *
from .recursion_pre_validator import *
from .pure_decorator import *