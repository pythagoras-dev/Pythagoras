"""Tests for internal helper functions in code_normalizer module.

This module tests internal helper functions that perform the individual steps
of function source code normalization. While these are implementation details,
testing them directly provides better error isolation and branch coverage.
"""

import ast
import pytest

from pythagoras import FunctionError
from pythagoras._310_ordinary_code_portals.code_normalizer import (
    _is_pythagoras_decorator,
    _AnnotationRemover,
    _extract_fn_name_and_source_code,
    _dedent_and_clean_empty_lines,
    _parse_and_validate_function_ast,
    _validate_and_remove_decorators,
)


# Tests for _is_pythagoras_decorator


def test_is_pythagoras_decorator_with_name_node():
    """Test _is_pythagoras_decorator with simple Name node."""
    source = "@ordinary\ndef f(): pass"
    tree = ast.parse(source)
    func_node = tree.body[0]
    decorator = func_node.decorator_list[0]

    assert _is_pythagoras_decorator(decorator) is True


def test_is_pythagoras_decorator_with_all_known_decorators():
    """Test all known Pythagoras decorator names."""
    known_decorators = ["ordinary", "logging", "safe",
                        "autonomous", "protected", "pure"]

    for dec_name in known_decorators:
        source = f"@{dec_name}\ndef f(): pass"
        tree = ast.parse(source)
        func_node = tree.body[0]
        decorator = func_node.decorator_list[0]
        assert _is_pythagoras_decorator(decorator) is True


def test_is_pythagoras_decorator_with_attribute_node():
    """Test _is_pythagoras_decorator with module-qualified Attribute node."""
    source = "@pth.ordinary\ndef f(): pass"
    tree = ast.parse(source)
    func_node = tree.body[0]
    decorator = func_node.decorator_list[0]

    assert _is_pythagoras_decorator(decorator) is True


def test_is_pythagoras_decorator_with_call_node():
    """Test _is_pythagoras_decorator with decorator call."""
    source = "@ordinary(portal=p)\ndef f(): pass"
    tree = ast.parse(source)
    func_node = tree.body[0]
    decorator = func_node.decorator_list[0]

    assert _is_pythagoras_decorator(decorator) is True


def test_is_pythagoras_decorator_with_non_pythagoras():
    """Test _is_pythagoras_decorator rejects non-Pythagoras decorators."""
    source = "@some_external_decorator\ndef f(): pass"
    tree = ast.parse(source)
    func_node = tree.body[0]
    decorator = func_node.decorator_list[0]

    assert _is_pythagoras_decorator(decorator) is False


def test_is_pythagoras_decorator_with_unknown_decorator():
    """Test _is_pythagoras_decorator with unknown decorator name."""
    source = "@unknown_decorator\ndef f(): pass"
    tree = ast.parse(source)
    func_node = tree.body[0]
    decorator = func_node.decorator_list[0]

    assert _is_pythagoras_decorator(decorator) is False


# Tests for _AnnotationRemover


def test_annotation_remover_visit_ann_assign_with_value():
    """Test _AnnotationRemover converts annotated assignment with value."""
    source = "x: int = 5"
    tree = ast.parse(source)
    remover = _AnnotationRemover()
    new_tree = remover.visit(tree)

    result = ast.unparse(new_tree)
    assert "int" not in result
    assert "x = 5" in result


def test_annotation_remover_visit_ann_assign_without_value():
    """Test _AnnotationRemover handles annotated assignment without value."""
    source = "x: int"
    tree = ast.parse(source)
    remover = _AnnotationRemover()
    new_tree = remover.visit(tree)

    result = ast.unparse(new_tree)
    assert "int" not in result
    assert "x" in result


def test_annotation_remover_visit_arg():
    """Test _AnnotationRemover removes function argument annotations."""
    source = "def f(x: int, y: str): pass"
    tree = ast.parse(source)
    remover = _AnnotationRemover()
    new_tree = remover.visit(tree)

    result = ast.unparse(new_tree)
    assert "int" not in result
    assert "str" not in result
    assert "def f(x, y):" in result


def test_annotation_remover_visit_function_def_return_annotation():
    """Test _AnnotationRemover removes return type annotation."""
    source = "def f(x) -> int: return x"
    tree = ast.parse(source)
    remover = _AnnotationRemover()
    new_tree = remover.visit(tree)

    result = ast.unparse(new_tree)
    assert "-> int" not in result
    assert "def f(x):" in result


def test_annotation_remover_visit_async_function_def():
    """Test _AnnotationRemover handles async function annotations."""
    source = "async def f(x: int) -> str: return str(x)"
    tree = ast.parse(source)
    remover = _AnnotationRemover()
    new_tree = remover.visit(tree)

    result = ast.unparse(new_tree)
    assert "int" not in result
    assert "-> str" not in result
    assert "async def f(x):" in result


def test_annotation_remover_empty_function_body_gets_pass():
    """Test _AnnotationRemover adds pass to empty function bodies."""
    source = "def f(): x: int"
    tree = ast.parse(source)
    remover = _AnnotationRemover()
    new_tree = remover.visit(tree)

    func_node = new_tree.body[0]
    assert len(func_node.body) > 0
    result = ast.unparse(new_tree)
    assert "pass" in result or "x" in result


# Tests for _extract_fn_name_and_source_code


def test_extract_fn_name_and_source_code_with_callable():
    """Test _extract_fn_name_and_source_code with callable function."""
    def sample_func(x, y):
        return x + y

    name, source = _extract_fn_name_and_source_code(sample_func)

    assert "sample_func" in name
    assert "def sample_func" in source
    assert "return x + y" in source


