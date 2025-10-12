import ast
from typing import List, Set


def check_if_fn_accepts_args(required_arg_names: List[str]|Set[str], fn: str) -> bool:
    """
    Analyzes the source code (string) `fn` of a Python function and determines
    if it can accept the arguments named in `required_arg_names`.

    This will return True if:
      - The function has a **kwargs parameter, or
      - The function explicitly defines all of the names in `required_arg_names` as parameters
        that can be passed by keyword.

    Otherwise, returns False.
    """

    tree = ast.parse(fn)

    func_def_nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    if not func_def_nodes:
        raise ValueError("No function definition found in the provided source code.")
    func_def = func_def_nodes[0]
    args = func_def.args

    # If there's a **kwargs (args.kwarg != None), it can accept any named argument
    if args.kwarg is not None:
        return True

    # Collect all explicitly named parameters (excluding positional-only)
    # Note: args.posonlyargs are NOT included as they cannot be passed by keyword
    param_names = {arg.arg for arg in args.args + args.kwonlyargs}

    return set(required_arg_names).issubset(param_names)