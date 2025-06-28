# from copy import deepcopy
#
# from parameterizable import sort_dict_by_keys
#
# from pythagoras import get_current_process_start_time, get_current_process_id
# from pythagoras._010_basic_portals.portal_tester import _PortalTester
# from pythagoras._090_swarming_portals.swarming_portals import (
#     SwarmingPortal, _process_random_execution_request)
# from src import pythagoras as pth
#
#
# def test_random_request_execution(tmpdir):
#
#     with _PortalTester(SwarmingPortal, tmpdir) as t:
#
#         @pth.pure()
#         def f(n):
#             return 5*n
#
#         address = f.swarm(n=10)
#
#         portal = t.portal
#
#         assert len(portal._execution_requests) == 1
#
#     init_params = deepcopy(t.portal.get_portable_params())
#     init_params["parent_process_id"] = get_current_process_id()
#     init_params["parent_process_start_time"] = get_current_process_start_time()
#     init_params["max_n_workers"] = 0
#     init_params = sort_dict_by_keys(init_params)
#
#     _process_random_execution_request(**init_params)
#
#     address._invalidate_cache()
#
#     with _PortalTester(SwarmingPortal, tmpdir) as t_new:
#         assert len(t.portal._execution_requests) == 0
#         assert address.ready
#         result = address.get()
#         assert result == 50
#         assert address.fn(n=-1) == -5
#         address._invalidate_cache()
#
#     with _PortalTester(SwarmingPortal, tmpdir) as t_new:
#         result = address.get()
#         assert result == 50
#         assert address.fn(n=-1) == -5
#
#
#
#
#
#
