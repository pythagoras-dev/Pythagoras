from pythagoras import BasicPortal, OrdinaryCodePortal, ordinary
from pythagoras import _PortalTester
from pythagoras._010_basic_portals.basic_portal_core_classes import (
    get_description_value_by_key)
from pythagoras._020_ordinary_code_portals.ordinary_portal_core_classes import (
    REGISTERED_FUNCTIONS_TXT)


def f():
    return 1

def g():
    return 2

def test_ordinary_portal(tmpdir):

    with (_PortalTester(OrdinaryCodePortal, tmpdir) as t):
        portal = t.portal

        description = portal.describe()

        assert description.iloc[2, 2] == 0

        f_new = ordinary(portal = portal)(f)
        description = portal.describe()
        assert get_description_value_by_key(description
            ,REGISTERED_FUNCTIONS_TXT) == 1

        g_new = ordinary(portal=portal)(g)
        description = portal.describe()
        assert get_description_value_by_key(description
            ,REGISTERED_FUNCTIONS_TXT) == 2


