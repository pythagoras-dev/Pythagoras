from pythagoras import (
    BasicPortal,
    _PortalTester,
    get_current_portal,
    get_all_known_portal_fingerprints
)
import pytest


def test_portal_nested(tmpdir):

    with _PortalTester():

        portal = BasicPortal(tmpdir)
        portal2 = BasicPortal(tmpdir)
        portal3 = BasicPortal(tmpdir)

        with portal:
            assert get_current_portal() == portal
            with portal2:
                assert get_current_portal() == portal2
                portal4 = BasicPortal(tmpdir)
                with portal3:
                    assert get_current_portal() == portal3
                    with portal2:
                        assert get_current_portal() == portal2
                    assert get_current_portal() == portal3
                assert get_current_portal() == portal2
            assert get_current_portal() == portal


def test_get_all_known_portal_fingerprints_empty():
    """Test getting fingerprints when no portals exist."""
    with _PortalTester():
        fingerprints = get_all_known_portal_fingerprints()
        assert fingerprints == set()


def test_get_all_known_portal_fingerprints_multiple(tmpdir):
    """Test getting fingerprints for multiple portals."""
    with _PortalTester():
        portal1 = BasicPortal(tmpdir.mkdir("p1"))
        portal2 = BasicPortal(tmpdir.mkdir("p2"))
        portal3 = BasicPortal(tmpdir.mkdir("p3"))

        fingerprints = get_all_known_portal_fingerprints()

        assert len(fingerprints) == 3
        assert portal1.fingerprint in fingerprints
        assert portal2.fingerprint in fingerprints
        assert portal3.fingerprint in fingerprints


def test_get_all_known_portal_fingerprints_type_validation(tmpdir):
    """Test type validation for get_all_known_portal_fingerprints."""

    class CustomPortal(BasicPortal):
        pass

    with _PortalTester():
        basic_portal = BasicPortal(tmpdir.mkdir("basic"))
        custom_portal = CustomPortal(tmpdir.mkdir("custom"))

        # Should work with BasicPortal (includes both)
        fingerprints = get_all_known_portal_fingerprints(BasicPortal)
        assert len(fingerprints) == 2

        # Should fail when requiring CustomPortal (basic_portal doesn't match)
        with pytest.raises(TypeError, match="not an instance of required"):
            get_all_known_portal_fingerprints(CustomPortal)


def test_get_all_known_portal_fingerprints_invalid_type():
    """Test TypeError when required_portal_type is invalid."""
    with _PortalTester():
        with pytest.raises(TypeError, match="must be BasicPortal or one of its"):
            get_all_known_portal_fingerprints(str)

        with pytest.raises(TypeError, match="must be BasicPortal or one of its"):
            get_all_known_portal_fingerprints(int)