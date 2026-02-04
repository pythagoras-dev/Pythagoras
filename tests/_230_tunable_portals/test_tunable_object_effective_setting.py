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

        assert obj.get_effective_setting("key") is None

        obj.local_node_settings["key"] = "local_val"
        assert obj.get_effective_setting("key") == "local_val"

        obj.global_portal_settings["key"] = "global_val"
        assert obj.get_effective_setting("key") == "global_val"

        del obj.global_portal_settings["key"]
        assert obj.get_effective_setting("key") == "local_val"

        portal.global_portal_settings["key"] = "portal_wide_val"
        assert obj.get_effective_setting("key") == "portal_wide_val"


def test_tunable_object_effective_setting_addr(tmpdir):
    """Test get_effective_setting works with addr (if available)."""
    with _PortalTester(TunablePortal, tmpdir) as pt:
        portal = pt.portal
        obj = ConcreteTunableWithAddr(portal)

        addr_key = obj.addr

        obj.local_node_settings["key"] = "val"

        # Verify settings are stored under the addr-specific subdict.
        sub = portal.local_node_settings.get_subdict(addr_key)
        assert sub["key"] == "val"

        # identity_key uses the default hash, not the addr.
        sub_ident = portal.local_node_settings.get_subdict(obj.identity_key)
        assert "key" not in sub_ident

        assert obj.get_effective_setting("key") == "val"
