from pythagoras._210_basic_portals.portal_tester import _PortalTester
from pythagoras._360_pure_code_portals.pure_core_classes import (
    PureCodePortal)
from pythagoras._360_pure_code_portals.pure_decorator import pure


def test_execution_attempts_simple(tmpdir):

    with _PortalTester(PureCodePortal, tmpdir):

        @pure(excessive_logging=True)
        def simple_func()->int:
            return 10

        assert len(simple_func.get_address().get_ValueAddr().get().execution_attempts) == 0
        assert simple_func() == 10
        assert len(simple_func.get_address().get_ValueAddr().get().execution_attempts) == 1



# def test_execution_attempts_weird(tmpdir):
#
#     with _PortalTester(PureCodePortal, tmpdir):
#
#         @pure()
#         def weird_func()->int:
#             import pythagoras as pth
#             if len(pth.all_autonomous_functions[pth.default_island_name]
#                    ["weird_func"].get_address().execution_attempts) < 3:
#                 return 10/0
#             return 10
#
#         assert len(weird_func.get_address().execution_attempts) == 0
#
#         with pytest.raises(ZeroDivisionError):
#             weird_func()
#         assert len(weird_func.get_address().execution_attempts) == 1
#         assert len(pth.default_portal._crash_history) == 1
#         assert len(pth.default_portal._execution_requests) == 1
#         assert len(pth.default_portal._execution_results) == 0
#
#         with pytest.raises(ZeroDivisionError):
#             weird_func()
#         assert len(weird_func.get_address().execution_attempts) == 2
#         assert len(pth.default_portal._crash_history) == 2
#         assert len(pth.default_portal._execution_requests) == 1
#         assert len(pth.default_portal._execution_results) == 0
#
#         assert weird_func() == 10
#         assert len(weird_func.get_address().execution_attempts) == 3
#         assert len(pth.default_portal._crash_history) == 2
#         assert len(pth.default_portal._execution_requests) == 0
#         assert len(pth.default_portal._execution_results) == 1