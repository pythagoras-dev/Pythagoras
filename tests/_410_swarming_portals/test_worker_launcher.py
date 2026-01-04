# from parameterizable import sort_dict_by_keys
#
# from pythagoras._210_basic_portals.portal_tester import _PortalTester
# from pythagoras._410_swarming_portals.swarming_portals import (
#     SwarmingPortal, _launch_many_background_workers)
# from src import pythagoras as pth
#
#
# def test_launch_many_background_workers(tmpdir):
#
#     with _PortalTester(SwarmingPortal, tmpdir, max_n_workers=0) as t:
#         portable_params = t.portal.get_portable_params()
#         portable_params["max_n_workers"] = t.portal.max_n_workers
#         portable_params = sort_dict_by_keys(portable_params)
#         _launch_many_background_workers(**portable_params)
#
#         @pth.pure()
#         def f():
#             return 5
#
#         address = f.swarm()
#         address._invalidate_cache()
#         assert address.get() == 5