"""Classes and utilities for ordinary functions in Pythagoras.

An ordinary function is a regular Python function with strict constraints
that enable reliable introspection, comparison, and isolated execution:
- Accepts only named (keyword) arguments
- No default parameter values
- No closures or captured state
- Not a method, lambda, async function, or builtin

Ordinary functions are the foundation of the Pythagoras execution model.
To use a function in Pythagoras, apply the @ordinary decorator to convert
it into an OrdinaryFn wrapper.

Key Concepts
------------
**Normalization**: Function source code is transformed into canonical form
by removing decorators, docstrings, comments, and type annotations, then
applying consistent PEP8 formatting. This enables reliable comparison and hashing
for caching and distributed execution.

**Execution Model**: OrdinaryFn instances execute in controlled namespaces
with only explicitly allowed symbols, providing isolation from caller context
and ensuring reproducibility.

**Decorator Constraints**: Ordinary functions may only use Pythagoras
decorators (@ordinary, @pure, etc.). External decorators are not allowed.

Main Exports
------------
- OrdinaryCodePortal: Portal for managing ordinary function lifecycle.
- OrdinaryFn: Wrapper class for ordinary functions with normalized execution.
- ordinary: Decorator to convert functions into OrdinaryFn instances.
- FunctionError: Exception raised when a function violates ordinarity rules.
- get_normalized_fn_source_code_str: Utility to get normalized source code.

Usage Note
----------
Most users work with higher-level abstractions (pure functions) built on
OrdinaryFn. Direct use of this module is for framework extension
and advanced customization.
"""

from .ordinary_portal_core_classes import *
from .reuse_flag import *
from .function_processing import *
from .ordinary_decorator import *
from .code_normalizer import *
from .function_error_exception import *


