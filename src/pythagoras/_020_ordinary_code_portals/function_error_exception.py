"""Exception for function compliance errors.

This module defines the FunctionError exception, which is raised when
a function does not meet the requirements for being an "ordinary"
Pythagoras function.
"""


class FunctionError(Exception):
    """Exception raised when a function violates Pythagoras constraints/requirements.

    Raised when a function fails to meet requirements such as keyword-only
    arguments, no defaults, no closures, or other rules.
    """

    pass