
from pythagoras import DataPortal
from pythagoras import _PortalTester
from pythagoras._210_basic_portals.portal_description_helpers import _get_description_value_by_key

from pythagoras._220_data_portals.data_portal_core_classes import _TOTAL_VALUES_TXT


def test_portal(tmpdir):

    with _PortalTester():
        portal = DataPortal(tmpdir)
        description = portal.describe()
        assert description.shape == (4, 3)
        assert _get_description_value_by_key(description
                                             , _TOTAL_VALUES_TXT) == 0


def test_stored_values(tmpdir):
    # tmpdir = 25*"Q" +str(int(time.time()))

    with _PortalTester(DataPortal
            , tmpdir
            ) as t:
        t.portal.global_value_store["a"] = 100
        t.portal.global_value_store["b"] = 200
        description = t.portal.describe()
        assert description.shape == (4, 3)
        assert _get_description_value_by_key(description
                                             , _TOTAL_VALUES_TXT) == 2


def test_portal_auxiliary_param_names(tmpdir):
    """Test auxiliary_param_names property is available."""
    with _PortalTester(DataPortal, tmpdir) as t:
        param_names = t.portal.auxiliary_param_names
        # root_dict is a base parameter, not auxiliary
        assert isinstance(param_names, set)





