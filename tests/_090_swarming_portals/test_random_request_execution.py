from copy import deepcopy

from parameterizable import sort_dict_by_keys

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

        assert len(t.portal._execution_requests) == 1

        init_params = deepcopy(t.portal.get_portable_params())
        init_params["principal_runtime_id"] = t.portal._principal_runtime_id
        init_params["principal_process_id"] = t.portal._principal_process_id
        init_params = sort_dict_by_keys(init_params)

        _process_random_execution_request(**init_params)

        assert len(t.portal._execution_requests) == 0
        assert address.ready

        address._invalidate_cache()
        result = address.get()
        assert result == 50
        assert address.fn(n=-1) == -5
        address._invalidate_cache()

    with _PortalTester(SwarmingPortal, tmpdir) as t_new:
        result = address.get()
        assert result == 50
        assert address.fn(n=-1) == -5






