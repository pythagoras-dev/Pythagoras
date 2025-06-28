from pythagoras._020_ordinary_code_portals.function_processing import (
    accepts_unlimited_positional_args)

def test_with_arbitrary_positional_args():
    def func_with_args(*xyz):
        pass
    assert accepts_unlimited_positional_args(func_with_args)

def test_without_arbitrary_positional_args():
    def func_without_args(a, b):
        pass
    assert not accepts_unlimited_positional_args(func_without_args)


def test_with_named_and_arbitrary_positional_args():
    def func_with_named_and_args(a, *rrr):
        pass
    assert accepts_unlimited_positional_args(func_with_named_and_args)

def test_positive_complex_function():
    def func_with_named_and_args(a:bool, b:str, *kuku, **yuiiiiii):
        pass
    assert accepts_unlimited_positional_args(func_with_named_and_args)

def test_negative_complex_function():
    def func_with_named_and_args(a:float, b:int, **yuiiiiii):
        pass
    assert not accepts_unlimited_positional_args(func_with_named_and_args)


class MyClass:
    def method_with_args(self, *args):
        pass

def test_method_of_class():
    assert accepts_unlimited_positional_args(MyClass.method_with_args)
