import pytest

from pythagoras import ConfigurablePortal, _PortalTester
from persidict import KEEP_CURRENT, DELETE_CURRENT


def test_get_portal_config_setting_rejects_invalid_key_type(tmpdir):
    with _PortalTester(ConfigurablePortal, tmpdir) as pt:
        portal = pt.portal
        with pytest.raises(TypeError, match="key must be a SafeStrTuple or a string"):
            portal._get_portal_config_setting(123)


def test_set_portal_config_setting_rejects_invalid_key_type(tmpdir):
    with _PortalTester(ConfigurablePortal, tmpdir) as pt:
        portal = pt.portal
        with pytest.raises(TypeError, match="key must be a SafeStrTuple or a string"):
            portal._set_portal_config_setting(123, "value")


def test_set_portal_config_setting_keep_current_noop(tmpdir):
    with _PortalTester(ConfigurablePortal, tmpdir) as pt:
        portal = pt.portal

        portal._set_portal_config_setting("a", KEEP_CURRENT)
        assert "a" not in portal._portal_config_settings
        assert "a" not in portal._portal_config_settings_cache

        portal._set_portal_config_setting("a", 1)
        portal._set_portal_config_setting("a", KEEP_CURRENT)
        assert portal._portal_config_settings["a"] == 1
        assert portal._portal_config_settings_cache["a"] == 1


def test_set_portal_config_setting_delete_current_removes_entries(tmpdir):
    with _PortalTester(ConfigurablePortal, tmpdir) as pt:
        portal = pt.portal

        portal._set_portal_config_setting("a", 1)
        assert "a" in portal._portal_config_settings
        assert portal._portal_config_settings_cache["a"] == 1

        portal._set_portal_config_setting("a", DELETE_CURRENT)
        assert "a" not in portal._portal_config_settings
        assert "a" not in portal._portal_config_settings_cache
        assert portal._get_portal_config_setting("a") is None


def test_get_portal_config_setting_prefers_cache_until_invalidated(tmpdir):
    with _PortalTester(ConfigurablePortal, tmpdir) as pt:
        portal = pt.portal

        portal._set_portal_config_setting("a", 1)
        assert portal._get_portal_config_setting("a") == 1

        portal._portal_config_settings["a"] = 2
        assert portal._get_portal_config_setting("a") == 1

        portal._invalidate_cache()
        assert portal._get_portal_config_setting("a") == 2


def test_get_portal_config_setting_caches_none_until_invalidated(tmpdir):
    with _PortalTester(ConfigurablePortal, tmpdir) as pt:
        portal = pt.portal

        assert portal._get_portal_config_setting("missing") is None
        assert portal._portal_config_settings_cache["missing"] is None

        portal._portal_config_settings["missing"] = 5
        assert portal._get_portal_config_setting("missing") is None

        portal._invalidate_cache()
        assert portal._get_portal_config_setting("missing") == 5