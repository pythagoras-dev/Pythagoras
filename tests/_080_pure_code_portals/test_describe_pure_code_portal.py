from src.pythagoras import PureCodePortal, pure
from src.pythagoras import _PortalTester

from src.pythagoras._010_basic_portals.basic_portal_class_OLD import get_description_value_by_key
from src.pythagoras._080_pure_code_portals.pure_core_classes import CACHED_EXECUTION_RESULTS_TXT, \
    EXECUTION_QUEUE_SIZE_TXT


def test_portal(tmpdir):

    with _PortalTester():
        portal = PureCodePortal(tmpdir)
        description = portal.describe()
        assert description.shape == (10, 3)

        assert get_description_value_by_key(description
            , CACHED_EXECUTION_RESULTS_TXT) == 0
        assert get_description_value_by_key(description
            , EXECUTION_QUEUE_SIZE_TXT) == 0


def f():
    return 1

def g():
    return 2

def test_stored_values(tmpdir):
    # tmpdir = 3*"STORED_VALUES_" +str(int(time.time()))

    global f,g

    with _PortalTester(PureCodePortal
            , tmpdir
            , p_consistency_checks = 0.5) as t:

        f = pure()(f)
        g = pure()(g)
        f()
        g.swarm()

        description = t.portal.describe()

        assert get_description_value_by_key(description
            , CACHED_EXECUTION_RESULTS_TXT) == 1
        assert get_description_value_by_key(description
            , EXECUTION_QUEUE_SIZE_TXT) == 1










