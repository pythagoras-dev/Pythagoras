from pythagoras import get_base16_hash_signature, get_base32_hash_signature

def test_get_base32_hash_signature_basics():
    """Test basic determinism and uniqueness of base32 hash signatures."""
    s1 = get_base32_hash_signature("test")
    s2 = get_base32_hash_signature("test")
    s3 = get_base32_hash_signature("other")
    
    assert isinstance(s1, str)
    assert len(s1) > 0
    assert s1 == s2  # Deterministic
    assert s1 != s3  # Different inputs produce different hashes


def test_get_base32_hash_signature_format():
    """Test that base32 signatures use the correct alphabet."""
    sig = get_base32_hash_signature("test")
    
    # Base32 alphabet: 0-9 and a-v (32 characters total)
    valid_chars = "0123456789abcdefghijklmnopqrstuv"
    assert all(c in valid_chars for c in sig.lower())
    
    # Should not contain characters beyond 'v'
    invalid_chars = "wxyz"
    assert not any(c in invalid_chars for c in sig.lower())


def test_get_base32_hash_signature_relationship_to_base16():
    """Test relationship between base16 and base32 signatures."""
    obj = "test_object"
    
    base16_sig = get_base16_hash_signature(obj)
    base32_sig = get_base32_hash_signature(obj)
    
    # Both should be deterministic
    assert base16_sig == get_base16_hash_signature(obj)
    assert base32_sig == get_base32_hash_signature(obj)
    
    # They should be different representations
    assert base16_sig != base32_sig
    
    # Base32 should be shorter (more compact encoding)
    # SHA256: 64 hex chars -> ~52 base32 chars
    assert len(base32_sig) < len(base16_sig)


def test_get_base32_hash_signature_types():
    """Test base32 hash signature with various types."""
    h_str = get_base32_hash_signature("test")
    h_int = get_base32_hash_signature(123)
    h_list = get_base32_hash_signature([1, 2, 3])
    h_dict = get_base32_hash_signature({"key": "value"})
    
    # All should be different
    assert len({h_str, h_int, h_list, h_dict}) == 4
    
    # All should use valid base32 alphabet
    valid_chars = "0123456789abcdefghijklmnopqrstuv"
    for sig in [h_str, h_int, h_list, h_dict]:
        assert all(c in valid_chars for c in sig.lower())


def test_get_base32_hash_signature_edge_cases():
    """Test base32 hash signature with edge cases."""
    # Empty and None
    h_empty = get_base32_hash_signature("")
    h_none = get_base32_hash_signature(None)
    h_empty_list = get_base32_hash_signature([])
    
    assert h_empty != h_none
    assert h_none != h_empty_list
    
    # All should be valid base32
    valid_chars = "0123456789abcdefghijklmnopqrstuv"
    for sig in [h_empty, h_none, h_empty_list]:
        assert all(c in valid_chars for c in sig.lower())
