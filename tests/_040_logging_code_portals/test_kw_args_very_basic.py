
import pytest

from pythagoras._040_logging_code_portals import KwArgs


@pytest.fixture
def sample_sorted_kwargs():
    """
    Provide a fixture with some default key-value pairs.
    """
    return KwArgs(a=1, c=3, b=2)

def test_sorted_kwargs_initialization(sample_sorted_kwargs):
    """
    Test initialization and whether the internal state
    is (eventually) sorted by keys.
    """
    # Directly checking the dict order might be affected by Python's insertion order,
    # so let's call _re_sort and check.
    sample_sorted_kwargs.sort(inplace=True)
    assert list(sample_sorted_kwargs.keys()) == ["a", "b", "c"]
    assert list(sample_sorted_kwargs.values()) == [1, 2, 3]

def test_setitem_maintains_dictionary_behavior(sample_sorted_kwargs):
    """
    Test that setting an item works like a standard dict,
    except with the custom checks for types and nesting.
    """
    sample_sorted_kwargs["d"] = 4
    assert sample_sorted_kwargs["d"] == 4

def test_setitem_raises_typeerror_for_non_string_key(sample_sorted_kwargs):
    """
    Test that setitem raises a TypeError if the key is not a string.
    """
    with pytest.raises(KeyError):
        sample_sorted_kwargs[123] = "invalid key"

def test_setitem_raises_nested_kwargs_error():
    """
    Test that adding a KwArgs as a value raises NestedKwArgsError.
    """
    parent = KwArgs()
    child = KwArgs(x=10)
    with pytest.raises(ValueError):
        parent["child"] = child

def test_reduce_triggers_resort(sample_sorted_kwargs):
    """
    Test that calling __reduce__ triggers sorting of keys.
    """
    # Insert items out of order
    sample_sorted_kwargs["d"] = 4
    sample_sorted_kwargs["z"] = 26
    sample_sorted_kwargs["m"] = 13
    # Force the reduce
    sample_sorted_kwargs.__reduce__()
    # Now the keys should be sorted
    assert list(sample_sorted_kwargs.keys()) == ["a", "b", "c", "d", "m", "z"]