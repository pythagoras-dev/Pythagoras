"""Function source code normalization utilities.

This module provides functionality to normalize Python function source code by
removing decorators, docstrings, type annotations, and comments, then applying
PEP 8 formatting. This enables consistent comparison and hashing of function
implementations.
"""

import ast
import inspect
import textwrap
from functools import cache
from typing import Callable
import autopep8

from .function_processing import get_function_name_from_source
from .._110_supporting_utilities.long_infoname import get_long_infoname
from .function_processing import assert_ordinarity
from .function_error_exception import FunctionError

_pythagoras_decorator_names: set[str] = {
    "ordinary"
    , "logging"
    , "safe"
    , "autonomous"
    , "protected"
    , "pure"
}


def _is_pythagoras_decorator(decorator_node: ast.expr) -> bool:
    """Check if decorator AST node is a Pythagoras decorator.

    Identifies Pythagoras decorators (@ordinary, @pure, etc.) in various forms:
    simple names, module-qualified attributes, or decorator calls.

    Args:
        decorator_node: AST expression node representing a decorator.

    Returns:
        True if decorator is a known Pythagoras decorator.
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
    annotations while preserving executable logic. This enables normalized
    function representations that can be compared independently of type hints.
    """

    def visit_AnnAssign(self, node: ast.AnnAssign) -> ast.Assign | None:
        """Convert annotated assignment to regular assignment.

        Transforms annotated assignments while preserving executable logic:
        `x: int = 5` becomes `x = 5`, and `x: int` becomes a bare name.

        Args:
            node: Annotated assignment node.

        Returns:
            Regular assignment or expression statement.
        """
        if node.value is not None:
            new_node = ast.Assign(targets=[node.target], value=node.value)
            return ast.copy_location(new_node, node)
        else:
            bare_name_expr = ast.Expr(value=node.target)
            return ast.copy_location(bare_name_expr, node)
    
    def visit_arg(self, node: ast.arg) -> ast.arg:
        """Remove type annotation from a function argument.

        Args:
            node: Function argument node.

        Returns:
            The same node with its annotation set to None.
        """
        node.annotation = None
        return node
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """Remove return annotation and process body.

        Args:
            node: Function definition node.

        Returns:
            Transformed function without return annotation.
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
            node: Async function definition node.

        Returns:
            Transformed async function without return annotation.
        """
        node.returns = None
        self.generic_visit(node)
        node.body = [stmt for stmt in node.body if stmt is not None]
        if not node.body:
            node.body = [ast.Pass()]
        return node


def _extract_fn_name_and_source_code(
        a_func: Callable | str,
        skip_ordinarity_check: bool = False
        ) -> tuple[str | None, str]:
    """Extract source code and function name from callable or string.

    Args:
        a_func: Function or source code string.
        skip_ordinarity_check: If True, skip ordinarity validation for callables.

    Returns:
        Tuple of (function_name_or_none, source_code). Name may be None for
        string inputs; extracted later during normalization.

    Raises:
        TypeError: If input is neither callable nor string.
    """
    if callable(a_func):
        if not skip_ordinarity_check:
            assert_ordinarity(a_func)
        fn_name_for_error_messages = get_long_infoname(a_func)
        fn_source_code = inspect.getsource(a_func)
        return fn_name_for_error_messages, fn_source_code
    elif isinstance(a_func, str):
        fn_source_code = a_func
        fn_name_for_error_messages = get_function_name_from_source(fn_source_code)
        return fn_name_for_error_messages, fn_source_code
    else:
        raise TypeError(f"a_func must be a callable or a string, got {get_long_infoname(a_func)}")


def _dedent_and_clean_empty_lines(
        fn_source_code: str,
        fn_name_for_error_messages: str | None
        ) -> str:
    """Dedent source code and remove empty lines.

    Args:
        fn_source_code: Source code string to clean.
        fn_name_for_error_messages: Function name for error messages; may be None.

    Returns:
        Cleaned source with dedentation and no empty lines.

    Raises:
        ValueError: If code is empty after cleaning.
    """
    fn_source_code = textwrap.dedent(fn_source_code)
    code_lines = fn_source_code.splitlines()

    code_clean_version_lines = []
    for line in code_lines:
        if not line.strip():
            continue
        code_clean_version_lines.append(line)

    if not code_clean_version_lines:
        raise ValueError(f"Cannot normalize empty code for function {fn_name_for_error_messages}")

    return "\n".join(code_clean_version_lines)


def _parse_and_validate_function_ast(
        code_clean_version: str,
        fn_name_for_error_messages: str
        ) -> ast.Module:
    """Parse source into AST and validate single function definition.

    Args:
        code_clean_version: Cleaned source code string.
        fn_name_for_error_messages: Function name for error messages.

    Returns:
        Validated AST Module with function definition.

    Raises:
        TypeError: If AST is not a Module.
        ValueError: If AST body is empty or lacks FunctionDef.
        SyntaxError: If source cannot be parsed.
    """
    code_ast = ast.parse(code_clean_version)

    if not isinstance(code_ast, ast.Module):
        raise TypeError(f"Expected AST Module for {fn_name_for_error_messages}, got {get_long_infoname(code_ast)}")

    if not code_ast.body:
        raise ValueError(f"Empty AST body for function {fn_name_for_error_messages}")

    if not isinstance(code_ast.body[0], (ast.FunctionDef)):
        raise ValueError(f"Top-level node is not a FunctionDef for {fn_name_for_error_messages}; got {get_long_infoname(code_ast.body[0])}")

    return code_ast


