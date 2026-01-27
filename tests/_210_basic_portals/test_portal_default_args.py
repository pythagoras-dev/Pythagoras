"""Tests for portal accessor functions with default arguments."""
import pytest
from pythagoras._210_basic_portals.basic_portal_core_classes import _clear_all_portals, BasicPortal
from pythagoras import (
    count_known_portals,
    get_known_portals,
    count_active_portals,
    measure_active_portals_stack,
    get_current_portal,
    get_nonactive_portals,
    get_noncurrent_portals
)


def test_default_args_behavior(tmpdir):
    """Verify accessor functions work correctly with default arguments."""
    _clear_all_portals()
    # Create a portal
    p1 = BasicPortal(tmpdir)
    
    # Check default arg (should count p1)
    assert count_known_portals() == 1
    assert get_known_portals() == {p1}
    
    # Check explicit BasicPortal arg
    assert count_known_portals(BasicPortal) == 1
    assert get_known_portals(BasicPortal) == {p1}
    
    # Check that None is NOT allowed anymore (raises TypeError from validation)
    with pytest.raises(TypeError):
        count_known_portals(None)
        
    with p1:
        assert count_active_portals() == 1
        assert count_active_portals(BasicPortal) == 1
        assert measure_active_portals_stack() == 1
        assert get_current_portal() == p1
        
        with pytest.raises(TypeError):
            count_active_portals(None)
            
    # Check non-active/non-current
    # Need another portal
    p2 = BasicPortal(str(tmpdir)+"/2")
    
    with p1:
        assert p2 in get_nonactive_portals()
        assert p2 in get_nonactive_portals(BasicPortal)
        assert p2 in get_noncurrent_portals()
        assert p2 in get_noncurrent_portals(BasicPortal)
        
        with pytest.raises(TypeError):
             get_nonactive_portals(None)

