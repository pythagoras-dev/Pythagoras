"""Classes and utilities to work with autonomous functions.

In an essence, an 'autonomous' function contains self-sufficient code
that does not depend on external imports or definitions. All required
imports should be done inside the function body. Only ordinary functions
can be autonomous.

Autonomous functions are always allowed to use the built-in objects
(functions, types, variables), as well as global objects,
explicitly imported inside the function body. An autonomous function
is allowed to use other autonomous functions,
created outside the autonomous function,
if they belong to the same island.

An island is namespace that groups autonomous functions together.
An autonomous function can use other autonomous functions from the same island
without explicitly importing them.

Autonomous functions are not allowed to:

    * use global objects, imported or defined outside the function body
      (except built-in objects and other autonomous functions
      from the same island);
    * use yield (yield from) statements;
    * use nonlocal variables, referencing the outside objects.

If an autonomous function is using other autonomous functions
from the same island, it is called "loosely autonomous function".
Otherwise, it is called "strictly autonomous function".

Autonomous functions can have nested functions and classes.

Only regular functions can be autonomous. Asynchronous functions,
class methods and lambda functions cannot be autonomous.

This module defines  decorators which are used to
inform Pythagoras that a function is intended to be autonomous,
and to enforce autonomicity requirements:
@autonomous() and @strictly_autonomous() .

It also defines functions which are used to check whether a corresponding
decorator was added earlier to another function: is_autonomous(),
is_loosely_autonomous(), and is_strictly_autonomous().

Applying a decorator to a function ensures both static and runtime autonomicity
checks are performed for the function. Static checks happen at the time
of decoration, while runtime checks happen at the time of function execution.
"""


from .autonomous_portal_core_classes import AutonomousFn, AutonomousCodePortal

from .autonomous_decorators import autonomous

