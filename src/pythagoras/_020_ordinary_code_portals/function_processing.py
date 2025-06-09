import types, inspect
from typing import Callable

from .._010_basic_portals.exceptions import NonCompliantFunction
from .._010_basic_portals.long_infoname import get_long_infoname


def get_function_name_from_source(function_source_code: str) -> str:
    """Return the name of a function from its source code."""
    lines = function_source_code.split('\n')
    for line in lines:
        stripped_line = line.strip()
        if stripped_line.startswith('def '):
            func_name_end = stripped_line.find('(')
            func_name = stripped_line[3:func_name_end]
            return func_name.strip()
    raise ValueError(f"Can't find function name in {function_source_code=}")


def accepts_unlimited_positional_args(func: Callable) -> bool:
    """Check if a function accepts an arbitrary number of positional arguments.

    This function inspects the signature of the provided callable and
    checks if it includes a name defined with `*args`,
    which allows it to accept any number of positional arguments.
    """

    signature = inspect.signature(func)
    for param in signature.parameters.values():
        if param.kind == inspect.Parameter.VAR_POSITIONAL:
            return True
    return False


def count_parameters_with_defaults(func: Callable) -> int:
    """Returns the number of function parameters that have default values."""
    signature = inspect.signature(func)
    return sum(
        param.default is not param.empty
        for param in signature.parameters.values()
    )


def assert_ordinarity(a_func:Callable) -> None:
    """Assert that a function is ordinary.

    A function is ordinary if it is not a method,
    a classmethod, a staticmethod, or a lambda function,
    or a build-in function.

    An ordinary function can only be called with keyword arguments,
    and its parameters can't have default values.

    assert_ordinarity checks a function, given as an input name,
    and throws an exception if the function is not ordinary.
    """

    # TODO: decide how to handle static methods
    # currently they are treated as ordinary functions

    name = get_long_infoname(a_func)

    if not callable(a_func):
        raise NonCompliantFunction(f"{name} must be callable.")

    if not inspect.isfunction(a_func):
        raise NonCompliantFunction(f"The function {name} is not ordinary."
            "It must be a function, not a method, "
            "a classmethod, or a lambda function.")

    if isinstance(a_func, types.MethodType):
        raise NonCompliantFunction(f"The function {name} can't be "
            "an instance or a class method, only "
            "regular functions are allowed.")

    if hasattr(a_func, "__closure__") and a_func.__closure__ is not None:
        raise NonCompliantFunction(f"The function {name} can't be a closure,"
            " only regular functions are allowed.")

    if a_func.__name__ == "<lambda>":
        raise NonCompliantFunction(f"The function {name} can't be lambda,"
            " only regular functions are allowed.")

    if accepts_unlimited_positional_args(a_func):
        raise NonCompliantFunction("Pythagoras only allows functions "
            f"with named arguments, but {name} accepts "
            "unlimited (nameless) positional arguments.")

    if inspect.iscoroutinefunction(a_func):
        raise NonCompliantFunction(f"The function {name} can't be "
            "an async function, only regular functions are allowed.")

    if count_parameters_with_defaults(a_func) > 0:
        raise NonCompliantFunction(f"The function {name} can't have "
            "default values for its parameters.")