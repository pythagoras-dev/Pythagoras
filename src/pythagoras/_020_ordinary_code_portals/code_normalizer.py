"""Function source code normalization utilities.

This module provides functionality to normalize Python function source code
by removing decorators, docstrings, type annotations, and comments,
and applying PEP 8 formatting. This allows for consistent comparison
of function implementations.
"""

import ast
import inspect
import textwrap
from typing import Callable
import autopep8

from .function_processing import get_function_name_from_source
from .._800_foundational_utilities.long_infoname import get_long_infoname
from .function_processing import assert_ordinarity
from .function_error_exception import FunctionError

_pythagoras_decorator_names: set[str] = {
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

    Analyzes decorator syntax to identify Pythagoras-specific
    decorators (@ordinary, @pure, etc.) in their various forms: simple names,
    module-qualified attributes, or decorator calls.

    Args:
        decorator_node: An AST expression node representing a decorator.

    Returns:
        True if the decorator is a known Pythagoras decorator, False otherwise.
    """
    if isinstance(decorator_node, ast.Name):
        return decorator_node.id in _pythagoras_decorator_names

    if isinstance(decorator_node, ast.Attribute):
        return decorator_node.attr in _pythagoras_decorator_names

    if isinstance(decorator_node, ast.Call):
        return _is_pythagoras_decorator(decorator_node.func)

    return False

class _AnnotationRemover(ast.NodeTransformer):
    """AST transformer that strips type annotations from Python code.

    Removes type hints from function signatures, arguments, and variable
    annotations while preserving executable logic. This is essential for
    creating normalized function representations that can be compared
    independent of type annotation differences.
    """

    def visit_AnnAssign(self, node: ast.AnnAssign) -> ast.Assign | None:
        """Convert annotated assignment to regular assignment.

        Transforms `x: int = 5` into `x = 5` or `x: int` into a bare
        name expression, ensuring annotated variables remain executable
        after type hints are stripped.

        Args:
            node: Annotated assignment node to transform.

        Returns:
            Regular assignment node or expression statement.
        """
        if node.value is not None:
            new_node = ast.Assign(targets=[node.target], value=node.value)
            return ast.copy_location(new_node, node)
        else:
            bare_name_expr = ast.Expr(value=node.target)
            return ast.copy_location(bare_name_expr, node)
    
    def visit_arg(self, node: ast.arg) -> ast.arg:
        """Remove annotation from function argument."""
        node.annotation = None
        return node
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """Remove return annotation and process body.

        Args:
            node: Function definition node to process.

        Returns:
            Transformed function definition without return type annotation.
        """
        node.returns = None
        self.generic_visit(node)
        node.body = [stmt for stmt in node.body if stmt is not None]
        if not node.body:
            node.body = [ast.Pass()]
        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AsyncFunctionDef:
        """Remove return annotation and process body.

        Args:
            node: Async function definition node to process.

        Returns:
            Transformed async function definition without return type annotation.
        """
        node.returns = None
        self.generic_visit(node)
        node.body = [stmt for stmt in node.body if stmt is not None]
        if not node.body:
            node.body = [ast.Pass()]
        return node


def _get_normalized_function_source_impl(
        a_func: Callable | str,
        drop_pth_decorators: bool = False,
        ) -> str:
    """Produce a normalized representation of a function's source code.

    Normalization creates a canonical form of function source code that enables
    reliable comparison of function logic independent of formatting, comments,
    type hints, or decorators. This is essential for Pythagoras to detect when
    function implementations are semantically identical despite superficial
    differences.

    The normalization pipeline:
    1. Extracts source code (via inspect.getsource for callables)
    2. Dedents and removes empty lines
    3. Parses into AST and validates single function definition
    4. Optionally strips Pythagoras decorators (@ordinary, @pure, etc.)
    5. Removes all docstrings, type annotations, and variable annotations
    6. Ensures syntactic validity (adds 'pass' to empty bodies)
    7. Unparses and formats with autopep8 for consistent style

    Args:
        a_func: The target function or a string containing its source code.
        drop_pth_decorators: If True, remove a single known Pythagoras
            decorator (e.g., @ordinary) from the function, if present.

    Returns:
        A normalized source code string for the function.

    Raises:
        FunctionError: If the function has multiple decorators or fails
            ordinarity checks.
        TypeError: If input types are not as expected or AST node types are invalid.
        ValueError: If parsing assumptions fail or integrity checks do not hold.
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

    code = textwrap.dedent(code)
    code_lines = code.splitlines()

    code_clean_version_lines = []
    for line in code_lines:
        if not line.strip():
            continue
        code_clean_version_lines.append(line)

    if not code_clean_version_lines:
        raise ValueError(f"Cannot normalize empty code for function {a_func_name}")

    code_clean_version = "\n".join(code_clean_version_lines)

    if a_func_name is None:
        a_func_name = get_function_name_from_source(code_clean_version)
    code_ast = ast.parse(code_clean_version)

    if not isinstance(code_ast, ast.Module):
        raise TypeError(f"Expected AST Module for {a_func_name}, got {type(code_ast).__name__}")
    
    if not code_ast.body:
        raise ValueError(f"Empty AST body for function {a_func_name}")
    
    if not isinstance(code_ast.body[0], (ast.FunctionDef)):
        raise ValueError(f"Top-level node is not a FunctionDef for {a_func_name}; got {type(code_ast.body[0]).__name__}")

    # TODO: add support for multiple decorators???
    decorator_list = code_ast.body[0].decorator_list
    if len(decorator_list) > 1:
        # Multiple decorators complicate source comparison and execution model.
        # Pythagoras decorators are designed to be composable at the class level
        # (e.g., OrdinaryFn -> AutonomousFn -> PureFn) rather than via stacking.
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

    # Remove type annotations using NodeTransformer
    annotation_remover = _AnnotationRemover()
    code_ast = annotation_remover.visit(code_ast)
    
    # Fix missing locations after AST transformation
    ast.fix_missing_locations(code_ast)
    
    # Remove docstrings
    for node in ast.walk(code_ast):
        if not isinstance(node
                , (ast.FunctionDef, ast.ClassDef
                   , ast.AsyncFunctionDef, ast.Module)):
            continue

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
        
        if not is_docstring:
            continue
            
        node.body = node.body[1:]
        if len(node.body) < 1:
            node.body.append(ast.Pass())

    result = ast.unparse(code_ast)
    result = autopep8.fix_code(result)

    return result