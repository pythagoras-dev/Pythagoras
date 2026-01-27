"""Tests for get_noncurrent_portals function."""
from pythagoras import _PortalTester, BasicPortal, get_noncurrent_portals


class HelperPortal(BasicPortal):
    """BasicPortal subclass for testing."""

    def __init__(self, path="default"):
        super().__init__(root_dict=path)


def test_get_noncurrent_portals_logic(tmp_path):
    """Verify get_noncurrent_portals returns correct portals in various states."""
    with _PortalTester():
        # Case 1: No portals
        assert len(get_noncurrent_portals()) == 0
        
        # Case 2: One portal, not active
        p1 = HelperPortal(str(tmp_path / "p1"))
        # It is created but not entered, so stack is empty.
        # Current is None (or undefined).
        assert get_noncurrent_portals() == {p1}
        
        # Case 3: One portal, active
        with p1:
            # p1 is active and current.
            # Non-current should be empty.
            assert len(get_noncurrent_portals()) == 0
            
        # Case 4: Two portals
        p2 = HelperPortal(str(tmp_path / "p2"))
        
        # None active
        # Current is None.
        # Both are non-current.
        result = get_noncurrent_portals()
        assert len(result) == 2
        assert p1 in result
        assert p2 in result
        
        # p1 active
        with p1:
            # p1 is current. p2 is non-current.
            # Note: p1 is active. p2 is non-active.
            assert get_noncurrent_portals() == {p2}
            
            # p2 active (nested)
            with p2:
                # p2 is current. p1 is active but not current.
                # So p1 should be in non-current?
                # Yes, "non-current" means "not the current one".
                # p1 is active, but not current.
                assert get_noncurrent_portals() == {p1}
