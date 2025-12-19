import pytest
from pythagoras._800_signatures_and_converters.hash_signatures import (
    get_base16_hash_signature,
    get_base32_hash_signature,
    get_hash_signature,
)

class SimpleObj:
    def __init__(self, val):
        self.val = val

def test_get_base16_hash_signature_basics():
    """Test basic usage of get_base16_hash_signature."""
    s1 = get_base16_hash_signature("hello")
    s2 = get_base16_hash_signature("hello")
    s3 = get_base16_hash_signature("world")

    assert isinstance(s1, str)
    assert len(s1) > 0
    assert s1 == s2
    assert s1 != s3
    
    # Check that it looks like hex
    int(s1, 16)

def test_get_base16_hash_signature_types():
    """Test get_base16_hash_signature with various types."""
    data_list = [1, 2, 3]
    data_dict = {"a": 1, "b": 2}
    
    h1 = get_base16_hash_signature(data_list)
    h2 = get_base16_hash_signature(data_dict)
    
    assert h1 != h2
    assert get_base16_hash_signature([1, 2, 3]) == h1
    assert get_base16_hash_signature({"a": 1, "b": 2}) == h2

def test_get_base32_hash_signature():
    """Test get_base32_hash_signature."""
    s1 = get_base32_hash_signature("test")
    s2 = get_base32_hash_signature("test")
    s3 = get_base32_hash_signature("other")
    
    assert s1 == s2
    assert s1 != s3
    assert s1 != get_base16_hash_signature("test")
    assert isinstance(s1, str)

def test_get_hash_signature():
    """Test get_hash_signature (shortened base32)."""
    obj = "long_string_to_ensure_hash_is_long_enough" * 10
    
    full_32 = get_base32_hash_signature(obj)
    short_sig = get_hash_signature(obj)
    
    assert short_sig == full_32[:22]
    assert len(short_sig) <= 22
    assert len(short_sig) > 0

def test_numpy_support():
    """Test numpy array hashing if numpy is available."""
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
    
    assert h1 == h2
    assert h1 != h3

def test_custom_object():
    """Test hashing of custom objects."""
    o1 = SimpleObj(10)
    o2 = SimpleObj(10)
    o3 = SimpleObj(20)
    
    h1 = get_base16_hash_signature(o1)
    h2 = get_base16_hash_signature(o2)
    h3 = get_base16_hash_signature(o3)
    
    assert h1 == h2
    assert h1 != h3
