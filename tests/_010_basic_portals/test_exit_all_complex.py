# import atexit
#
# from pythagoras import BasicPortal
# from pythagoras import _PortalTester
#
#
# def test_exit_all_complex(tmpdir):
#     with _PortalTester():
#         for i in range(3):
#             portal = BasicPortal(tmpdir+"_"+str(i))
#             portal.__enter__()
#         assert len(BasicPortal._active_portals_stack) == 3
#         with BasicPortal(tmpdir+"_AAAAA"):
#             assert len(BasicPortal._active_portals_stack) == 4
#             with BasicPortal(tmpdir+"_BBBBB"):
#                 assert len(BasicPortal._active_portals_stack) == 5
#                 with BasicPortal(tmpdir+"_CCCCC"):
#                     assert len(BasicPortal._active_portals_stack) == 6
#         assert len(BasicPortal._active_portals_stack) == 3
#         BasicPortal.__exit_all__()
#         assert len(BasicPortal._active_portals_stack) == 0