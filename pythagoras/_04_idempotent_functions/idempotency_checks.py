from pythagoras._04_idempotent_functions.idempotent_func_and_address import (
    IdempotentFunction)


def is_idempotent(a_func):
    assert callable(a_func)
    return isinstance(a_func, IdempotentFunction)