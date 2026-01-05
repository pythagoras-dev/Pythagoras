import pytest

from pythagoras._310_ordinary_code_portals.function_processing import (
    get_function_name_from_source)

from inspect import getsource

def test_get_function_name_from_source():
    def a_function():
        pass

    name = get_function_name_from_source(getsource(a_function))
    assert name == "a_function"

    def another_function():
        pass

    name = get_function_name_from_source(getsource(another_function))
    assert name == "another_function"

def test_get_function_name_from_source_with_decorators():
    def sample_decorator(f):
        return f

    @sample_decorator
    def sample_function():
        pass

    name = get_function_name_from_source(getsource(sample_function))
    assert name == "sample_function"


def test_no_function_definition():
    """Test that ValueError is raised when no function is found."""
    source_without_function = """
x = 10
y = 20
result = x + y
"""
    with pytest.raises(ValueError, match="No function definition found"):
        get_function_name_from_source(source_without_function)


def test_multiple_function_definitions():
    """Test that ValueError is raised when multiple functions are found."""
    source_with_multiple = """
def first_function():
    pass

def second_function():
    pass
"""
    with pytest.raises(ValueError, match="Multiple function definitions found"):
        get_function_name_from_source(source_with_multiple)
