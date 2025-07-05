"""Decorators and utilities to work with pure functions.

A pure function is a protected function that has no side effects and
always returns the same result if it is called multiple times
with the same arguments.

This subpackage defines a decorator which is used to inform Pythagoras that
a function is intended to be pure: @pure().

Pythagoras persistently caches results, produced by a pure function, so that
if the function is called multiple times with the same arguments,
the function is executed only once, and the cached result is returned
for all the subsequent executions.

While caching the results of a pure function, Pythagoras also tracks
changes in the source code of the function. If the source code of a pure
function changes, the function is executed again on the next call.
However, the previously cached results are still available
for the old version of the function. Only changes in the function's
source code are tracked.

Pythagoras provides infrastructure for remote execution of
pure functions in distributed environments. Pythagoras employs
an asynchronous execution model called 'swarming':
you do not know when your function will be executed,
what machine will execute it, and how many times it will be executed.
Pythagoras ensures that the function will be eventually executed
at least once, but does not offer any further guarantees.
"""

from .pure_core_classes import (
    PureFn
    , PureCodePortal
    , PureFnExecutionResultAddr)

from .pure_decorator import pure