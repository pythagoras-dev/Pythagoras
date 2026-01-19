
import pytest
from pythagoras import (
    BasicPortal,
    _PortalTester,
    get_known_portals,
    count_known_portals,
    count_active_portals,
    measure_active_portals_stack,
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
             get_known_portals(required_portal_type=PortalA)
             
        with pytest.raises(TypeError):
             count_known_portals(required_portal_type=PortalA)
             
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
                 count_active_portals(required_portal_type=PortalB)
                 
             with pytest.raises(TypeError):
                 measure_active_portals_stack(required_portal_type=PortalB)

             # stack has pA(PortalA). required=PortalA. OK.
             assert count_active_portals(required_portal_type=PortalA) == 1
             assert measure_active_portals_stack(required_portal_type=PortalA) == 1

