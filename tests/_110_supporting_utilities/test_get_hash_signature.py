from pythagoras import get_base32_hash_signature, get_hash_signature


def test_get_hash_signature_basics():
    """Test basic properties of shortened hash signature."""
    sig = get_hash_signature("test")
    
    assert isinstance(sig, str)
    assert len(sig) == 22  # Should be exactly 22 characters
    
    # Should be deterministic
    assert sig == get_hash_signature("test")
    
    # Different inputs should produce different signatures
    assert sig != get_hash_signature("other")


def test_get_hash_signature_length():
    """Test that get_hash_signature always returns exactly 22 characters."""
    test_objects = [
        "",
        "short",
        "a" * 1000,
        123,
        [1, 2, 3],
        {"key": "value"},
        None,
        (1, 2, 3, 4, 5),
    ]
    
    for obj in test_objects:
        sig = get_hash_signature(obj)
        assert len(sig) == 22, f"Expected length 22, got {len(sig)} for {obj}"


def test_get_hash_signature_is_prefix():
    """Test that get_hash_signature returns the first 22 chars of base32."""
    obj = "test_object_for_prefix_check"
    
    full_base32 = get_base32_hash_signature(obj)
    short_sig = get_hash_signature(obj)
    
    assert short_sig == full_base32[:22]
    assert len(short_sig) == 22


def test_get_hash_signature_format():
    """Test that shortened signature uses valid base32 alphabet."""
    sig = get_hash_signature("test")
    
    valid_chars = "0123456789abcdefghijklmnopqrstuv"
    assert all(c in valid_chars for c in sig.lower())


def test_get_hash_signature_uniqueness():
    """Test that shortened signatures maintain reasonable uniqueness."""
    # Generate signatures for many different objects
    signatures = set()
    n_objects = 1000
    
    for i in range(n_objects):
        sig = get_hash_signature(f"object_{i}")
        signatures.add(sig)
    
    # All should be unique (collision probability is extremely low)
    assert len(signatures) == n_objects


def test_get_hash_signature_types():
    """Test shortened signature with various types."""
    sigs = [
        get_hash_signature("string"),
        get_hash_signature(42),
        get_hash_signature([1, 2, 3]),
        get_hash_signature({"a": 1}),
        get_hash_signature(None),
    ]
    
    # All should be 22 characters
    assert all(len(sig) == 22 for sig in sigs)
    
    # All should be unique
    assert len(set(sigs)) == len(sigs)
