import ast
from typing import List, Set


def check_if_fn_accepts_args(required_arg_names: List[str]|Set[str], fn: str) -> bool:
    """
    Analyzes the source code (string) `fn` of a Python function and determines
    if it can accept the arguments named in `required_arg_names`.

    This will return True if:
      - The function has a **kwargs parameter, or
      - The function explicitly defines all of the names in `required_arg_names` as parameters.

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

    # Collect all explicitly named parameters
    param_names = set()
    for arg in args.args:
        param_names.add(arg.arg)
    for kwarg in args.kwonlyargs:
        param_names.add(kwarg.arg)

    for name in required_arg_names:
        if name not in param_names:
            return False
    return True