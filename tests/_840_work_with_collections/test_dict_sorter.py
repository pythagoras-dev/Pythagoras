from src.pythagoras._840_work_with_collections import sort_dict_by_keys

import pytest


def test_sort_dict_by_keys_basic():
    """
    Test that the function correctly sorts a dictionary
    whose keys are in an arbitrary order.
    """
    unsorted_dict = {"c": 3, "a": 1, "b": 2}
    expected = {"a": 1, "b": 2, "c": 3}
    assert sort_dict_by_keys(unsorted_dict) == expected

def test_sort_dict_by_keys_already_sorted():
    """
    Test that the function returns the same dictionary
    if the keys are already sorted.
    """
    sorted_dict = {"a": 1, "b": 2, "c": 3}
    assert sort_dict_by_keys(sorted_dict) == sorted_dict

def test_sort_dict_by_keys_empty():
    """
    Test that the function handles an empty dictionary.
    """
    assert sort_dict_by_keys({}) == {}

def test_sort_dict_by_keys_single_key():
    """
    Test that the function works with a dictionary that has only one key.
    """
    single_key_dict = {"a": 1}
    assert sort_dict_by_keys(single_key_dict) == single_key_dict

def test_sort_dict_by_keys_case_sensitivity():
    """
    Test how the function handles case-sensitive sorting of keys.
    In ASCII, uppercase letters come before lowercase letters.
    """
    mixed_case_dict = {"b": 2, "A": 1, "C": 3}
    # Sorted order by key (ASCII-based): "A" < "C" < "b"
    expected = {"A": 1, "C": 3, "b": 2}
    assert sort_dict_by_keys(mixed_case_dict) == expected

def test_sort_dict_by_keys_numeric_strings():
    """
    Test that numeric strings as keys are also sorted correctly
    (lexicographically).
    """
    numeric_str_keys = {"10": "ten", "2": "two", "1": "one"}
    # Lexicographic sort: "1", "10", "2"
    expected = {"1": "one", "10": "ten", "2": "two"}
    assert sort_dict_by_keys(numeric_str_keys) == expected

def test_sort_dict_by_keys_assert_on_non_dict():
    """
    Test that the function raises an AssertionError
    when a non-dict is passed.
    """
    with pytest.raises(AssertionError):
        sort_dict_by_keys(["not", "a", "dict"])
