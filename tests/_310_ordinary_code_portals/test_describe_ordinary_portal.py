from pythagoras._210_basic_portals.portal_description_helpers import _get_description_value_by_key
from pythagoras._310_ordinary_code_portals import OrdinaryCodePortal, ordinary
from pythagoras._210_basic_portals import _PortalTester
from pythagoras._310_ordinary_code_portals.ordinary_portal_core_classes import (
    _REGISTERED_FUNCTIONS_TXT)


def f():
    return 1

def g():
    return 2

def test_ordinary_portal(tmpdir):

    with (_PortalTester(OrdinaryCodePortal, tmpdir) as t):
        portal = t.portal

        description = portal.describe()
        assert _get_description_value_by_key(description
                                             , _REGISTERED_FUNCTIONS_TXT) == 0

        f_new = ordinary(portal = portal)(f)
        # Lazy registration - not registered yet
        description = portal.describe()
        assert _get_description_value_by_key(description
                                             , _REGISTERED_FUNCTIONS_TXT) == 0
        _ = f_new.portal  # Trigger registration
        description = portal.describe()
        assert _get_description_value_by_key(description
                                             , _REGISTERED_FUNCTIONS_TXT) == 1

        g_new = ordinary(portal=portal)(g)
        # Lazy registration - not registered yet
        description = portal.describe()
        assert _get_description_value_by_key(description
                                             , _REGISTERED_FUNCTIONS_TXT) == 1
        _ = g_new.portal  # Trigger registration
        description = portal.describe()
        assert _get_description_value_by_key(description
                                             , _REGISTERED_FUNCTIONS_TXT) == 2


