"""Tests for get_portal_by_fingerprint functionality."""
import pytest
from pythagoras import (
    BasicPortal,
    _PortalTester,
    get_portal_by_fingerprint,
    get_all_known_portal_fingerprints
)


class CustomPortal(BasicPortal):
    """Custom portal subclass for type testing."""
    pass


def test_get_portal_by_valid_fingerprint(tmpdir):
    """Test retrieving a portal by its fingerprint."""
    with _PortalTester():
        portal1 = BasicPortal(tmpdir.mkdir("p1"))
        portal2 = BasicPortal(tmpdir.mkdir("p2"))

        fp1 = portal1.fingerprint
        fp2 = portal2.fingerprint

        # Should retrieve the correct portals
        assert get_portal_by_fingerprint(fp1) is portal1
        assert get_portal_by_fingerprint(fp2) is portal2


def test_get_portal_by_fingerprint_with_type_validation(tmpdir):
    """Test retrieving a portal with type validation."""
    with _PortalTester():
        basic_portal = BasicPortal(tmpdir.mkdir("basic"))
        custom_portal = CustomPortal(tmpdir.mkdir("custom"))

        basic_fp = basic_portal.fingerprint
        custom_fp = custom_portal.fingerprint

        # Should work when type matches
        assert get_portal_by_fingerprint(basic_fp, BasicPortal) is basic_portal
        assert get_portal_by_fingerprint(custom_fp, CustomPortal) is custom_portal

        # CustomPortal is also a BasicPortal
        assert get_portal_by_fingerprint(custom_fp, BasicPortal) is custom_portal


def test_get_portal_by_fingerprint_type_mismatch(tmpdir):
    """Test TypeError when portal type doesn't match required type."""
    with _PortalTester():
        basic_portal = BasicPortal(tmpdir.mkdir("basic"))
        basic_fp = basic_portal.fingerprint

        # Should raise TypeError when type doesn't match
        with pytest.raises(TypeError, match="not an instance of required"):
            get_portal_by_fingerprint(basic_fp, CustomPortal)


def test_get_portal_by_fingerprint_not_found(tmpdir):
    """Test KeyError when fingerprint doesn't exist."""
    with _PortalTester():
        portal = BasicPortal(tmpdir)

        # Use a non-existent fingerprint
        fake_fingerprint = "nonexistent_fingerprint_12345"

        with pytest.raises(KeyError, match="Portal with fingerprint"):
            get_portal_by_fingerprint(fake_fingerprint)


def test_get_portal_by_fingerprint_invalid_type(tmpdir):
    """Test TypeError when fingerprint is not a string."""
    with _PortalTester():
        portal = BasicPortal(tmpdir)

        # Pass non-string fingerprints
        with pytest.raises(TypeError, match="Expected PortalStrFingerprint"):
            get_portal_by_fingerprint(123)

        with pytest.raises(TypeError, match="Expected PortalStrFingerprint"):
            get_portal_by_fingerprint(None)

        with pytest.raises(TypeError, match="Expected PortalStrFingerprint"):
            get_portal_by_fingerprint(portal)


def test_get_portal_by_fingerprint_invalid_portal_type():
    """Test TypeError when required_portal_type is invalid."""
    with _PortalTester():
        # Should raise when portal_type is not a BasicPortal subclass
        with pytest.raises(TypeError, match="must be BasicPortal or one of its"):
            get_portal_by_fingerprint("some_fp", required_portal_type=str)

        with pytest.raises(TypeError, match="must be BasicPortal or one of its"):
            get_portal_by_fingerprint("some_fp", required_portal_type=int)
