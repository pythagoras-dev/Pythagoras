from copy import deepcopy
from src.pythagoras._010_basic_portals.portal_tester import _PortalTester
from src.pythagoras._090_swarming_portals.swarming_portals import (
    SwarmingPortal, _process_random_execution_request)
from src import pythagoras as pth


def test_random_request_execution(tmpdir):

    with _PortalTester(SwarmingPortal, tmpdir) as t:

        @pth.pure()
        def f(n):
            return 5*n

        address = f.swarm(n=10)

        init_params = deepcopy(t.portal.__get_portable_params__())
        init_params["runtime_id"] = None

    _process_random_execution_request(**init_params)

    address._invalidate_cache()

    with _PortalTester(SwarmingPortal, tmpdir) as t_new:
        address._portal = t_new.portal
        result = address.get()
        assert result == 50
        assert address.fn(n=-1) == -5






