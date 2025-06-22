from src.pythagoras import OrdinaryCodePortal, ordinary
from src.pythagoras import _PortalTester
from src.pythagoras._010_basic_portals.basic_portal_core_classes_NEW import (
    _get_description_value_by_key)
from src.pythagoras._020_ordinary_code_portals.ordinary_portal_core_classes_NEW import (
    REGISTERED_FUNCTIONS_TXT)


def f():
    return 1

def g():
    return 2

def test_ordinary_portal(tmpdir):

    with (_PortalTester(OrdinaryCodePortal, tmpdir) as t):
        portal = t.portal

        description = portal.describe()
        assert _get_description_value_by_key(description
            , REGISTERED_FUNCTIONS_TXT) == 0

        f_new = ordinary(portal = portal)(f)
        description = portal.describe()
        assert _get_description_value_by_key(description
            ,REGISTERED_FUNCTIONS_TXT) == 1

        g_new = ordinary(portal=portal)(g)
        description = portal.describe()
        assert _get_description_value_by_key(description
            ,REGISTERED_FUNCTIONS_TXT) == 2


