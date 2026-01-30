from pythagoras import TunableObject, TunablePortal, _PortalTester, ValueAddr

class ConcreteTunable(TunableObject):
    def __init__(self, portal=None):
        super().__init__(portal)
    
    def __getstate__(self):
        return {"a": 1}
        
    def __setstate__(self, state):
        super().__setstate__(state)

class ConcreteTunableWithAddr(ConcreteTunable):
    @property
    def addr(self):
        return ValueAddr("test_addr_12345")

def test_tunable_object_effective_setting_default(tmpdir):
    """Test get_effective_setting works with default addr behavior."""
    with _PortalTester(TunablePortal, tmpdir) as pt:
        portal = pt.portal
        obj = ConcreteTunable(portal)

        # Initially empty
        assert obj.get_effective_setting("key") is None

        # Set via local_node_settings
        obj.local_node_settings["key"] = "local_val"
        assert obj.get_effective_setting("key") == "local_val"

        # Set via global_portal_settings (object-scoped)
        obj.global_portal_settings["key"] = "global_val"
        # Global takes precedence over local
        assert obj.get_effective_setting("key") == "global_val"

        # Remove global, local should be used
        del obj.global_portal_settings["key"]
        assert obj.get_effective_setting("key") == "local_val"

        # Portal-wide setting should override object-level settings
        portal.global_portal_settings["key"] = "portal_wide_val"
        assert obj.get_effective_setting("key") == "portal_wide_val"

def test_tunable_object_effective_setting_addr(tmpdir):
    """Test get_effective_setting works with addr (if available)."""
    with _PortalTester(TunablePortal, tmpdir) as pt:
        portal = pt.portal
        obj = ConcreteTunableWithAddr(portal)
        
        # Verify it uses addr for storage
        # We access portal settings directly to verify key usage
        addr_key = obj.addr
        
        obj.local_node_settings["key"] = "val"
        
        # Check portal structure directly
        # local_node_settings is a PersiDict. get_subdict(addr) creates sub-keys.
        
        sub = portal.local_node_settings.get_subdict(addr_key)
        assert sub["key"] == "val"
        
        # identity_key should NOT have it (unless identity == addr, which is not true here)
        # Note: ConcreteTunableWithAddr doesn't override identity_key, so it uses default hash.
        # ValueAddr("test_addr_12345") is distinct from object hash.
        sub_ident = portal.local_node_settings.get_subdict(obj.identity_key)
        assert "key" not in sub_ident

        assert obj.get_effective_setting("key") == "val"
