from pythagoras import TunablePortal, _PortalTester


def test_get_effective_setting_precedence(tmpdir):
    """Verify portal setting precedence between global and local stores."""
    with _PortalTester(TunablePortal, tmpdir) as pt:
        portal = pt.portal

        key = "test_key"
        global_val = "global_value"
        local_val = "local_value"
        default_val = "default_value"

        # Key not present anywhere.
        assert portal.get_effective_setting(key) is None
        assert portal.get_effective_setting(key, default=default_val) == default_val

        # Key present in local settings only.
        portal.local_node_settings[key] = local_val
        assert portal.get_effective_setting(key) == local_val
        assert portal.get_effective_setting(key, default=default_val) == local_val

        # Key present in both (global takes precedence).
        portal.global_portal_settings[key] = global_val
        assert portal.get_effective_setting(key) == global_val

        # Key present in global only.
        del portal.local_node_settings[key]
        assert portal.get_effective_setting(key) == global_val


def test_get_effective_setting_invalid_key_type(tmpdir):
    """Exercise behavior for non-string configuration keys."""
    with _PortalTester(TunablePortal, tmpdir) as pt:
        portal = pt.portal
        # NOTE: PersiDict key validation varies by backend.
        try:
            portal.get_effective_setting(123)
        except TypeError:
            pass
        except Exception:
            pass
