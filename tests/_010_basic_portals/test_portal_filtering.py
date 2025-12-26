
import pytest
from pythagoras import (
    BasicPortal,
    _PortalTester,
    get_number_of_known_portals,
    get_all_known_portals,
    get_number_of_active_portals,
    get_depth_of_active_portal_stack,
    get_current_portal,
    get_nonactive_portals,
    get_noncurrent_portals
)

class PortalA(BasicPortal): pass
class PortalB(BasicPortal): pass
class PortalC(BasicPortal): pass

def test_filtering(tmpdir):
    with _PortalTester():
        # Setup
        pA1 = PortalA(tmpdir + "/a1")
        pA2 = PortalA(tmpdir + "/a2")
        pB1 = PortalB(tmpdir + "/b1")
        pC1 = PortalC(tmpdir + "/c1") # Just known, never active
        
        # Known portals
        assert get_number_of_known_portals() == 4
        assert get_number_of_known_portals(target_portal_type=PortalA) == 2
        assert get_number_of_known_portals(target_portal_type=PortalB) == 1
        assert get_number_of_known_portals(target_portal_type=PortalC) == 1
        
        assert set(get_all_known_portals()) == {pA1, pA2, pB1, pC1}
        assert set(get_all_known_portals(target_portal_type=PortalA)) == {pA1, pA2}
        assert set(get_all_known_portals(target_portal_type=PortalB)) == {pB1}
        
        with pA1:
            with pB1:
                with pA1: # Re-entry
                     
                     # Active portals (unique)
                     # Stack: [pA1, pB1, pA1]
                     # Unique: {pA1, pB1}
                     assert get_number_of_active_portals() == 2 
                     assert get_number_of_active_portals(target_portal_type=PortalA) == 1 # pA1 is active (unique count)
                     assert get_number_of_active_portals(target_portal_type=PortalB) == 1
                     assert get_number_of_active_portals(target_portal_type=PortalC) == 0
                     
                     # Depth
                     assert get_depth_of_active_portal_stack() == 3
                     assert get_depth_of_active_portal_stack(target_portal_type=PortalA) == 2
                     assert get_depth_of_active_portal_stack(target_portal_type=PortalB) == 1
                     assert get_depth_of_active_portal_stack(target_portal_type=PortalC) == 0

                     # Current portal
                     assert get_current_portal() == pA1
                     
                     # Non-active
                     # Active unique are {pA1, pB1}
                     # Known are {pA1, pA2, pB1, pC1}
                     # Non-active are {pA2, pC1}
                     assert set(get_nonactive_portals()) == {pA2, pC1}
                     assert set(get_nonactive_portals(target_portal_type=PortalA)) == {pA2}
                     assert set(get_nonactive_portals(target_portal_type=PortalB)) == set()
                     assert set(get_nonactive_portals(target_portal_type=PortalC)) == {pC1}
                     
                     # Non-current
                     # Current is pA1 (top of stack)
                     # Non-current: {pA2, pB1, pC1}
                     assert set(get_noncurrent_portals()) == {pA2, pB1, pC1}
                     assert set(get_noncurrent_portals(target_portal_type=PortalA)) == {pA2}
                     assert set(get_noncurrent_portals(target_portal_type=PortalB)) == {pB1}
                     assert set(get_noncurrent_portals(target_portal_type=PortalC)) == {pC1}

