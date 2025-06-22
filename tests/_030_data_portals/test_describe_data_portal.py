from src.pythagoras import DataPortal
from src.pythagoras import _PortalTester

from src.pythagoras._010_basic_portals.basic_portal_core_classes import _get_description_value_by_key
from src.pythagoras._030_data_portals.data_portal_core_classes import TOTAL_VALUES_TXT, \
    PROBABILITY_OF_CHECKS_TXT


def test_portal(tmpdir):

    with _PortalTester():
        portal = DataPortal(tmpdir)
        description = portal.describe()
        assert description.shape == (5, 3)
        assert _get_description_value_by_key(description
            , TOTAL_VALUES_TXT) == 0
        assert _get_description_value_by_key(description
            , PROBABILITY_OF_CHECKS_TXT) == 0

def test_portal_with_consistency_checks(tmpdir):

    with _PortalTester():
        portal = DataPortal(tmpdir, p_consistency_checks = 1)
        description = portal.describe()
        assert description.shape == (5, 3)
        assert _get_description_value_by_key(description
            , TOTAL_VALUES_TXT) == 0
        assert _get_description_value_by_key(description
            , PROBABILITY_OF_CHECKS_TXT) == 1


def test_stored_values(tmpdir):
    # tmpdir = 25*"Q" +str(int(time.time()))

    with _PortalTester(DataPortal
            , tmpdir
            , p_consistency_checks = 0.5) as t:
        t.portal._value_store["a"] = 100
        t.portal._value_store["b"] = 200
        description = t.portal.describe()
        assert description.shape == (5, 3)
        assert _get_description_value_by_key(description
            , TOTAL_VALUES_TXT) == 2
        assert _get_description_value_by_key(description
            , PROBABILITY_OF_CHECKS_TXT) == 0.5







