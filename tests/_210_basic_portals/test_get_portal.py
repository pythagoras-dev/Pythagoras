"""Tests for get_current_portal function."""
from pythagoras import (
    BasicPortal,
    _PortalTester,
    get_current_portal,
)
import pytest


def test_portal_nested(tmpdir):
    """Verify get_current_portal returns correct portal in nested contexts."""
    with _PortalTester():

        portal = BasicPortal(tmpdir.mkdir("p1"))
        portal2 = BasicPortal(tmpdir.mkdir("p2"))
        portal3 = BasicPortal(tmpdir.mkdir("p3"))

        with portal:
            assert get_current_portal() == portal
            with portal2:
                assert get_current_portal() == portal2
                _portal4 = BasicPortal(tmpdir.mkdir("p4"))
                with portal3:
                    assert get_current_portal() == portal3
                    with portal2:
                        assert get_current_portal() == portal2
                    assert get_current_portal() == portal3
                assert get_current_portal() == portal2
            assert get_current_portal() == portal


def test_get_current_portal_no_portals_no_instantiator():
    """Test get_current_portal raises when no portals exist and no instantiator set."""
    from pythagoras._210_basic_portals.basic_portal_core_classes import _clear_all_portals

    _clear_all_portals()

    # Should raise RuntimeError
    with pytest.raises(RuntimeError):
        get_current_portal()
