import pytest
from pythagoras._370_protected_code_portals.iterative_flattener import (
    flatten_iterative)


def test_fltattener_int():
    model_list = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    list_1 = [1, [2, 3, [4, 5, 6], 7, 8], 9]
    list_2 = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    list_3 = [1, [2, 3, [4, 5, 6], 7, 8], 9]
    list_4 = [1, [2, [3, [4, [5,[6,[7]]]]]],8, 9]
    assert flatten_iterative(list_1) == model_list
    assert flatten_iterative(list_2) == model_list
    assert flatten_iterative(list_3) == model_list
    assert flatten_iterative(list_4) == model_list


def test_flattener_empty():
    assert flatten_iterative([]) == []
    assert flatten_iterative([[[[[[]]]]]]) == []
    assert flatten_iterative([[],[],[],[],[],[],[],[],[],[]]) == []


def test_flattener_str():
    model_list = ["aaa", "bbb", "ccc", "ddd"]
    list_1 = [[[["aaa"], "bbb"], "ccc"], "ddd"]
    assert flatten_iterative(list_1) == model_list


# Tests for flatten_iterative


def test_flatten_iterative_flat_list():
    """Flat list should remain unchanged."""
    assert flatten_iterative([1, 2, 3, 4]) == [1, 2, 3, 4]


def test_flatten_iterative_flat_tuple():
    """Flat tuple should be converted to list."""
    assert flatten_iterative((1, 2, 3, 4)) == [1, 2, 3, 4]


def test_flatten_iterative_empty_iterables():
    """Empty iterables should produce empty list."""
    assert flatten_iterative([]) == []
    assert flatten_iterative(()) == []
    assert flatten_iterative(iter([])) == []


def test_flatten_iterative_nested_lists():
    """Nested lists should be fully flattened."""
    assert flatten_iterative([1, [2, 3, [4, 5]], 6]) == [1, 2, 3, 4, 5, 6]
    assert flatten_iterative([[[[[1]]]]]) == [1]


def test_flatten_iterative_mixed_iterables():
    """Mixed iterable types should all be flattened."""
    result = flatten_iterative([1, (2, 3), [4, (5, 6)], 7])
    assert result == [1, 2, 3, 4, 5, 6, 7]


def test_flatten_iterative_with_sets():
    """Sets should be flattened but order depends on iteration."""
    result = flatten_iterative([1, {2, 3}, 4])
    assert len(result) == 4
    assert result[0] == 1
    assert result[3] == 4
    assert set(result[1:3]) == {2, 3}


def test_flatten_iterative_strings_atomic():
    """Strings should not be flattened (treated as atomic)."""
    assert flatten_iterative(["hello", "world"]) == ["hello", "world"]
    assert flatten_iterative(["a", ["b", "c"]]) == ["a", "b", "c"]
    assert flatten_iterative([["ab", "cd"], "ef"]) == ["ab", "cd", "ef"]


def test_flatten_iterative_bytes_atomic():
    """Bytes and bytearray should not be flattened."""
    result = flatten_iterative([b"hello", [b"world"]])
    assert result == [b"hello", b"world"]

    ba = bytearray(b"test")
    result = flatten_iterative([ba, [1, 2]])
    assert result == [ba, 1, 2]


def test_flatten_iterative_numbers_preserved():
    """Numbers should be preserved as atomic values."""
    assert flatten_iterative([1, [2.5, [3+4j]], True]) == [1, 2.5, 3+4j, True]


def test_flatten_iterative_none_preserved():
    """None values should be preserved."""
    assert flatten_iterative([1, None, [2, None], 3]) == [1, None, 2, None, 3]


def test_flatten_iterative_generator():
    """Generators should be flattened correctly."""
    gen = (x for x in range(3))
    result = flatten_iterative([1, gen, 4])
    assert result == [1, 0, 1, 2, 4]


def test_flatten_iterative_nested_generators():
    """Nested structure with generators."""
    def gen():
        yield 1
        yield [2, 3]
        yield 4

    result = flatten_iterative(gen())
    assert result == [1, 2, 3, 4]


def test_flatten_iterative_order_preserved():
    """Left-to-right order should be preserved."""
    result = flatten_iterative([1, [2, 3], 4, [5, [6, 7]], 8])
    assert result == [1, 2, 3, 4, 5, 6, 7, 8]


def test_flatten_iterative_deeply_nested():
    """Very deep nesting should work without recursion errors."""
    nested = [1]
    for _ in range(100):
        nested = [nested]
    nested.append(2)
    result = flatten_iterative(nested)
    assert result == [1, 2]


def test_flatten_iterative_type_error_non_iterable():
    """Non-iterable input should raise TypeError."""
    with pytest.raises(TypeError, match="Expected an iterable"):
        flatten_iterative(42)

    with pytest.raises(TypeError, match="Expected an iterable"):
        flatten_iterative(None)


def test_flatten_iterative_cyclic_reference():
    """Self-referential structures should raise ValueError."""
    lst = [1, 2]
    lst.append(lst)

    with pytest.raises(ValueError, match="Cyclic reference detected"):
        flatten_iterative(lst)


def test_flatten_iterative_indirect_cycle():
    """Indirect cycles should be detected."""
    a = [1]
    b = [2, a]
    a.append(b)

    with pytest.raises(ValueError, match="Cyclic reference detected"):
        flatten_iterative(a)


@pytest.mark.parametrize("input_iter,expected", [
    ([1, 2, 3], [1, 2, 3]),
    ([1, [2], 3], [1, 2, 3]),
    ([(1, 2), [3, 4]], [1, 2, 3, 4]),
    ([[], [[], []]], []),
    ([[1], [2], [3]], [1, 2, 3]),
])
def test_flatten_iterative_parametrized(input_iter, expected):
    """Parametrized tests for various input patterns."""
    assert flatten_iterative(input_iter) == expected


def test_flatten_iterative_with_range():
    """Range objects should be flattened."""
    result = flatten_iterative([1, range(3), 4])
    assert result == [1, 0, 1, 2, 4]


def test_flatten_iterative_dict_keys_values():
    """Dict views (keys/values) should be flattened."""
    d = {1: 'a', 2: 'b'}
    result = flatten_iterative([0, d.keys(), 3])
    assert result == [0, 1, 2, 3]


def test_flatten_iterative_mixed_with_strings():
    """Complex nesting with strings preserved as atomic."""
    result = flatten_iterative([["hello", [1, 2]], ("world", [3, 4])])
    assert result == ["hello", 1, 2, "world", 3, 4]


