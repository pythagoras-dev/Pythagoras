import pytest
from pythagoras import get_base16_hash_signature


class SimpleObj:
    """Simple test class for custom object hashing."""
    def __init__(self, val):
        self.val = val


def test_get_base16_hash_signature_basics():
    """Test basic determinism and uniqueness of base16 hash signatures."""
    s1 = get_base16_hash_signature("hello")
    s2 = get_base16_hash_signature("hello")
    s3 = get_base16_hash_signature("world")

    assert isinstance(s1, str)
    assert len(s1) > 0
    assert s1 == s2  # Deterministic
    assert s1 != s3  # Different inputs produce different hashes
    
    # Verify it's valid hexadecimal
    int(s1, 16)


def test_get_base16_hash_signature_format():
    """Test that base16 signatures are valid hexadecimal strings."""
    sig = get_base16_hash_signature("test")
    
    # Should be valid hex (only 0-9, a-f)
    assert all(c in "0123456789abcdef" for c in sig.lower())
    
    # Should be parseable as hex
    int(sig, 16)
    
    # SHA256 produces 64 hex characters
    assert len(sig) == 64


def test_get_base16_hash_signature_types():
    """Test base16 hash signature with various Python types."""
    # Strings
    h_str = get_base16_hash_signature("test")
    
    # Numbers
    h_int = get_base16_hash_signature(42)
    h_float = get_base16_hash_signature(3.14)
    h_bool = get_base16_hash_signature(True)
    
    # Collections
    h_list = get_base16_hash_signature([1, 2, 3])
    h_tuple = get_base16_hash_signature((1, 2, 3))
    h_dict = get_base16_hash_signature({"a": 1, "b": 2})
    h_set = get_base16_hash_signature({1, 2, 3})
    
    # All should be different
    all_hashes = [h_str, h_int, h_float, h_bool, h_list, h_tuple, h_dict, h_set]
    assert len(set(all_hashes)) == len(all_hashes)
    
    # Deterministic for same input
    assert get_base16_hash_signature([1, 2, 3]) == h_list
    assert get_base16_hash_signature({"a": 1, "b": 2}) == h_dict


def test_get_base16_hash_signature_edge_cases():
    """Test base16 hash signature with edge cases."""
    # Empty string
    h_empty_str = get_base16_hash_signature("")
    assert isinstance(h_empty_str, str)
    assert len(h_empty_str) == 64
    
    # Empty collections
    h_empty_list = get_base16_hash_signature([])
    h_empty_dict = get_base16_hash_signature({})
    h_empty_tuple = get_base16_hash_signature(())
    
    # All should be valid and different
    assert h_empty_str != h_empty_list
    assert h_empty_list != h_empty_dict
    assert h_empty_dict != h_empty_tuple
    
    # None
    h_none = get_base16_hash_signature(None)
    assert isinstance(h_none, str)
    assert len(h_none) == 64
    
    # Zero
    h_zero = get_base16_hash_signature(0)
    assert isinstance(h_zero, str)
    assert h_zero != h_none


def test_get_base16_hash_signature_special_chars():
    """Test base16 hash signature with special characters and unicode."""
    # Special characters
    h1 = get_base16_hash_signature("hello\nworld")
    h2 = get_base16_hash_signature("hello\tworld")
    h3 = get_base16_hash_signature("hello world")
    
    assert h1 != h2 != h3
    
    # Unicode
    h_unicode = get_base16_hash_signature("hello 世界 🌍")
    assert isinstance(h_unicode, str)
    assert len(h_unicode) == 64
    
    # Should be deterministic
    assert h_unicode == get_base16_hash_signature("hello 世界 🌍")


def test_get_base16_hash_signature_nested_structures():
    """Test base16 hash signature with nested data structures."""
    nested_list = [[1, 2], [3, [4, 5]]]
    nested_dict = {"a": {"b": 1, "c": {"d": 2}}}
    
    h1 = get_base16_hash_signature(nested_list)
    h2 = get_base16_hash_signature(nested_dict)
    
    assert h1 != h2
    assert h1 == get_base16_hash_signature([[1, 2], [3, [4, 5]]])
    assert h2 == get_base16_hash_signature({"a": {"b": 1, "c": {"d": 2}}})


def test_get_base16_hash_signature_order_sensitivity():
    """Test that base16 hash is sensitive to order in lists but not dicts."""
    # Lists are order-sensitive
    h1 = get_base16_hash_signature([1, 2, 3])
    h2 = get_base16_hash_signature([3, 2, 1])
    assert h1 != h2
    
    # Dicts should be consistent (joblib handles dict ordering)
    h3 = get_base16_hash_signature({"a": 1, "b": 2})
    h4 = get_base16_hash_signature({"b": 2, "a": 1})
    assert h3 == h4


def test_get_base16_hash_signature_custom_objects():
    """Test base16 hash signature with custom objects."""
    o1 = SimpleObj(10)
    o2 = SimpleObj(10)
    o3 = SimpleObj(20)
    
    h1 = get_base16_hash_signature(o1)
    h2 = get_base16_hash_signature(o2)
    h3 = get_base16_hash_signature(o3)
    
    assert isinstance(h1, str)
    assert len(h1) == 64
    assert h1 == h2  # Same attribute values
    assert h1 != h3  # Different attribute values


def test_get_base16_hash_signature_numpy():
    """Test base16 hash signature with numpy arrays if available."""
    try:
        import numpy as np
    except ImportError:
        pytest.skip("Numpy not installed")
    
    arr1 = np.array([1, 2, 3])
    arr2 = np.array([1, 2, 3])
    arr3 = np.array([4, 5, 6])
    
    h1 = get_base16_hash_signature(arr1)
    h2 = get_base16_hash_signature(arr2)
    h3 = get_base16_hash_signature(arr3)
    
    assert h1 == h2  # Same content
    assert h1 != h3  # Different content
    
    # Test different dtypes
    arr_int = np.array([1, 2, 3], dtype=np.int32)
    arr_float = np.array([1.0, 2.0, 3.0], dtype=np.float64)
    
    h_int = get_base16_hash_signature(arr_int)
    h_float = get_base16_hash_signature(arr_float)
    
    # Different dtypes should produce different hashes
    assert h_int != h_float
