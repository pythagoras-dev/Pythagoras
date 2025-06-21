# from pythagoras._010_basic_portals.portal_tester import _PortalTester
# from pythagoras._040_logging_code_portals.logging_portal_core_classes import (
#     LoggingCodePortal, log_event)
# import time

# def test_event_logging_basic(tmpdir):
#     with _PortalTester(LoggingCodePortal, tmpdir) as p:
#         assert len(p.portal._event_history) == 0
#         log_event("Hello, world!")
#         assert len(p.portal._event_history) == 1
#
# def test_exception_logging_basic(tmpdir):
#     # tmpdir = 20*"Q"+str(int(time.time()))
#     with _PortalTester(LoggingCodePortal, tmpdir) as p:
#         assert len(p.portal._crash_history) == 0
#         try:
#             raise ValueError("This is a test exception.")
#         except ValueError as e:
#             LoggingCodePortal._exception_logger()
#         assert len(p.portal._crash_history) == 1
#
#
# def test_exception_logging_nested(tmpdir):
#     # tmpdir = 20*"Q"+str(int(time.time()))
#     # dir_2 = tmpdir+"D2"
#     dir_2 = tmpdir.mkdir("D2")
#     with _PortalTester(LoggingCodePortal, tmpdir) as p1:
#         with LoggingCodePortal(dir_2) as portal_2:
#             assert len(p1.portal._crash_history) == 0
#             assert len(portal_2._crash_history) == 0
#             try:
#                 raise ValueError("This is a test exception.")
#             except ValueError as e:
#                 LoggingCodePortal._exception_logger()
#             assert len(p1.portal._crash_history) == 1
#             assert len(portal_2._crash_history) == 1
