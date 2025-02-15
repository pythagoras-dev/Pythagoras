# from pythagoras import DefaultLocalPortal, BasicPortal, SwarmingPortal, _PortalTester
# import tempfile
# from unittest.mock import patch
# from pathlib import Path
# import pytest
# import pythagoras as pth
#
# @pytest.fixture
# def mock_path_home():
#     """Fixture to mock pathlib.Path.home to use a temporary directory."""
#     with tempfile.TemporaryDirectory() as temp_home:
#         with patch("pathlib.Path.home", return_value=Path(temp_home)):
#             yield Path(temp_home)
#
# def test_default_local_portal(mock_path_home):
#     with _PortalTester():
#         DefaultLocalPortal._clear_all()
#         portal_1 = DefaultLocalPortal()
#         portal_2 = DefaultLocalPortal()
#         portal_3 = DefaultLocalPortal()
#         assert len(BasicPortal._all_portals) == 1
#
#         assert ".pythagoras" in portal_1._root_dict.base_dir
#         assert ".default_portal" in portal_2._root_dict.base_dir
#         homepath = Path("~").expanduser()
#         assert str(mock_path_home) in portal_3._root_dict.base_dir
#         assert len(BasicPortal._entered_portals_stack) == 0
#
#         assert isinstance(portal_1, SwarmingPortal)
#         DefaultLocalPortal._clear_all()
#
# def f():
#     return 42
#
# def test_work_with_no_portal(mock_path_home):
#     with _PortalTester():
#         DefaultLocalPortal._clear_all()
#         assert len(BasicPortal._all_portals) == 0
#         f_pure = pth.pure()(f)
#         f_result = f_pure()
#         assert f_result == 42
#         assert len(BasicPortal._all_portals) == 1
#         portal = DefaultLocalPortal()
#         assert len(portal.execution_requests) == 0
#         assert len(portal.execution_results) == 1
#         assert len(portal.known_functions) == 1
#         assert len(BasicPortal._entered_portals_stack) == 0
#         DefaultLocalPortal._clear_all()
#
# def test_work_with_one_portal(mock_path_home, tmpdir):
#     DefaultLocalPortal._clear_all()
#     with _PortalTester(SwarmingPortal, tmpdir):
#         assert len(BasicPortal._all_portals) == 1
#         f_pure = pth.pure()(f)
#         f_result = f_pure()
#         assert f_result == 42
#         assert len(BasicPortal._all_portals) == 1
#         assert len(BasicPortal._entered_portals_stack) == 1
#         portal = DefaultLocalPortal()
#         assert len(BasicPortal._entered_portals_stack) == 1
#         assert len(BasicPortal._all_portals) == 2
#         assert len(portal.execution_requests) == 0
#         assert len(portal.execution_results) == 0
#         assert len(portal.known_functions) == 0
#     DefaultLocalPortal._clear_all()
#
#
# def test_work_with_two_portals(mock_path_home, tmpdir):
#     DefaultLocalPortal._clear_all()
#     with _PortalTester(SwarmingPortal, tmpdir):
#         assert len(BasicPortal._entered_portals_stack) == 1
#         with SwarmingPortal(tmpdir.mkdir("la-la-la")) as sw_portal_2:
#             assert len(BasicPortal._all_portals) == 2
#             assert len(BasicPortal._entered_portals_stack) == 2
#             f_pure = pth.pure()(f)
#             f_result = f_pure()
#             assert f_result == 42
#             assert len(BasicPortal._all_portals) == 2
#             assert len(sw_portal_2.known_functions) == 1
#         assert len(BasicPortal._entered_portals_stack) == 1
#         assert len(BasicPortal._all_portals) == 2
#         f_pure_new = pth.pure()(f)
#         f_result = f_pure_new()
#         # assert f_result == 42
#         # assert len(BasicPortal._all_portals) == 2
#         #
#         # for i in range(5):
#         #     d_portal = DefaultLocalPortal()
#         #     assert len(BasicPortal._all_portals) == 3
#         #
#         # assert len(d_portal.execution_requests) == 0
#         # assert len(d_portal.execution_results) == 0
#         # assert len(d_portal.known_functions) == 0
#         # assert len(BasicPortal._entered_portals_stack) == 1
#     DefaultLocalPortal._clear_all()
#
