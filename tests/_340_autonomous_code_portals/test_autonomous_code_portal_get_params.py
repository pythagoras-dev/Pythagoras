# from pythagoras import AutonomousCodePortal
# from pythagoras import _PortalTester
# # from parameterizable import get_object_from_portable_params
#
# def test_autonomous_portal_get_params(tmpdir):
#     with _PortalTester(AutonomousCodePortal, root_dict = tmpdir) as t:
#         portal = t.portal
#         params = portal.get_params()
#         exportable_params = portal.get_portable_params()
#         new_portal = get_object_from_portable_params(exportable_params)
#         new_params = new_portal.get_params()
#         new_exportable_params = new_portal.get_portable_params()
#         assert params == new_params
#         assert exportable_params == new_exportable_params
#
#
#
# def test_autonomous_data_portal_get_params_1(tmpdir):
#     with _PortalTester(AutonomousCodePortal
#             , root_dict = tmpdir):
#         portal = t.portal
#         params = portal.get_params()
#         exportable_params = portal.get_portable_params()
#         new_portal = get_object_from_portable_params(exportable_params)
#         new_params = new_portal.get_params()
#         new_exportable_params = new_portal.get_portable_params()
#         assert params == new_params
#         assert exportable_params == new_exportable_params
