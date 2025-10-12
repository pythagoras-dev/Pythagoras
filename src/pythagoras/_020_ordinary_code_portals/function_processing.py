import types, inspect
from typing import Callable

from .exceptions import FunctionError
from .._010_basic_portals.long_infoname import get_long_infoname


def get_function_name_from_source(function_source_code: str) -> str:
    """Extract the function name from a source code snippet.

    This parser scans the source code line-by-line and returns the name
    from the first line that starts with "def ". It assumes a standard
    function definition like:

    def my_func(arg1, arg2):
        ...

    It does not currently detect async functions defined with "async def",
    and it will raise an error if no valid definition is found.

    Args:
        function_source_code: The source code containing a function definition.

    Returns:
        The function name as it appears before the opening parenthesis.

    Raises:
        ValueError: If no function definition line is found in the input.
    """
    lines = function_source_code.split('\n')
    for line in lines:
        stripped_line = line.strip()
        if stripped_line.startswith('def '):
            func_name_end = stripped_line.find('(')
            func_name = stripped_line[3:func_name_end]
            return func_name.strip()
    raise ValueError(f"Can't find function name in {function_source_code=}")


def accepts_unlimited_positional_args(func: Callable) -> bool:
    """Return True if the function accepts arbitrary positional args.

    The check is based on inspect.signature and looks for a parameter of
    kind VAR_POSITIONAL (i.e., a "*args" parameter).

    Args:
        func: The callable to inspect.

    Returns:
        True if the function defines a VAR_POSITIONAL ("*args") parameter;
        False otherwise.
    """

    signature = inspect.signature(func)
    for param in signature.parameters.values():
        if param.kind == inspect.Parameter.VAR_POSITIONAL:
            return True
    return False


def count_parameters_with_defaults(func: Callable) -> int:
    """Count parameters that have default values in the function signature.

    Args:
        func: The callable to inspect.

    Returns:
        The number of parameters with default values.
    """
    signature = inspect.signature(func)
    return sum(
        param.default is not param.empty
        for param in signature.parameters.values()
    )


def assert_ordinarity(a_func: Callable) -> None:
    """Validate that a callable complies with Pythagoras "ordinary" rules.

    In Pythagoras, an "ordinary" function is a regular Python function that:
    - is a plain function object (not a bound/unbound method, classmethod,
      staticmethod object, lambda, closure, coroutine, or built-in), and
    - does not accept unlimited positional arguments (no "*args"), and
    - has no parameters with default values.

    Notes:
    - Static methods: The handling of static methods is undecided; for now they
      are treated the same as regular functions only if provided directly as a
      function object. If a function fails any of the checks below, an error is
      raised.

    Args:
        a_func: The callable to validate.

    Raises:
        FunctionError: If the callable violates any of the ordinarity
            constraints described above (e.g., not a function, is a method,
            is a lambda/closure/async function, accepts *args, or has defaults).
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

    if inspect.iscoroutinefunction(a_func):
        raise FunctionError(f"The function {name} can't be "
            "an async function, only regular functions are allowed.")

    if count_parameters_with_defaults(a_func) > 0:
        raise FunctionError(f"The function {name} can't have "
            "default values for its parameters.")