"""Decorators and utilities to work with pure functions.

A pure function is an autonomous function that has no side effects and
always returns the same result if it is called multiple times
with the same arguments.

This module defines a decorator which is used to inform Pythagoras that
a function is intended to be pure: @pure().

Pythagoras persistently caches results, produced by a pure function, so that
if the function is called multiple times with the same arguments,
the function is executed only once, and the cached result is returned
for all the subsequent executions.

While caching the results of a pure function, Pythagoras also tracks
changes in the source code of the function. If the source code of a pure
function changes, the function is executed again on the next call.
However, the previously cached results are still available
for the old version of the function.

A pure function must be autonomous. Pythagoras tracks source code changes
for the pure function as well other autonomous functions it is using,
provided they belong to the same island. Pythagoras does not track source code
changes for functions from other islands, even if they are used
by the pure function. Pythagoras also does not track any other
source code changes (e.g. changes in the imported packages).

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