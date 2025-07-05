""" Classes and functions that enable swarming algorithm.

Pythagoras provides infrastructure for remote execution of
pure functions in distributed environments. Pythagoras employs
an asynchronous execution model called 'swarming':
you do not know when your function will be executed,
what machine will execute it, and how many times it will be executed.
Pythagoras ensures that the function will be eventually executed
at least once but does not offer any further guarantees.
"""

from .swarming_portals import *
