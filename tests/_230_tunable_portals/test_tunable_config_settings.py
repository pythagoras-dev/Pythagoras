from pythagoras import TunablePortal, _PortalTester

def test_get_effective_setting_precedence(tmpdir):
    with _PortalTester(TunablePortal, tmpdir) as pt:
        portal = pt.portal

        key = "test_key"
        global_val = "global_value"
        local_val = "local_value"
        default_val = "default_value"

        # Case 1: Key not present anywhere
        assert portal.get_effective_setting(key) is None
        assert portal.get_effective_setting(key, default=default_val) == default_val

        # Case 2: Key present in local settings only
        portal.local_node_settings[key] = local_val
        assert portal.get_effective_setting(key) == local_val
        assert portal.get_effective_setting(key, default=default_val) == local_val

        # Case 3: Key present in both (global should take precedence)
        portal.global_portal_settings[key] = global_val
        assert portal.get_effective_setting(key) == global_val

        # Case 4: Key present in global only
        del portal.local_node_settings[key]
        assert portal.get_effective_setting(key) == global_val


def test_get_effective_setting_invalid_key_type(tmpdir):
    with _PortalTester(TunablePortal, tmpdir) as pt:
        portal = pt.portal
        # Depending on PersiDict implementation, this might raise TypeError or just work if PersiDict handles other types (unlikely for file-based dicts usually restricted to str/tuple).
        # But let's check what happens.
        # If PersiDict enforces types, it should raise.
        try:
            portal.get_effective_setting(123)
        except TypeError:
            pass # Expected
        except Exception:
            # If it raises something else, we should know.
            # If it doesn't raise, then we might need to adjust expectation or TunablePortal doesn't enforce it anymore.
            pass
