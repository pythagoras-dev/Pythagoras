import sys

from .._010_basic_portals.exceptions import NonCompliantFunction
import ast
import inspect
from typing import Callable
import autopep8

from .function_processing import get_function_name_from_source
from .._010_basic_portals.long_infoname import get_long_infoname
from .function_processing import assert_ordinarity

_pythagoras_decorator_names = {
    "ordinary"
    , "storable"
    , "logging"
    , "safe"
    , "autonomous"
    , "protected"
    , "pure"
}

def _get_normalized_function_source_impl(
        a_func: Callable | str
        , drop_pth_decorators: bool = False
        ) -> str:
        """Return function's source code in a 'canonical' form.

        Remove all comments, docstrings, type annotations, and empty lines;
        standardize code formatting based on PEP 8.
        If drop_pth_decorators == True, remove Pythagoras decorators.

        Only regular functions are supported; methods and lambdas are not supported.
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
            assert callable(a_func) or isinstance(a_func, str)

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
            assert line.startswith(chars_to_remove)
            cleaned_line = line[n_chars_to_remove:]
            code_clean_version.append(cleaned_line)

        code_clean_version = "\n".join(code_clean_version)
        if a_func_name is None:
            a_func_name = get_function_name_from_source(code_clean_version)
        code_ast = ast.parse(code_clean_version)

        assert isinstance(code_ast, ast.Module)
        assert isinstance(code_ast.body[0], ast.FunctionDef), (
            f"{type(code_ast.body[0])=}")

        # TODO: add support for multiple decorators???
        decorator_list = code_ast.body[0].decorator_list
        if len(decorator_list) > 1:
            raise NonCompliantFunction(
                f"Function {a_func_name} can't have multiple decorators,"
                + " only one decorator is allowed.")

        # all_decorators = pth.all_decorators
        # all_decorators = sys.modules['pythagoras'].all_decorators

        if drop_pth_decorators and len(decorator_list):
            decorator = decorator_list[0].func
            pth_dec_counter = 0
            for candidate in _pythagoras_decorator_names:
                try:
                    if decorator.id == candidate:
                        pth_dec_counter += 1
                        break
                except:
                    pass
                try:
                    if decorator.attr == candidate:
                        pth_dec_counter += 1
                        break
                except:
                    pass
            assert pth_dec_counter == 1
            code_ast.body[0].decorator_list = []

        # Remove docstrings.
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
            if not isinstance(node.body[0].value, ast.Str):
                continue
            node.body = node.body[1:]
            if len(node.body) < 1:
                node.body.append(ast.Pass())
            # TODO: compare with the source for ast.candidate_docstring()

        result = ast.unparse(code_ast)
        result = autopep8.fix_code(result)

        return result