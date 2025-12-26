from pythagoras._010_basic_portals.basic_portal_core_classes import (
    BasicPortal, _PORTAL_REGISTRY
)
import pytest

# We will import get_noncurrent_portals inside the test to allow creating the file 
# before the function exists, although proper TDD would imply defining it first or 
# accepting import error. 
# But to run the test I need the function to exist. 
# So I will implement the function immediately after creating this file.

class HelperPortal(BasicPortal):
    def __init__(self, path="default"):
        super().__init__(root_dict=path)

def test_get_noncurrent_portals_logic(tmp_path):
    from pythagoras._010_basic_portals.basic_portal_core_classes import get_noncurrent_portals
    
    _PORTAL_REGISTRY.clear()
    
    # Case 1: No portals
    assert len(get_noncurrent_portals()) == 0
    
    # Case 2: One portal, not active
    p1 = HelperPortal(str(tmp_path / "p1"))
    # It is created but not entered, so stack is empty.
    # Current is None (or undefined).
    assert get_noncurrent_portals() == [p1]
    
    # Case 3: One portal, active
    with p1:
        # p1 is active and current.
        # Non-current should be empty.
        assert get_noncurrent_portals() == []
        
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
        assert get_noncurrent_portals() == [p2]
        
        # p2 active (nested)
        with p2:
            # p2 is current. p1 is active but not current.
            # So p1 should be in non-current?
            # Yes, "non-current" means "not the current one".
            # p1 is active, but not current.
            assert get_noncurrent_portals() == [p1]
            
    _PORTAL_REGISTRY.clear()
