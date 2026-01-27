"""Tests for BasicPortal.describe() method."""
from pythagoras import BasicPortal
from pythagoras import _PortalTester
from pythagoras._210_basic_portals.basic_portal_core_classes import (
    _BASE_DIRECTORY_TXT, _BACKEND_TYPE_TXT, _PYTHAGORAS_VERSION_TXT)
from pythagoras._210_basic_portals.portal_description_helpers import _get_description_value_by_key
from importlib import metadata


def test_portal(tmpdir):
    """Verify describe() returns DataFrame with correct shape and values."""
    with _PortalTester():
        portal = BasicPortal(tmpdir)
        description = portal.describe()
        assert description.shape == (3, 3)

        assert _get_description_value_by_key(description
                                             , _BASE_DIRECTORY_TXT) == str(tmpdir)
        assert _get_description_value_by_key(description
                                             , _BACKEND_TYPE_TXT) == "FileDirDict"


def test_portal_description_contains_all_fields(tmpdir):
    """Test that portal description contains all expected fields."""
    with _PortalTester():
        portal = BasicPortal(tmpdir)
        description = portal.describe()

        # Verify shape
        assert description.shape == (3, 3)
        assert list(description.columns) == ["type", "name", "value"]

        # Verify all three rows are present and correct
        base_dir = _get_description_value_by_key(description, _BASE_DIRECTORY_TXT)
        backend_type = _get_description_value_by_key(description, _BACKEND_TYPE_TXT)
        pythagoras_version = _get_description_value_by_key(description, _PYTHAGORAS_VERSION_TXT)

        # Check values
        assert base_dir == str(tmpdir)
        assert backend_type == "FileDirDict"
        assert pythagoras_version == metadata.version("pythagoras")

        # Check types (Disk vs Runtime)
        base_dir_row = description[description['name'] == _BASE_DIRECTORY_TXT].iloc[0]
        backend_type_row = description[description['name'] == _BACKEND_TYPE_TXT].iloc[0]
        version_row = description[description['name'] == _PYTHAGORAS_VERSION_TXT].iloc[0]

        assert base_dir_row['type'] == "Disk"
        assert backend_type_row['type'] == "Disk"
        assert version_row['type'] == "Runtime"



