import pytest
from pythagoras._220_data_portals import HashAddr


class MockHashAddr(HashAddr):
    """Mock HashAddr for testing abstract base class."""
    @property
    def ready(self):
        return True

    def get(self, timeout=None, expected_type=None):
        return None


def test_hash_addr_basic_construction():
    """Test HashAddr construction with valid inputs."""
    addr = MockHashAddr("test_descriptor", "abcdefghij")
    assert addr.descriptor == "test_descriptor"
    assert addr.hash_signature == "abcdefghij"
    assert addr.shard == "abc"
    assert addr.subshard == "def"
    assert addr.hash_tail == "ghij"


def test_hash_addr_rejects_non_string_descriptor():
    """Test that HashAddr raises TypeError for non-string descriptor."""
    with pytest.raises(TypeError, match="descriptor and hash_signature must be strings"):
        MockHashAddr(123, "abcdefghij")


def test_hash_addr_rejects_non_string_hash():
    """Test that HashAddr raises TypeError for non-string hash."""
    with pytest.raises(TypeError, match="descriptor and hash_signature must be strings"):
        MockHashAddr("descriptor", 123)


def test_hash_addr_rejects_empty_descriptor():
    """Test that HashAddr raises ValueError for empty descriptor."""
    with pytest.raises(ValueError, match="descriptor and hash_signature must not be empty"):
        MockHashAddr("", "abcdefghij")


def test_hash_addr_rejects_empty_hash():
    """Test that HashAddr raises ValueError for empty hash."""
    with pytest.raises(ValueError, match="descriptor and hash_signature must not be empty"):
        MockHashAddr("descriptor", "")


def test_hash_addr_rejects_short_hash():
    """Test that HashAddr raises ValueError for hash shorter than 10 chars."""
    with pytest.raises(ValueError, match="hash_signature must be at least 10 characters"):
        MockHashAddr("descriptor", "short")


def test_hash_addr_from_strings_valid():
    """Test HashAddr.from_strings() reconstructs address correctly."""
    addr = MockHashAddr.from_strings(
        descriptor="test_desc",
        hash_signature="1234567890abc",
        assert_readiness=False
    )
    assert addr.descriptor == "test_desc"
    assert addr.hash_signature == "1234567890abc"
    assert addr.shard == "123"
    assert addr.subshard == "456"
    assert addr.hash_tail == "7890abc"


def test_hash_addr_from_strings_rejects_non_string():
    """Test from_strings() raises TypeError for non-string inputs."""
    with pytest.raises(TypeError, match="descriptor and hash_signature must be strings"):
        MockHashAddr.from_strings(descriptor=123, hash_signature="abcdefghij")


def test_hash_addr_from_strings_rejects_empty():
    """Test from_strings() raises ValueError for empty strings."""
    with pytest.raises(ValueError, match="descriptor and hash_signature must not be empty"):
        MockHashAddr.from_strings(descriptor="", hash_signature="abcdefghij")


def test_hash_addr_equality():
    """Test HashAddr equality compares type and strings."""
    addr1 = MockHashAddr("desc", "abcdefghij")
    addr2 = MockHashAddr("desc", "abcdefghij")
    addr3 = MockHashAddr("desc", "xxxxxxxxxx")

    assert addr1 == addr2
    assert addr1 != addr3


def test_hash_addr_hash_consistency_with_equality():
    """Verify hash/equality contract: equal objects must have equal hashes."""
    addr1 = MockHashAddr("desc", "abcdefghij")
    addr2 = MockHashAddr("desc", "abcdefghij")

    assert addr1 == addr2
    assert hash(addr1) == hash(addr2)


def test_hash_addr_usable_in_sets():
    """Verify HashAddr instances can be used in sets correctly."""
    addr1 = MockHashAddr("desc", "abcdefghij")
    addr2 = MockHashAddr("desc", "abcdefghij")
    addr3 = MockHashAddr("desc", "xxxxxxxxxx")

    addr_set = {addr1, addr2, addr3}
    assert len(addr_set) == 2  # addr1 and addr2 are equal, so only 2 unique


def test_hash_addr_usable_as_dict_keys():
    """Verify HashAddr instances can be used as dictionary keys correctly."""
    addr1 = MockHashAddr("desc", "abcdefghij")
    addr2 = MockHashAddr("desc", "abcdefghij")

    d = {addr1: "value1"}
    d[addr2] = "value2"

    assert len(d) == 1  # addr1 and addr2 are equal, so same key
    assert d[addr1] == "value2"  # Updated by addr2


def test_hash_addr_build_descriptor_basic():
    """Test _build_descriptor() with basic types."""
    assert "int" in HashAddr._build_descriptor(42).lower()
    assert "str" in HashAddr._build_descriptor("hello").lower()
    assert "list" in HashAddr._build_descriptor([1, 2, 3]).lower()


def test_hash_addr_build_descriptor_with_len():
    """Test _build_descriptor() includes length for objects with __len__."""
    descriptor = HashAddr._build_descriptor([1, 2, 3])
    assert "_len_3" in descriptor


def test_hash_addr_build_descriptor_with_custom_method():
    """Test _build_descriptor() uses custom __hash_addr_descriptor__ if available."""
    class CustomObj:
        def __hash_addr_descriptor__(self):
            return "custom_descriptor"

    obj = CustomObj()
    assert HashAddr._build_descriptor(obj) == "custom_descriptor"


def test_hash_addr_build_hash_signature():
    """Test _build_hash_signature() returns base32 hash."""
    sig = HashAddr._build_hash_signature(42)
    assert isinstance(sig, str)
    assert len(sig) > 0
    # Base32 uses 0-9 and a-v
    assert all(c in "0123456789abcdefghijklmnopqrstuv" for c in sig)
