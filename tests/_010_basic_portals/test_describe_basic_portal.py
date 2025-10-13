from pythagoras import BasicPortal
from pythagoras import _PortalTester
from pythagoras._010_basic_portals.basic_portal_core_classes import (
    _get_description_value_by_key, _BASE_DIRECTORY_TXT, _BACKEND_TYPE_TXT)


def test_portal(tmpdir):

    with _PortalTester():
        portal = BasicPortal(tmpdir)
        description = portal.describe()
        assert description.shape == (3, 3)

        assert _get_description_value_by_key(description
                                             , _BASE_DIRECTORY_TXT) == str(tmpdir)
        assert _get_description_value_by_key(description
                                             , _BACKEND_TYPE_TXT) == "FileDirDict"



