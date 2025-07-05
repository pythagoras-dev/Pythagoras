"""Classes and utilities to work with autonomous functions.

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


from .autonomous_portal_core_classes import AutonomousFn, AutonomousCodePortal

from .autonomous_decorators import autonomous

