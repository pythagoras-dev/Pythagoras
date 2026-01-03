
import pytest
from pythagoras import (
    BasicPortal,
    _PortalTester,
    get_all_known_portals,
    get_number_of_known_portals,
    get_number_of_active_portals,
    get_depth_of_active_portal_stack,
    get_nonactive_portals,
    get_noncurrent_portals
)

class PortalA(BasicPortal): pass
class PortalB(BasicPortal): pass

def test_strict_type_checking(tmpdir):
    with _PortalTester():
        pA = PortalA(tmpdir + "/a")
        pB = PortalB(tmpdir + "/b")
        
        # known_portals has pA(PortalA) and pB(PortalB)
        
        # Should raise because pB is not PortalA
        with pytest.raises(TypeError):
             get_all_known_portals(required_portal_type=PortalA)
             
        with pytest.raises(TypeError):
             get_number_of_known_portals(required_portal_type=PortalA)
             
        # Non-active check (both are inactive)
        with pytest.raises(TypeError):
             get_nonactive_portals(required_portal_type=PortalA)
             
        # Non-current check (both are non-current)
        with pytest.raises(TypeError):
             get_noncurrent_portals(required_portal_type=PortalA)

        with pA:
             # Active: pA. Stack: [pA]
             # unique active: {pA}. pA is PortalA. This should OK?
             # Wait, if I ask for PortalB?
             
             # Stack has pA. required=PortalB. pA is not PortalB. Raise.
             with pytest.raises(TypeError):
                 get_number_of_active_portals(required_portal_type=PortalB)
                 
             with pytest.raises(TypeError):
                 get_depth_of_active_portal_stack(required_portal_type=PortalB)

             # stack has pA(PortalA). required=PortalA. OK.
             assert get_number_of_active_portals(required_portal_type=PortalA) == 1
             assert get_depth_of_active_portal_stack(required_portal_type=PortalA) == 1

