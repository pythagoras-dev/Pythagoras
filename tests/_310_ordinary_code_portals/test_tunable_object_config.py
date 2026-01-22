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

def test_ordinary_fn_config_setting_roundtrip(tmpdir):
    """Test _get_config_setting and _set_config_setting roundtrip."""
    with _PortalTester(OrdinaryCodePortal, tmpdir) as pt:
        portal = pt.portal
        fn = OrdinaryFn(simple_function, portal=portal)

        # Set a function-specific config
        fn._set_config_setting("test_key", "test_value", portal)

        # Retrieve it
        value = fn._get_config_setting("test_key", portal)
        assert value == "test_value"


def test_ordinary_fn_config_portal_wide_fallback(tmpdir):
    """Test _get_config_setting uses portal-wide settings as fallback."""
    with _PortalTester(OrdinaryCodePortal, tmpdir) as pt:
        portal = pt.portal
        fn = OrdinaryFn(simple_function, portal=portal)

        # Set portal-wide config
        portal.global_portal_settings["fallback_key"] = "portal_value"

        # Function should get portal-wide value when no function-specific value exists
        value = fn._get_config_setting("fallback_key", portal)
        assert value == "portal_value"


def test_ordinary_fn_config_portal_overrides_function_specific(tmpdir):
    """Test portal-wide config takes precedence over function-specific."""
    with _PortalTester(OrdinaryCodePortal, tmpdir) as pt:
        portal = pt.portal
        fn = OrdinaryFn(simple_function, portal=portal)

        # Set both portal-wide and function-specific
        portal.global_portal_settings["key"] = "portal_value"
        fn._set_config_setting("key", "function_value", portal)

        # Portal-wide is checked first in current implementation
        value = fn._get_config_setting("key", portal)
        assert value == "portal_value"

def test_storable_fn_addr_property(tmpdir):
    """Test OrdinaryFn.addr property returns correct ValueAddr."""
    with _PortalTester(OrdinaryCodePortal, tmpdir):
        fn = OrdinaryFn(simple_function)
        addr = fn.addr

        from pythagoras._220_data_portals import ValueAddr
        assert isinstance(addr, ValueAddr)
        assert addr.descriptor == fn.__hash_addr_descriptor__()
        assert addr.ready

def test_ordinary_fn_config_setting_type_validation(tmpdir):
    """Test config methods reject invalid key types."""
    with _PortalTester(OrdinaryCodePortal, tmpdir) as pt:
        portal = pt.portal
        fn = OrdinaryFn(simple_function, portal=portal)

        with pytest.raises(TypeError, match="key must be a SafeStrTuple or a string"):
            fn._get_config_setting(123, portal)

        with pytest.raises(TypeError, match="key must be a SafeStrTuple or a string"):
            fn._set_config_setting(123, "value", portal)
