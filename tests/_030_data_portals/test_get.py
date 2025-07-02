from pythagoras._030_data_portals import get, HashAddr


class MockHashAddr(HashAddr):
    """Mock HashAddr class for testing."""
    def __init__(self, return_value):
        super().__init__("aaaaaaaaaaaaa", "bbbbbbbbbbbbbbbbbbb")
        self._return_value = return_value

    @property
    def ready(self):
        return True

    def get(self, timeout=None, expected_type=None):
        return self._return_value


def test_get_basic_objects():
    """Test that get returns the same object for basic objects."""
    assert get(1) == 1
    assert get(1.0) == 1.0
    assert get("string") == "string"
    assert get(None) is None
    assert get(True) is True
    assert get(False) is False


def test_get_hash_addr():
    """Test that get returns the result of the get method for HashAddr objects."""
    # Test with different return values
    hash_addr_int = MockHashAddr(return_value=42)
    assert get(hash_addr_int) == 42

    hash_addr_str = MockHashAddr(return_value="hello")
    assert get(hash_addr_str) == "hello"

    hash_addr_none = MockHashAddr(return_value=None)
    assert get(hash_addr_none) is None


def test_get_list():
    """Test that get returns a new list with get applied to each item."""
    # List with basic items
    assert get([1, 2, 3]) == [1, 2, 3]

    # List with HashAddr
    hash_addr = MockHashAddr(return_value=42)
    assert get([1, hash_addr, 3]) == [1, 42, 3]

    # List with multiple HashAddr
    hash_addr1 = MockHashAddr(return_value="hello")
    hash_addr2 = MockHashAddr(return_value="world")
    assert get([hash_addr1, hash_addr2]) == ["hello", "world"]

    # Empty list
    assert get([]) == []


def test_get_tuple():
    """Test that get returns a new tuple with get applied to each item."""
    # Tuple with basic items
    assert get((1, 2, 3)) == (1, 2, 3)

    # Tuple with HashAddr
    hash_addr = MockHashAddr(return_value=42)
    assert get((1, hash_addr, 3)) == (1, 42, 3)

    # Tuple with multiple HashAddr
    hash_addr1 = MockHashAddr(return_value="hello")
    hash_addr2 = MockHashAddr(return_value="world")
    assert get((hash_addr1, hash_addr2)) == ("hello", "world")

    # Empty tuple
    assert get(()) == ()


def test_get_dict():
    """Test that get returns a new dict with get applied to each value."""
    # Dict with basic values
    assert get({"a": 1, "b": 2, "c": 3}) == {"a": 1, "b": 2, "c": 3}

    # Dict with HashAddr
    hash_addr = MockHashAddr(return_value=42)
    assert get({"a": 1, "b": hash_addr, "c": 3}) == {"a": 1, "b": 42, "c": 3}

    # Dict with multiple HashAddr
    hash_addr1 = MockHashAddr(return_value="hello")
    hash_addr2 = MockHashAddr(return_value="world")
    assert get({"a": hash_addr1, "b": hash_addr2}) == {"a": "hello", "b": "world"}

    # Empty dict
    assert get({}) == {}


def test_get_nested_structures():
    """Test that get works with nested structures."""
    # Nested list with basic items
    assert get([1, [2, 3], 4]) == [1, [2, 3], 4]

    # Nested list with HashAddr
    hash_addr = MockHashAddr(return_value=42)
    assert get([1, [2, hash_addr], 4]) == [1, [2, 42], 4]

    # Nested dict with basic values
    assert get({"a": 1, "b": {"c": 2, "d": 3}, "e": 4}) == {"a": 1, "b": {"c": 2, "d": 3}, "e": 4}

    # Nested dict with HashAddr
    assert get({"a": 1, "b": {"c": 2, "d": hash_addr}, "e": 4}) == {"a": 1, "b": {"c": 2, "d": 42}, "e": 4}

    # Complex nested structure
    hash_addr1 = MockHashAddr(return_value="hello")
    hash_addr2 = MockHashAddr(return_value="world")
    complex_structure = {
        "a": [1, 2, {"b": (3, hash_addr1)}],
        "c": {"d": [5, hash_addr2, 7]}
    }
    expected_result = {
        "a": [1, 2, {"b": (3, "hello")}],
        "c": {"d": [5, "world", 7]}
    }
    assert get(complex_structure) == expected_result


def test_get_circular_references():
    """Test that get handles circular references correctly."""
    # Create circular reference in list
    circular_list = [1, 2, 3]
    circular_list.append(circular_list)
    result = get(circular_list)
    assert result[0] == 1
    assert result[1] == 2
    assert result[2] == 3
    assert result[3] is result  # The circular reference is preserved

    # Create circular reference in dict
    circular_dict = {"a": 1, "b": 2}
    circular_dict["c"] = circular_dict
    result = get(circular_dict)
    assert result["a"] == 1
    assert result["b"] == 2
    assert result["c"] is result  # The circular reference is preserved

    # Create circular reference with HashAddr
    hash_addr = MockHashAddr(return_value=42)
    circular_list_with_hash_addr = [1, 2, hash_addr]
    circular_list_with_hash_addr.append(circular_list_with_hash_addr)
    result = get(circular_list_with_hash_addr)
    assert result[0] == 1
    assert result[1] == 2
    assert result[2] == 42  # HashAddr is resolved
    assert result[3] is result  # The circular reference is preserved