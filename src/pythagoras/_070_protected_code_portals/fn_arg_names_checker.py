import ast
from typing import List, Set


def check_if_fn_accepts_args(required_arg_names: List[str]|Set[str], fn: str) -> bool:
    """Determine whether a function can accept specific keyword argument names.

    Analyzes the source code of a single Python function and checks whether
    all required names could be passed as keyword arguments.

    Args:
      required_arg_names: Iterable of parameter names that must be accepted.
      fn: Source code string containing exactly one function definition.

    Returns:
      True if the function has **kwargs or explicitly defines all required names
      as keyword-acceptable parameters; otherwise False.

    Raises:
      ValueError: If no function definition is found or if multiple functions are present.
    """

    tree = ast.parse(fn)

    func_def_nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    if not func_def_nodes:
        raise ValueError("No function definition found in the provided source code.")
    if not len(func_def_nodes) == 1:
        raise ValueError("Multiple function definitions found in the provided source code.")
    func_def = func_def_nodes[0]
    args = func_def.args

    # If there's a **kwargs (args.kwarg != None), it can accept any named argument
    if args.kwarg is not None:
        return True

    # Collect all explicitly named parameters (excluding positional-only)
    # Note: args.posonlyargs are NOT included as they cannot be passed by keyword
    param_names = {arg.arg for arg in args.args + args.kwonlyargs}

    return set(required_arg_names).issubset(param_names)