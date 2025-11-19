import ast
import inspect
from typing import Callable
import autopep8

from .function_processing import get_function_name_from_source
from .._010_basic_portals.long_infoname import get_long_infoname
from .function_processing import assert_ordinarity
from .exceptions import FunctionError

_pythagoras_decorator_names = {
    "ordinary"
    , "storable"
    , "logging"
    , "safe"
    , "autonomous"
    , "protected"
    , "pure"
}


def _is_pythagoras_decorator(decorator_node: ast.expr) -> bool:
    """Check if a decorator AST node represents a Pythagoras decorator.
    
    Args:
        decorator_node: An AST expression node representing a decorator.
        
    Returns:
        True if the decorator is a known Pythagoras decorator, False otherwise.
    """
    # Handle simple decorator like @ordinary
    if isinstance(decorator_node, ast.Name):
        return decorator_node.id in _pythagoras_decorator_names
    
    # Handle attribute decorator like @pth.ordinary or @pythagoras.ordinary
    if isinstance(decorator_node, ast.Attribute):
        return decorator_node.attr in _pythagoras_decorator_names
    
    # Handle call decorator like @ordinary() - check the function being called
    if isinstance(decorator_node, ast.Call):
        return _is_pythagoras_decorator(decorator_node.func)
    
    return False

def _get_normalized_function_source_impl(
        a_func: Callable | str,
        drop_pth_decorators: bool = False,
        ) -> str:
        """Produce a normalized representation of a function's source code.

        The normalization process performs the following steps:
        1) Accepts either a callable or a string of source code. If a callable
           is provided, it must be an ordinary function (validated) and its
           source is retrieved with inspect.getsource.
        2) Removes empty lines and normalizes indentation for functions defined
           inside other scopes so that parsing can succeed.
        3) Parses the code with ast.parse and validates there is exactly one
           top-level function definition.
        4) Optionally drops a single Pythagoras decorator (if present) when
           drop_pth_decorators=True. Only known Pythagoras decorator names are
           removed; any other decorator remains.
        5) Strips all docstrings, return/type annotations, and variable
           annotations from the AST. For nodes that become empty as a result,
           a "pass" is inserted to keep the code valid.
        6) Unparses the AST back to code and runs autopep8 to enforce PEP 8
           formatting.

        Args:
            a_func: The target function or a string containing its source code.
            drop_pth_decorators: If True, remove a single known Pythagoras
                decorator (e.g., @ordinary) from the function, if present.

        Returns:
            A normalized source code string for the function.

        Raises:
            FunctionError: If the function has multiple decorators when
                a callable or a string representing a single function is
                expected; or if it fails ordinarity checks.
            TypeError | ValueError: If input types or parsing assumptions fail
                (e.g., unexpected AST node types), or when integrity checks do not hold.
            SyntaxError: If the provided source string cannot be parsed.
        """

        a_func_name, code = None, ""

        if callable(a_func):
            assert_ordinarity(a_func)
            a_func_name = get_long_infoname(a_func)
            code = inspect.getsource(a_func)
        elif isinstance(a_func, str):
            code = a_func
            a_func_name = get_function_name_from_source(code)
        else:
            raise TypeError(f"a_func must be a callable or a string, got {type(a_func).__name__}")

        code_lines = code.splitlines()

        code_no_empty_lines = []
        for line in code_lines:
            if set(line) <= set(" \t"):
                continue
            code_no_empty_lines.append(line)

        # Fix indent for functions that are defined within other functions;
        # most frequently it is used for tests.
        first_line_no_indent = code_no_empty_lines[0].lstrip()
        n_chars_to_remove = len(code_no_empty_lines[0]) - len(first_line_no_indent)
        chars_to_remove = code_no_empty_lines[0][:n_chars_to_remove]
        code_clean_version = []
        for line in code_no_empty_lines:
            if not line.startswith(chars_to_remove):
                raise ValueError(f"Inconsistent indentation detected while normalizing function {a_func_name}")
            cleaned_line = line[n_chars_to_remove:]
            code_clean_version.append(cleaned_line)

        code_clean_version = "\n".join(code_clean_version)
        if a_func_name is None:
            a_func_name = get_function_name_from_source(code_clean_version)
        code_ast = ast.parse(code_clean_version)

        if not isinstance(code_ast, ast.Module):
            raise TypeError(f"Expected AST Module for {a_func_name}, got {type(code_ast).__name__}")
        if not isinstance(code_ast.body[0], ast.FunctionDef):
            raise ValueError(f"Top-level node is not a FunctionDef for {a_func_name}; got {type(code_ast.body[0]).__name__}")

        # TODO: add support for multiple decorators???
        decorator_list = code_ast.body[0].decorator_list
        if len(decorator_list) > 1:
            raise FunctionError(
                f"Function {a_func_name} can't have multiple decorators,"
                + " only one decorator is allowed.")

        # Remove Pythagoras decorators if requested
        if drop_pth_decorators and decorator_list:
            decorator_node = decorator_list[0]
            if _is_pythagoras_decorator(decorator_node):
                code_ast.body[0].decorator_list = []
            else:
                raise ValueError(
                    f"Function {a_func_name} has a non-Pythagoras decorator "
                    f"that cannot be dropped with drop_pth_decorators=True"
                )

        # Remove docstrings and annotations.
        for node in ast.walk(code_ast):

            if isinstance(node, ast.AnnAssign):
                # remove type annotation from variable declarations
                node.annotation = None
                continue

            if isinstance(node, ast.arg):
                # argument annotations in functions
                node.annotation = None
                continue

            if not isinstance(node
                    , (ast.FunctionDef, ast.ClassDef
                       , ast.AsyncFunctionDef, ast.Module)):
                continue

            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # remove return annotation from function definitions
                node.returns = None

            if not len(node.body):
                continue
            if not isinstance(node.body[0], ast.Expr):
                continue
            if not hasattr(node.body[0], 'value'):
                continue
            
            # Check for docstring: ast.Constant (Python 3.8+) with string value
            # or ast.Str (deprecated but kept for compatibility)
            first_value = node.body[0].value
            is_docstring = False
            
            if isinstance(first_value, ast.Constant) and isinstance(first_value.value, str):
                is_docstring = True
            elif isinstance(first_value, ast.Str):
                # Deprecated in Python 3.8+ but kept for backwards compatibility
                is_docstring = True
            
            if not is_docstring:
                continue
                
            node.body = node.body[1:]
            if len(node.body) < 1:
                node.body.append(ast.Pass())

        result = ast.unparse(code_ast)
        result = autopep8.fix_code(result)

        return result