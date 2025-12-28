"""Classes and utilities to work with ordinary functions.

An 'ordinary' function is a regular Python function with strict constraints
that enable reliable introspection, comparison, and isolated execution:
- Accepts only named (keyword) arguments
- No default parameter values
- No closures or captured state
- Not a method, lambda, async function, or builtin

Ordinary functions are the foundation of the Pythagoras execution model.
To be used in Pythagoras, an ordinary function must be converted into an
OrdinaryFn object by applying the @ordinary decorator.

Key Concepts
------------
**Normalization**: Pythagoras transforms function source code into canonical
form by removing decorators, docstrings, comments, and type annotations, then
applying PEP8 formatting. This enables reliable comparison and hashing for
caching and memoization.

**Execution Model**: OrdinaryFn instances execute in controlled namespaces
with only explicitly allowed symbols. This provides isolation from caller
context, enables portal-based tracking, and ensures reproducibility.

**Decorator Constraints**: Ordinary functions may only have Pythagoras
decorators (@ordinary, @autonomous, @protected, @pure, etc.). External
decorators are not allowed to maintain source code predictability.

Main Exports
------------
- OrdinaryFn: Wrapper class for ordinary functions with normalized execution
- OrdinaryCodePortal: Portal subclass for managing ordinary function lifecycle
- ordinary: Decorator to convert functions into OrdinaryFn instances
- get_normalized_function_source: Utility to normalize function source code
- FunctionError: Exception for ordinarity constraint violations

Usage Note
----------
Most Pythagoras users work with higher-level abstractions (autonomous and
pure functions) built on top of OrdinaryFn. Direct use of this module is
primarily for framework extension and advanced customization.
"""

from .ordinary_portal_core_classes import *
from .function_processing import *
from .ordinary_decorator import *
from .code_normalizer import *
from .function_error_exception import *


