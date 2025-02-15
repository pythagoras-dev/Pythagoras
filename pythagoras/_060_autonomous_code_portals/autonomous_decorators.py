"""Support for work with autonomous functions.

In an essence, an autonomous function contains self-sufficient code
that does not depend on external imports or definitions.

Autonomous functions are always allowed to use the built-in objects
(functions, types, variables), as well as global objects,
explicitly imported inside the function body. An autonomous function
may be allowed to use other autonomous functions, which are created or imported
outside the autonomous function, provided that they belong to the same island.

Autonomous functions are not allowed to:
    * use global objects, imported or defined outside the function body
      (except built-in objects and, possibly,
      other autonomous functions from the same island);
    * use yield (yield from) statements;
    * use nonlocal variables, referencing the outside objects.

If an autonomous function is allowed to use other autonomous functions,
it is called "loosely autonomous function". Otherwise, it is called
"strictly autonomous function".

Autonomous functions can have nested functions and classes.

Only ordinary functions can be autonomous. Asynchronous functions,
class methods and lambda functions cannot be autonomous.

Decorators @autonomous, @loosely_autonomous, and @strictly_autonomous
allow to inform Pythagoras that a function is intended to be autonomous,
and to enforce autonomicity requirements for the function.
"""
from typing import Callable

from pythagoras._050_safe_code_portals import safe
from .autonomous_portal_core_classes import AutonomousFn, AutonomousCodePortal


class autonomous(safe):
    """Decorator for enforcing autonomicity requirements for functions.

    An autonomous function is only allowed to use the built-in objects
    (functions, types, variables), as well as global objects,
    accessible via import statements inside the function body.
    """
    _fixed_args: dict|None

    def __init__(self
                 , fixed_kwargs: dict | None = None
                 , excessive_logging: bool|None = None
                 , portal: AutonomousCodePortal | None = None
                 ):
        assert isinstance(portal, AutonomousCodePortal) or portal is None
        assert isinstance(fixed_kwargs, dict) or fixed_kwargs is None
        safe.__init__(self=self
            , portal=portal
            , excessive_logging=excessive_logging)
        self._fixed_kwargs = fixed_kwargs


    def __call__(self, fn: Callable|str) -> AutonomousFn:
        """Decorator for autonomous functions.

        It does both static and dynamic checks for autonomous functions.

        Static checks: it checks whether the function uses any global
        non-built-in objects which do not have associated import statements
        inside the function. If allow_idempotent==True,
        global idempotent functions are also allowed.
        The decorator also checks whether the function is using
        any non-local objects variables, and whether the function
        has yield / yield from statements in its code. If static checks fail,
        the decorator throws a FunctionAutonomicityError exception.

        Dynamic checks: during the execution time it hides all the global
        and non-local objects from the function, except the built-in ones
        (and idempotent ones, if allow_idempotent==True).
        If a function tries to use a non-built-in
        (and non-idempotent, if allow_idempotent==True)
        object without explicitly importing it inside the function body,
        it will result in raising an exception.

        Currently, neither static nor dynamic checks are guaranteed to catch
        all possible violations of function autonomy requirements.
        """

        wrapper = AutonomousFn(fn
            ,portal=self._portal
            ,fixed_kwargs=self._fixed_kwargs
            ,excessive_logging=self._excessive_logging)
        return wrapper