def test_extract_fn_name_and_source_code_with_string():
    """Test _extract_fn_name_and_source_code with source string."""
    source_code = """
def my_func(a, b):
    return a * b
"""
    name, source = _extract_fn_name_and_source_code(source_code)

    assert name == "my_func"
    assert "def my_func" in source


def test_extract_fn_name_and_source_code_with_invalid_type():
    """Test _extract_fn_name_and_source_code rejects invalid types."""
    with pytest.raises(TypeError, match="must be a callable or a string"):
        _extract_fn_name_and_source_code(123)

    with pytest.raises(TypeError, match="must be a callable or a string"):
        _extract_fn_name_and_source_code([1, 2, 3])


def test_extract_fn_name_and_source_code_with_non_ordinary_function():
    """Test _extract_fn_name_and_source_code validates ordinarity."""
    def func_with_defaults(x=10):
        return x

    with pytest.raises(FunctionError, match="can't have.*default values"):
        _extract_fn_name_and_source_code(func_with_defaults)


# Tests for _dedent_and_clean_empty_lines


def test_dedent_and_clean_empty_lines_removes_indentation():
    """Test _dedent_and_clean_empty_lines removes leading whitespace."""
    source = """
    def f():
        return 1
    """
    result = _dedent_and_clean_empty_lines(source, "f")

    assert result.startswith("def f")
    assert "    def" not in result


def test_dedent_and_clean_empty_lines_removes_empty_lines():
    """Test _dedent_and_clean_empty_lines removes blank lines."""
    source = """
def f():

    return 1

"""
    result = _dedent_and_clean_empty_lines(source, "f")
    lines = result.split('\n')

    assert all(line.strip() for line in lines)
    assert len(lines) == 2


def test_dedent_and_clean_empty_lines_with_empty_code():
    """Test _dedent_and_clean_empty_lines raises error on empty code."""
    with pytest.raises(ValueError, match="Cannot normalize empty code"):
        _dedent_and_clean_empty_lines("   \n\n  ", "some_func")

    with pytest.raises(ValueError, match="Cannot normalize empty code"):
        _dedent_and_clean_empty_lines("", "some_func")


# Tests for _parse_and_validate_function_ast


def test_parse_and_validate_function_ast_with_valid_function():
    """Test _parse_and_validate_function_ast with valid function source."""
    source = "def my_func(x):\n    return x * 2"
    ast_module = _parse_and_validate_function_ast(source, "my_func")

    assert isinstance(ast_module, ast.Module)
    assert len(ast_module.body) == 1
    assert isinstance(ast_module.body[0], ast.FunctionDef)


def test_parse_and_validate_function_ast_with_empty_body():
    """Test _parse_and_validate_function_ast rejects empty AST body."""
    with pytest.raises(ValueError, match="Empty AST body"):
        _parse_and_validate_function_ast("", "empty_func")


def test_parse_and_validate_function_ast_with_non_function():
    """Test _parse_and_validate_function_ast rejects non-function code."""
    source = "x = 10\ny = 20"
    with pytest.raises(ValueError, match="not a FunctionDef"):
        _parse_and_validate_function_ast(source, "not_a_func")


def test_parse_and_validate_function_ast_with_class():
    """Test _parse_and_validate_function_ast rejects class definitions."""
    source = "class MyClass:\n    pass"
    with pytest.raises(ValueError, match="not a FunctionDef"):
        _parse_and_validate_function_ast(source, "MyClass")


# Tests for _validate_and_remove_decorators


def test_validate_and_remove_decorators_single_pythagoras():
    """Test _validate_and_remove_decorators removes Pythagoras decorator."""
    source = "@ordinary\ndef f(): pass"
    code_ast = ast.parse(source)

    _validate_and_remove_decorators(code_ast, "f", drop_pth_decorators=True)

    func_node = code_ast.body[0]
    assert len(func_node.decorator_list) == 0


def test_validate_and_remove_decorators_keeps_when_flag_false():
    """Test _validate_and_remove_decorators keeps decorator when flag is False."""
    source = "@ordinary\ndef f(): pass"
    code_ast = ast.parse(source)

    _validate_and_remove_decorators(code_ast, "f", drop_pth_decorators=False)

    func_node = code_ast.body[0]
    assert len(func_node.decorator_list) == 1


def test_validate_and_remove_decorators_multiple_decorators_error():
    """Test _validate_and_remove_decorators rejects multiple decorators."""
    source = "@decorator1\n@decorator2\ndef f(): pass"
    code_ast = ast.parse(source)

    with pytest.raises(FunctionError, match="can't have multiple decorators"):
        _validate_and_remove_decorators(code_ast, "f", drop_pth_decorators=False)


def test_validate_and_remove_decorators_non_pythagoras_with_drop_flag():
    """Test _validate_and_remove_decorators errors on non-Pythagoras with drop flag."""
    source = "@external_decorator\ndef f(): pass"
    code_ast = ast.parse(source)

    with pytest.raises(ValueError, match="non-Pythagoras decorator"):
        _validate_and_remove_decorators(code_ast, "f", drop_pth_decorators=True)


def test_validate_and_remove_decorators_no_decorator():
    """Test _validate_and_remove_decorators handles functions without decorators."""
    source = "def f(): pass"
    code_ast = ast.parse(source)

    _validate_and_remove_decorators(code_ast, "f", drop_pth_decorators=True)

    func_node = code_ast.body[0]
    assert len(func_node.decorator_list) == 0
