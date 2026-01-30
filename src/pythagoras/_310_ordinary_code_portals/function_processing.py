"""Utilities for inspecting and validating Python functions.

This module provides functions to extract function names from source code,
validate compliance with Pythagoras ordinarity rules (keyword-only arguments,
no defaults, no closures, etc.), and enforce these constraints.
"""

import ast
import textwrap
import types
import inspect
from functools import cache
from typing import Callable

from .function_error_exception import FunctionError
from .._110_supporting_utilities import get_long_infoname

@cache
def get_function_name_from_source(function_source_code: str) -> str:
    """Extract the function name from source code.

    Args:
        function_source_code: Source code containing a function definition.

    Returns:
        Function name from the definition.

    Raises:
        ValueError: If no function definition is found or multiple definitions
            are present.
    """
    module_ast = ast.parse(textwrap.dedent(function_source_code))

    names = []

    for node in module_ast.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names.append(node.name)

    if not len(names):
        raise ValueError("No function definition found in the provided source.")
    elif len(names) > 1:
        raise ValueError("Multiple function definitions found in the provided source.")
    else:
        return names[0]



def accepts_unlimited_positional_args(func: Callable) -> bool:
    """Check if function accepts arbitrary positional arguments.

    Args:
        func: Callable to inspect.

    Returns:
        True if function has a VAR_POSITIONAL (*args) parameter.
    """

    signature = inspect.signature(func)
    for param in signature.parameters.values():
        if param.kind == inspect.Parameter.VAR_POSITIONAL:
            return True
    return False


def has_positional_only_params(func: Callable) -> bool:
    """Check if function has positional-only parameters.

    Args:
        func: Callable to inspect.

    Returns:
        True if function has any POSITIONAL_ONLY parameters.
    """
    signature = inspect.signature(func)
    for param in signature.parameters.values():
        if param.kind == inspect.Parameter.POSITIONAL_ONLY:
            return True
    return False


def count_parameters_with_defaults(func: Callable) -> int:
    """Count parameters with default values.

    Args:
        func: Callable to inspect.

    Returns:
        Number of parameters with default values.
    """
    signature = inspect.signature(func)
    return sum(
        param.default is not param.empty
        for param in signature.parameters.values()
    )


def assert_ordinarity(a_func: Callable) -> None:
    """Validate that a callable complies with Pythagoras ordinarity rules.

    An ordinary function must be:
    - A plain function (not method, classmethod, lambda, closure, or async)
    - Accept only named arguments (no *args)
    - Have no parameters with default values

    Note:
        Static method handling is undecided; currently treated as regular
        functions if provided as function objects.

    Args:
        a_func: Callable to validate.

    Raises:
        FunctionError: If the callable violates ordinarity constraints.
    """

    # TODO: decide how to handle static methods
    # currently they are treated as ordinary functions

    name = get_long_infoname(a_func)

    if not callable(a_func):
        raise FunctionError(f"{name} must be callable.")

    if not inspect.isfunction(a_func):
        raise FunctionError(f"The function {name} is not ordinary."
            "It must be a function, not a method, "
            "a classmethod, or a lambda function.")

    if isinstance(a_func, types.MethodType):
        raise FunctionError(f"The function {name} can't be "
            "an instance or a class method, only "
            "regular functions are allowed.")

    if hasattr(a_func, "__closure__") and a_func.__closure__ is not None:
        raise FunctionError(f"The function {name} can't be a closure,"
            " only regular functions are allowed.")

    if a_func.__name__ == "<lambda>":
        raise FunctionError(f"The function {name} can't be lambda,"
            " only regular functions are allowed.")

    if accepts_unlimited_positional_args(a_func):
        raise FunctionError("Pythagoras only allows functions "
            f"with named arguments, but {name} accepts "
            "unlimited (nameless) positional arguments.")

    if has_positional_only_params(a_func):
        raise FunctionError(f"The function {name} has positional-only "
            "parameters, which are not allowed in ordinary functions.")

    if inspect.iscoroutinefunction(a_func):
        raise FunctionError(f"The function {name} can't be "
            "an async function, only regular functions are allowed.")

    if count_parameters_with_defaults(a_func) > 0:
        raise FunctionError(f"The function {name} can't have "
            "default values for its parameters.")