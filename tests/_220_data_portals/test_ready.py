from collections.abc import Mapping, Sequence
from pythagoras._220_data_portals import ready, HashAddr


class MockHashAddr(HashAddr):
    """Mock HashAddr class for testing."""
    def __init__(self, ready_value=True):
        super().__init__("aaaaaaaaaaaaa","bbbbbbbbbbbbbbbbb")
        self._ready = ready_value

    @property
    def ready(self):
        return self._ready

    def get(self, timeout=None, expected_type=None):
        return None


def test_ready_basic_objects():
    """Test that ready returns True for basic objects."""
    assert ready(1) is True
    assert ready(1.0) is True
    assert ready("string") is True
    assert ready(None) is True
    assert ready(True) is True
    assert ready(False) is True


def test_ready_hash_addr():
    """Test that ready returns the ready property for HashAddr objects."""
    # Test with ready=True
    hash_addr_ready = MockHashAddr(ready_value=True)
    assert ready(hash_addr_ready) is True

    # Test with ready=False
    hash_addr_not_ready = MockHashAddr(ready_value=False)
    assert ready(hash_addr_not_ready) is False


def test_ready_list():
    """Test that ready returns True if all items in a list are ready."""
    # List with all ready items
    assert ready([1, 2, 3]) is True

    # List with a not ready HashAddr
    not_ready_addr = MockHashAddr(ready_value=False)
    assert ready([1, not_ready_addr, 3]) is False

    # List with all ready HashAddr
    ready_addr1 = MockHashAddr(ready_value=True)
    ready_addr2 = MockHashAddr(ready_value=True)
    assert ready([ready_addr1, ready_addr2]) is True

    # Empty list
    assert ready([]) is True


def test_ready_tuple():
    """Test that ready returns True if all items in a tuple are ready."""
    # Tuple with all ready items
    assert ready((1, 2, 3)) is True

    # Tuple with a not ready HashAddr
    not_ready_addr = MockHashAddr(ready_value=False)
    assert ready((1, not_ready_addr, 3)) is False

    # Tuple with all ready HashAddr
    ready_addr1 = MockHashAddr(ready_value=True)
    ready_addr2 = MockHashAddr(ready_value=True)
    assert ready((ready_addr1, ready_addr2)) is True

    # Empty tuple
    assert ready(()) is True


def test_ready_dict():
    """Test that ready returns True if all values in a dict are ready."""
    # Dict with all ready values
    assert ready({"a": 1, "b": 2, "c": 3}) is True

    # Dict with a not ready HashAddr
    not_ready_addr = MockHashAddr(ready_value=False)
    assert ready({"a": 1, "b": not_ready_addr, "c": 3}) is False

    # Dict with all ready HashAddr
    ready_addr1 = MockHashAddr(ready_value=True)
    ready_addr2 = MockHashAddr(ready_value=True)
    assert ready({"a": ready_addr1, "b": ready_addr2}) is True

    # Empty dict
    assert ready({}) is True


def test_ready_nested_structures():
    """Test that ready works with nested structures."""
    # Nested list with all ready items
    assert ready([1, [2, 3], 4]) is True

    # Nested list with a not ready HashAddr
    not_ready_addr = MockHashAddr(ready_value=False)
    assert ready([1, [2, not_ready_addr], 4]) is False

    # Nested dict with all ready values
    assert ready({"a": 1, "b": {"c": 2, "d": 3}, "e": 4}) is True

    # Nested dict with a not ready HashAddr
    assert ready({"a": 1, "b": {"c": 2, "d": not_ready_addr}, "e": 4}) is False

    # Complex nested structure
    complex_structure = {
        "a": [1, 2, {"b": (3, 4)}],
        "c": {"d": [5, 6, 7]}
    }
    assert ready(complex_structure) is True

    # Complex nested structure with not ready HashAddr
    complex_structure_not_ready = {
        "a": [1, 2, {"b": (3, not_ready_addr)}],
        "c": {"d": [5, 6, 7]}
    }
    assert ready(complex_structure_not_ready) is False


def test_ready_circular_references():
    """Test that ready handles circular references correctly."""
    # Create circular reference in list
    circular_list = [1, 2, 3]
    circular_list.append(circular_list)
    assert ready(circular_list) is True

    # Create circular reference in dict
    circular_dict = {"a": 1, "b": 2}
    circular_dict["c"] = circular_dict
    assert ready(circular_dict) is True

    # Create circular reference with not ready HashAddr
    not_ready_addr = MockHashAddr(ready_value=False)
    circular_list_not_ready = [1, 2, not_ready_addr]
    circular_list_not_ready.append(circular_list_not_ready)
    assert ready(circular_list_not_ready) is False


def test_ready_custom_mapping_all_ready():
    """Test ready returns True for custom Mapping with all ready values."""
    class CustomMapping(Mapping):
        def __init__(self, data):
            self._data = data

        def __getitem__(self, key):
            return self._data[key]

        def __iter__(self):
            return iter(self._data)

        def __len__(self):
            return len(self._data)

    custom_map = CustomMapping({"a": 1, "b": 2})
    assert ready(custom_map) is True


def test_ready_custom_mapping_with_not_ready_hashaddr():
    """Test ready returns False for custom Mapping with not ready HashAddr."""
    class CustomMapping(Mapping):
        def __init__(self, data):
            self._data = data

        def __getitem__(self, key):
            return self._data[key]

        def __iter__(self):
            return iter(self._data)

        def __len__(self):
            return len(self._data)

    not_ready_addr = MockHashAddr(ready_value=False)
    custom_map = CustomMapping({"a": not_ready_addr})
    assert ready(custom_map) is False


def test_ready_custom_sequence_all_ready():
    """Test ready returns True for custom Sequence with all ready items."""
    class CustomSequence(Sequence):
        def __init__(self, items):
            self._items = list(items)

        def __getitem__(self, index):
            return self._items[index]

        def __len__(self):
            return len(self._items)

    custom_seq = CustomSequence([1, 2, 3])
    assert ready(custom_seq) is True


def test_ready_custom_sequence_with_not_ready_hashaddr():
    """Test ready returns False for custom Sequence with not ready HashAddr."""
    class CustomSequence(Sequence):
        def __init__(self, items):
            self._items = list(items)

        def __getitem__(self, index):
            return self._items[index]

        def __len__(self):
            return len(self._items)

    not_ready_addr = MockHashAddr(ready_value=False)
    custom_seq = CustomSequence([1, not_ready_addr, 3])
    assert ready(custom_seq) is False
