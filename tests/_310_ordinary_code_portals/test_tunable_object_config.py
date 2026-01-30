import pytest
from pythagoras import _PortalTester
from pythagoras._310_ordinary_code_portals import OrdinaryCodePortal, OrdinaryFn

def simple_function(x, y):
    return x + y

def test_tunable_object_config_persistence(tmpdir):
    with _PortalTester(OrdinaryCodePortal, tmpdir) as pt:
        portal = pt.portal
        fn = OrdinaryFn(simple_function, portal=portal)
        
        # Inject an auxiliary param for testing purposes
        fn._auxiliary_config_params_at_init["my_param"] = "test_value"
        
        # Trigger first visit
        fn._first_visit_to_portal(portal)
        
        # Verify persistence in local_node_settings
        # We expect the key to be (fn, "my_param") or similar.
        # Check if the value is present.
        
        # Since OrdinaryFn has .addr, the key used is (fn.addr, "my_param")
        assert (fn.addr, "my_param") in portal.local_node_settings
        assert portal.local_node_settings[(fn.addr, "my_param")] == "test_value"

def test_tunable_object_first_visit_creates_addr(tmpdir):
    """Test first visit to portal creates function address (moved from old test)."""
    with _PortalTester(OrdinaryCodePortal, tmpdir) as pt:
        portal = pt.portal
        fn = OrdinaryFn(simple_function)

        # Before visit, function may not have registered addr (or fully initialized connection)
        # But OrdinaryFn(..., portal=portal) might do it? 
        # Here we pass portal=None in constructor.
        
        # Trigger first visit
        fn._first_visit_to_portal(portal)

        # After visit, addr should be created/ready
        assert hasattr(fn, "addr")
        assert fn.addr.ready

def test_storable_fn_addr_property(tmpdir):
    """Test OrdinaryFn.addr property returns correct ValueAddr."""
    with _PortalTester(OrdinaryCodePortal, tmpdir):
        fn = OrdinaryFn(simple_function)
        addr = fn.addr

        from pythagoras._220_data_portals import ValueAddr
        assert isinstance(addr, ValueAddr)
        assert addr.descriptor == fn.__hash_addr_descriptor__()
        assert addr.ready

