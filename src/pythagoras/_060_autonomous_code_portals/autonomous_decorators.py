"""Support for work with autonomous functions.

In essence, an 'autonomous' function contains self-sufficient code
that does not depend on external imports or definitions. All required
imports should be done inside the function body.
Only ordinary functions can be autonomous.

Autonomous functions are always allowed to use the built-in objects
(functions, types, variables), as well as global objects,
explicitly imported inside the function body. An autonomous function
is allowed to use other autonomous functions if they are passed as
input arguments to the function.

Autonomous functions are not allowed to:

    * use global objects, imported or defined outside the function body
      (except built-in objects);
    * use yield (yield from) statements;
    * use nonlocal variables, referencing the outside objects.

Autonomous functions can have nested functions and classes.

Only ordinary functions can be autonomous. Asynchronous functions, closures,
class methods, and lambda functions cannot be autonomous.

An autonomous function can only be called with keyword arguments.
It can't be called with positional arguments.

Autonomous functions support partial application of arguments:
the process of pre-filling some arguments of a function,
producing a new autonomous function that takes the remaining arguments.

This module defines a decorator which is used to
inform Pythagoras that a function is intended to be autonomous
and to enforce autonomicity requirements.

Applying a decorator to a function ensures both static and runtime autonomicity
checks are performed for the function. Static checks happen at the time
of decoration, while runtime checks happen at the time of function execution.
"""
from typing import Callable

from .._050_safe_code_portals import safe
from .autonomous_portal_core_classes import AutonomousFn, AutonomousCodePortal
from persidict import Joker, KEEP_CURRENT


class autonomous(safe):
    """Decorator that turns a regular function into an autonomous one.

    An autonomous function is a self-contained function: it
    can only use built-ins and any names it imports inside its own body. This
    decorator wraps the target callable into an AutonomousFn and enforces both
    static and runtime autonomy checks via the selected portal.

    Notes:
        - Only regular (non-async) functions are supported.
        - Methods, closures, lambdas, and coroutines are not considered autonomous.
    """
    _fixed_args: dict|None

    def __init__(self
                 , fixed_kwargs: dict | None = None
                 , excessive_logging: bool|Joker = KEEP_CURRENT
                 , portal: AutonomousCodePortal | None = None
                 ):
        """Initialize the decorator.

        Args:
            fixed_kwargs: Keyword arguments to pre-bind (partially apply) to the
                decorated function. These will be merged into every call.
            excessive_logging: If True, enables verbose logging within the
                selected portal. KEEP_CURRENT leaves the portal's setting as-is.
            portal: Portal instance to use for autonomy and safety checks.

        Raises:
            TypeError: If portal is not an AutonomousCodePortal or None, or
                if fixed_kwargs is not a dict or None.
        """
        if not (isinstance(portal, AutonomousCodePortal) or portal is None):
            raise TypeError(f"portal must be an AutonomousCodePortal or None, got {type(portal).__name__}")
        if not (isinstance(fixed_kwargs, dict) or fixed_kwargs is None):
            raise TypeError(f"fixed_kwargs must be a dict or None, got {type(fixed_kwargs).__name__}")
        safe.__init__(self=self
            , portal=portal
            , excessive_logging=excessive_logging)
        self._fixed_kwargs = fixed_kwargs


    def __call__(self, fn: Callable|str) -> AutonomousFn:
        """Wrap the function with autonomy enforcement.

        Args:
            fn: The function object to decorate.

        Returns:
            AutonomousFn: A wrapper that enforces autonomy at decoration and at
            execution time, with any fixed keyword arguments pre-applied.
        """
        wrapper = AutonomousFn(fn
            ,portal=self._portal
            ,fixed_kwargs=self._fixed_kwargs
            ,excessive_logging=self._excessive_logging)
        return wrapper