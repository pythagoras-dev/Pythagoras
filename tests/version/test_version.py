import re

import pytest

import pythagoras


def test_version_exists():
    """
    Test that __version__ attribute exists and is accessible.
    """
    assert hasattr(pythagoras, '__version__')
    assert pythagoras.__version__ is not None


def test_version_is_string():
    """
    Test that __version__ is a string.
    """
    assert isinstance(pythagoras.__version__, str)
    assert len(pythagoras.__version__) > 0


def test_version_follows_semantic_versioning():
    """
    Test that __version__ follows semantic versioning format (X.Y.Z).
    """
    # Basic semantic versioning pattern: major.minor.patch
    # May also include pre-release identifiers (alpha, beta, rc)
    semver_pattern = r'^\d+\.\d+\.\d+(?:[-.]?(?:a|alpha|b|beta|rc|dev)\d*)?$'
    assert re.match(semver_pattern, pythagoras.__version__)


def test_version_accessible_from_metadata():
    """
    Test that __version__ can be accessed and is consistent with importlib.metadata.
    """
    from importlib import metadata
    
    # Test that we can get version from metadata (this is how it's implemented)
    try:
        metadata_version = metadata.version("pythagoras")
        # The __version__ should match what metadata reports
        assert pythagoras.__version__ == metadata_version
    except Exception as e:
        # If metadata lookup fails, at least ensure __version__ exists and is valid
        pytest.fail(f"Could not retrieve version from metadata: {e}")


def test_version_format_compatibility():
    """
    Test that __version__ can be compared and parsed as a version string.
    """
    # Split version into components
    parts = pythagoras.__version__.split('.')

    # Verify we can parse major, minor, patch version numbers
    assert len(parts) >= 3
    assert all(p.isdigit() for p in parts[:3])

    major = int(parts[0])
    minor = int(parts[1])
    patch = int(parts[2])

    # Test that version components are integers >= 0
    assert major >= 0
    assert minor >= 0
    assert patch >= 0


# def test_version_in_all():
#     """
#     Test that __version__ is included in the __all__ list.
#     """
#     assert '__version__' in pythagoras.__all__