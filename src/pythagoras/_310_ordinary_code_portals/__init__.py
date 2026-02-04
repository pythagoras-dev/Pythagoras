"""Ordinary function wrappers, portals, and normalization helpers.

Ordinary functions are regular Python callables with strict constraints that
make them easy to normalize, compare, and execute in isolation:

- Accept keyword arguments only
- Define no default parameter values
- Avoid closures, async definitions, lambdas, and methods
- Use only Pythagoras decorators

Normalization removes decorators, docstrings, comments, and type annotations,
then applies PEP 8 formatting to produce stable source for hashing and
comparison.

Most users work with higher-level abstractions built on OrdinaryFn. Use these
utilities when extending the framework or controlling execution contexts
directly.
"""

from .ordinary_portal_core_classes import *
from .reuse_flag import *
from .function_processing import *
from .ordinary_decorator import *
from .code_normalizer import *
from .function_error_exception import *

