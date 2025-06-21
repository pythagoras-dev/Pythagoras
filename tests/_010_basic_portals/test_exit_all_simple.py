#
# from pythagoras import BasicPortal, _PortalTester
#
# def test_exit_all_simple(tmpdir):
#     with _PortalTester():
#         for i in range(3):
#             portal = BasicPortal(tmpdir+"_"+str(i))
#             portal.__enter__()
#         assert len(BasicPortal._active_portals_stack) == 3
#         BasicPortal.__exit_all__()
#         assert len(BasicPortal._active_portals_stack) == 0
