import pytest
from pythagoras._210_basic_portals import _PortalTester
from pythagoras._330_data_portals import DataPortal, StorableFn, ValueAddr
from persidict import KEEP_CURRENT, DELETE_CURRENT


def simple_function(x, y):
    """Simple test function."""
    return x + y


def test_storable_fn_addr_property(tmpdir):
    """Test StorableFn.addr property returns correct ValueAddr."""
    with _PortalTester(DataPortal, tmpdir):
        fn = StorableFn(simple_function)
        addr = fn.addr

        assert isinstance(addr, ValueAddr)
        assert addr.descriptor == fn.__hash_addr_descriptor__()
        assert addr.ready


def test_storable_fn_config_setting_roundtrip(tmpdir):
    """Test _get_config_setting and _set_config_setting roundtrip."""
    with _PortalTester(DataPortal, tmpdir) as pt:
        portal = pt.portal
        fn = StorableFn(simple_function, portal=portal)

        # Set a function-specific config
        fn._set_config_setting("test_key", "test_value", portal)

        # Retrieve it
        value = fn._get_config_setting("test_key", portal)
        assert value == "test_value"


def test_storable_fn_config_portal_wide_fallback(tmpdir):
    """Test _get_config_setting uses portal-wide settings as fallback."""
    with _PortalTester(DataPortal, tmpdir) as pt:
        portal = pt.portal
        fn = StorableFn(simple_function, portal=portal)

        # Set portal-wide config
        portal._set_portal_config_setting("fallback_key", "portal_value")

        # Function should get portal-wide value when no function-specific value exists
        value = fn._get_config_setting("fallback_key", portal)
        assert value == "portal_value"


def test_storable_fn_config_function_specific_overrides_portal(tmpdir):
    """Test function-specific config takes precedence over portal-wide."""
    with _PortalTester(DataPortal, tmpdir) as pt:
        portal = pt.portal
        fn = StorableFn(simple_function, portal=portal)

        # Set both portal-wide and function-specific
        portal._set_portal_config_setting("key", "portal_value")
        fn._set_config_setting("key", "function_value", portal)

        # Function-specific should NOT override (portal-wide is checked first)
        value = fn._get_config_setting("key", portal)
        assert value == "portal_value"


def test_storable_fn_config_setting_type_validation(tmpdir):
    """Test config methods reject invalid key types."""
    with _PortalTester(DataPortal, tmpdir) as pt:
        portal = pt.portal
        fn = StorableFn(simple_function, portal=portal)

        with pytest.raises(TypeError, match="key must be a SafeStrTuple or a string"):
            fn._get_config_setting(123, portal)

        with pytest.raises(TypeError, match="key must be a SafeStrTuple or a string"):
            fn._set_config_setting(123, "value", portal)


def test_storable_fn_first_visit_creates_addr(tmpdir):
    """Test first visit to portal creates function address."""
    with _PortalTester(DataPortal, tmpdir) as pt:
        portal = pt.portal
        fn = StorableFn(simple_function)

        # Before visit, function may not have registered addr
        initial_store_len = len(portal._value_store)

        # Trigger first visit
        fn._first_visit_to_portal(portal)

        # After visit, addr should be created
        assert hasattr(fn, "addr")
        assert fn.addr.ready
