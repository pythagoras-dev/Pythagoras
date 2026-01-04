from pythagoras import PureCodePortal, pure
from pythagoras import _PortalTester
from pythagoras._210_basic_portals.portal_description_helpers import _get_description_value_by_key

from pythagoras._360_pure_code_portals.pure_core_classes import _CACHED_EXECUTION_RESULTS_TXT, \
    _EXECUTION_QUEUE_SIZE_TXT


def test_portal(tmpdir):

    with _PortalTester():
        portal = PureCodePortal(tmpdir)
        description = portal.describe()
        assert description.shape == (10, 3)

        assert _get_description_value_by_key(description
                                             , _CACHED_EXECUTION_RESULTS_TXT) == 0
        assert _get_description_value_by_key(description
                                             , _EXECUTION_QUEUE_SIZE_TXT) == 0


def f():
    return 1

def g():
    return 2

def test_stored_values(tmpdir):
    # tmpdir = 3*"STORED_VALUES_" +str(int(time.time()))

    global f,g

    with _PortalTester(PureCodePortal
            , tmpdir
            ) as t:

        f = pure()(f)
        g = pure()(g)
        f()
        g.swarm()

        description = t.portal.describe()

        assert _get_description_value_by_key(description
                                             , _CACHED_EXECUTION_RESULTS_TXT) == 1
        assert _get_description_value_by_key(description
                                             , _EXECUTION_QUEUE_SIZE_TXT) == 1










