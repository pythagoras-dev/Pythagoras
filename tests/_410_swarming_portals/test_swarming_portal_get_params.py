

# from parameterizable import get_object_from_portable_params

# def test_swarming_portal_get_params(tmpdir):
#     with _PortalTester(SwarmingPortal, root_dict = tmpdir) as t:
#         portal = t.portal
#         params = portal.get_params()
#         exportable_params = portal.get_portable_params()
#
#     new_portal = get_object_from_portable_params(exportable_params)
#     new_params = new_portal.get_params()
#     new_exportable_params = new_portal.get_portable_params()
#     assert params == new_params
#     assert exportable_params == new_exportable_params



# def test_swarming_data_portal_get_params_1(tmpdir):
#     with _PortalTester(SwarmingPortal
#             , root_dict = tmpdir
#             
#             , max_n_workers = 5) as t:
#         portal = t.portal
#         params = portal.get_params()
#         assert params["p_consistency_checks"] == 0.5
#         assert params["max_n_workers"] == 5
#         exportable_params = portal.get_portable_params()
#         assert exportable_params["max_n_workers"] == 5
#         params_json = mixinforge.dumps(portal)
#
#
#     with _PortalTester():
#         # new_portal = get_object_from_portable_params(exportable_params)
#         # new_params = new_portal.get_params()
#         # new_exportable_params = new_portal.get_portable_params()
#         # assert params == new_params
#         # assert exportable_params == new_exportable_params
#         new_portal_J2 = mixinforge.loads(params_json)
#         new_params_J2 = new_portal_J2.get_params()
#         assert params == new_params_J2
#
#
#     updated_params = json.loads(params_json)
#     updated_params[mixinforge.json_processor._Markers.PARAMS][mixinforge.json_processor._Markers.DICT]["max_n_workers"] = 0
#     updated_params_json = json.dumps(updated_params)
#     print()