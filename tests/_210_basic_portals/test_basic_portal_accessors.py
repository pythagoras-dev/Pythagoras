"""Tests for basic portal accessor functions."""


from pythagoras import (
    BasicPortal,
    count_known_portals,
    get_known_portals,
    count_active_portals,
    measure_active_portals_stack,
    get_nonactive_portals,
    _PortalTester,
)


def test_get_number_of_known_portals_no_portals():
    """Verify count is zero when no portals exist."""
    with _PortalTester():
        count = count_known_portals()
        assert count == 0


def test_get_number_of_known_portals_single_portal(tmp_path):
    """Verify count is correct with one portal."""
    with _PortalTester():
        _portal = BasicPortal(root_dict=str(tmp_path / "p1"))
        count = count_known_portals()
        assert count == 1


def test_get_number_of_known_portals_multiple_portals(tmp_path):
    """Verify count is correct with multiple portals."""
    with _PortalTester():
        BasicPortal(root_dict=str(tmp_path / "p1"))
        BasicPortal(root_dict=str(tmp_path / "p2"))
        BasicPortal(root_dict=str(tmp_path / "p3"))
        count = count_known_portals()
        assert count == 3


def test_get_all_known_portals_returns_list(tmp_path):
    """Verify get_all_known_portals returns a list."""
    with _PortalTester():
        BasicPortal(root_dict=str(tmp_path / "p1"))
        result = get_known_portals()
        assert isinstance(result, set)


def test_get_all_known_portals_empty():
    """Verify empty list when no portals exist."""
    with _PortalTester():
        result = get_known_portals()
        assert len(result) == 0


def test_get_all_known_portals_content(tmp_path):
    """Verify get_all_known_portals returns correct portal instances."""
    with _PortalTester():
        p1 = BasicPortal(root_dict=str(tmp_path / "p1"))
        p2 = BasicPortal(root_dict=str(tmp_path / "p2"))
        result = get_known_portals()

        assert len(result) == 2
        assert p1 in result
        assert p2 in result
        assert all(isinstance(p, BasicPortal) for p in result)


def test_get_number_of_active_portals_no_active(tmp_path):
    """Verify count is zero when no portals are active."""
    with _PortalTester():
        # Create portal but don't activate it
        BasicPortal(root_dict=str(tmp_path / "p1"))
        count = count_active_portals()
        assert count == 0


def test_get_number_of_active_portals_single_active(tmp_path):
    """Verify count with one active portal."""
    with _PortalTester():
        portal = BasicPortal(root_dict=str(tmp_path / "p1"))
        with portal:
            count = count_active_portals()
            assert count == 1


def test_get_number_of_active_portals_nested_same_portal(tmp_path):
    """Verify count with same portal activated multiple times."""
    with _PortalTester():
        portal = BasicPortal(root_dict=str(tmp_path / "p1"))
        with portal:
            with portal:
                # Should still count as 1 unique portal
                count = count_active_portals()
                assert count == 1


def test_get_number_of_active_portals_multiple_unique(tmp_path):
    """Verify count with multiple unique active portals."""
    with _PortalTester():
        p1 = BasicPortal(root_dict=str(tmp_path / "p1"))
        p2 = BasicPortal(root_dict=str(tmp_path / "p2"))
        with p1:
            with p2:
                count = count_active_portals()
                assert count == 2


def test_get_depth_of_active_portal_stack_empty(tmp_path):
    """Verify depth is zero when no portals are active."""
    with _PortalTester():
        BasicPortal(root_dict=str(tmp_path / "p1"))
        depth = measure_active_portals_stack()
        assert depth == 0


def test_get_depth_of_active_portal_stack_single_activation(tmp_path):
    """Verify depth is 1 for single portal activation."""
    with _PortalTester():
        portal = BasicPortal(root_dict=str(tmp_path / "p1"))
        with portal:
            depth = measure_active_portals_stack()
            assert depth == 1


def test_get_depth_of_active_portal_stack_nested_same_portal(tmp_path):
    """Verify depth increases with nested activation of same portal."""
    with _PortalTester():
        portal = BasicPortal(root_dict=str(tmp_path / "p1"))
        with portal:
            depth1 = measure_active_portals_stack()
            with portal:
                depth2 = measure_active_portals_stack()
                assert depth1 == 1
                assert depth2 == 2


def test_get_depth_of_active_portal_stack_multiple_portals(tmp_path):
    """Verify depth with multiple different portals."""
    with _PortalTester():
        p1 = BasicPortal(root_dict=str(tmp_path / "p1"))
        p2 = BasicPortal(root_dict=str(tmp_path / "p2"))
        with p1:
            with p2:
                depth = measure_active_portals_stack()
                assert depth == 2


def test_get_nonactive_portals_all_active(tmp_path):
    """Verify empty list when all portals are active."""
    with _PortalTester():
        p1 = BasicPortal(root_dict=str(tmp_path / "p1"))
        with p1:
            result = get_nonactive_portals()
            assert len(result) == 0


def test_get_nonactive_portals_mixed(tmp_path):
    """Verify correct list when some portals are not active."""
    with _PortalTester():
        p1 = BasicPortal(root_dict=str(tmp_path / "p1"))
        p2 = BasicPortal(root_dict=str(tmp_path / "p2"))
        p3 = BasicPortal(root_dict=str(tmp_path / "p3"))

        with p1:
            result = get_nonactive_portals()
            assert len(result) == 2
            assert p1 not in result
            assert p2 in result
            assert p3 in result


def test_get_nonactive_portals_none_active(tmp_path):
    """Verify all portals returned when none are active."""
    with _PortalTester():
        p1 = BasicPortal(root_dict=str(tmp_path / "p1"))
        p2 = BasicPortal(root_dict=str(tmp_path / "p2"))

        result = get_nonactive_portals()
        assert len(result) == 2
        assert p1 in result
        assert p2 in result