def _validate_and_remove_decorators(
        code_ast: ast.Module,
        fn_name_for_error_messages: str,
        drop_pth_decorators: bool
        ) -> None:
    """Validate decorator count and optionally remove Pythagoras decorators.

    Modifies AST in place to remove decorators when requested.

    Args:
        code_ast: AST Module with function definition.
        fn_name_for_error_messages: Function name for error messages.
        drop_pth_decorators: Whether to remove Pythagoras decorators.

    Raises:
        FunctionError: If function has multiple decorators.
        ValueError: If drop_pth_decorators is True but decorator is not
            Pythagoras-specific.
    """
    decorator_list = code_ast.body[0].decorator_list
    if len(decorator_list) > 1:
        # Multiple decorators complicate source comparison and execution.
        # Pythagoras decorators compose at the class level (OrdinaryFn ->
        # AutonomousFn -> PureFn) rather than via stacking.
        raise FunctionError(
            f"Function {fn_name_for_error_messages} can't have multiple "
            "decorators; only one decorator is allowed.")

    # Remove Pythagoras decorators when requested
    if drop_pth_decorators and decorator_list:
        decorator_node = decorator_list[0]
        if _is_pythagoras_decorator(decorator_node):
            code_ast.body[0].decorator_list = []
        else:
            raise ValueError(
                f"Function {fn_name_for_error_messages} has a non-Pythagoras decorator "
                f"that cannot be dropped with drop_pth_decorators=True"
            )


def _remove_type_annotations(code_ast: ast.Module) -> ast.Module:
    """Remove type annotations from AST.

    Args:
        code_ast: AST Module to process.

    Returns:
        Transformed AST without type annotations.
    """
    annotation_remover = _AnnotationRemover()
    code_ast = annotation_remover.visit(code_ast)
    ast.fix_missing_locations(code_ast)
    return code_ast


def _remove_docstrings(code_ast: ast.Module) -> None:
    """Remove docstrings from all AST nodes.

    Modifies AST in place, removing docstring expressions and adding 'pass' to
    empty bodies.

    Args:
        code_ast: AST Module to process.
    """
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
        first_value = node.body[0].value
        is_docstring = False

        if isinstance(first_value, ast.Constant) and isinstance(first_value.value, str):
            is_docstring = True

        if not is_docstring:
            continue

        node.body = node.body[1:]
        if len(node.body) < 1:
            node.body.append(ast.Pass())


@cache
def _normalize_fn_source_code_str(
        fn_source_code: str,
        fn_name_for_error_messages: str | None,
        drop_pth_decorators: bool = False,
        ) -> str:
    """Normalize function source code string.

    Applies full normalization: dedent, clean empty lines, parse AST, remove
    decorators/annotations/docstrings, and PEP 8 format.

    Args:
        fn_source_code: Source code string to normalize.
        fn_name_for_error_messages: Function name for error messages; may be None.
        drop_pth_decorators: Whether to remove Pythagoras decorators.

    Returns:
        Normalized source code string.

    Raises:
        FunctionError: If function has multiple decorators.
        TypeError: If AST node types are invalid.
        ValueError: If parsing assumptions or integrity checks fail.
        SyntaxError: If source cannot be parsed.
    """
    code_clean_version = _dedent_and_clean_empty_lines(fn_source_code, fn_name_for_error_messages)

    if fn_name_for_error_messages is None:
        fn_name_for_error_messages = get_function_name_from_source(code_clean_version)

    code_ast = _parse_and_validate_function_ast(code_clean_version, fn_name_for_error_messages)
    _validate_and_remove_decorators(code_ast, fn_name_for_error_messages, drop_pth_decorators)
    code_ast = _remove_type_annotations(code_ast)
    _remove_docstrings(code_ast)

    result = ast.unparse(code_ast)
    result = autopep8.fix_code(result)

    return result


def _get_normalized_fn_source_code_str_impl(
        a_func: Callable | str,
        drop_pth_decorators: bool = False,
        skip_ordinarity_check: bool = False,
        ) -> str:
    """Produce normalized representation of function source code.

    Normalization creates canonical source form enabling reliable comparison
    independent of formatting, comments, type hints, or decorators. This allows
    Pythagoras to detect semantically identical functions despite superficial
    differences.

    Normalization pipeline:
    1. Extract source code (via inspect.getsource for callables)
    2. Dedent and remove empty lines
    3. Parse into AST and validate single function definition
    4. Optionally strip Pythagoras decorators (@ordinary, @pure, etc.)
    5. Remove docstrings, type annotations, and variable annotations
    6. Ensure syntactic validity (add 'pass' to empty bodies)
    7. Unparse and apply PEP 8 formatting for consistent style

    Args:
        a_func: Function or source code string.
        drop_pth_decorators: Whether to remove Pythagoras decorators.
        skip_ordinarity_check: If True, skip ordinarity validation for callables.

    Returns:
        Normalized source code string.

    Raises:
        FunctionError: If function has multiple decorators or fails ordinarity
            checks (unless skip_ordinarity_check is True).
        TypeError: If input types or AST node types are invalid.
        ValueError: If parsing assumptions or integrity checks fail.
        SyntaxError: If source cannot be parsed.
    """
    func_name_for_error_messages, code = _extract_fn_name_and_source_code(
        a_func, skip_ordinarity_check=skip_ordinarity_check)
    return _normalize_fn_source_code_str(code, func_name_for_error_messages, drop_pth_decorators)