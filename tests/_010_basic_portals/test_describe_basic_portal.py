from src.pythagoras import BasicPortal
from src.pythagoras import _PortalTester
from src.pythagoras._010_basic_portals.basic_portal_core_classes_NEW import (
    get_description_value_by_key, BASE_DIRECTORY_TXT, BACKEND_TYPE_TXT)


def test_portal(tmpdir):

    with _PortalTester():
        portal = BasicPortal(tmpdir)
        description = portal.describe()
        assert description.shape == (2, 3)

        assert get_description_value_by_key(description
            , BASE_DIRECTORY_TXT) == str(tmpdir)
        assert get_description_value_by_key(description
            , BACKEND_TYPE_TXT) == "FileDirDict"



