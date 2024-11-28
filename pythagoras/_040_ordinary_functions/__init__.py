"""Classes and utilities to work with ordinary functions.

An 'ordinary' function is just a regular Python function that accepts
only named (keyword) arguments. To be used in Pythagoras, an ordinary
function must be converted into an OrdinaryFn object
by applying @ordinary decorator.

Lambda functions, class methods, asynchronous functions and closures
are not ordinary functions.

Ordinary functions are not allowed to have decorators, except for ones that
are part of Pythagoras (e.g. @autonomous, or @idempotent, or @ordinary).

Pythagoras transforms source code of an ordinary function into a normalised
form: a string that represents the function's source code, with all
decorators, docstrings, and comments removed, and the resulting code
formatted according to PEP8. This way, Pythagoras can later compare the source
code of two functions to check if they are equivalent.

Typically, a Pythagoras user does not need to directly work
with ordinary functions. Pythagoras employs OrdinaryFn
to implement autonomous and idempotent functions (which are
subclasses of OrdinaryFn). Most of the time, a Pythagoras user will
work with idempotent functions.
"""

from .ordinary_funcs import OrdinaryFn

from .ordinary_decorator import ordinary

from .long_infoname import get_long_infoname

