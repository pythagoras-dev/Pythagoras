"""Tests for PortalTracker class."""
import pytest
from pythagoras._210_basic_portals import PortalTracker
from pythagoras._210_basic_portals import BasicPortal, _PortalTester


def test_empty_initialization():
    """Test creating an empty PortalTracker."""
    tracker = PortalTracker()

    assert len(tracker) == 0
    assert not tracker
    assert list(tracker) == []


@pytest.mark.parametrize("portal_count", [1, 2, 5])
def test_initialization_with_portals(tmp_path, portal_count):
    """Test initialization with portal instances."""
    with _PortalTester():
        portals = [BasicPortal(tmp_path / f"p{i}") for i in range(portal_count)]
        tracker = PortalTracker(portals)

        assert len(tracker) == portal_count
        assert tracker
        for portal in portals:
            assert portal in tracker


def test_add_portal_instance(tmp_path):
    """Test adding a portal instance."""
    with _PortalTester():
        portal = BasicPortal(tmp_path)
        tracker = PortalTracker()

        tracker.add(portal)

        assert len(tracker) == 1
        assert portal in tracker


def test_add_duplicate_is_idempotent(tmp_path):
    """Test that adding the same portal multiple times has no extra effect."""
    with _PortalTester():
        portal = BasicPortal(tmp_path)
        tracker = PortalTracker()

        tracker.add(portal)
        tracker.add(portal)
        tracker.add(portal)

        assert len(tracker) == 1
        assert portal in tracker


def test_add_invalid_type_raises_typeerror():
    """Test that adding invalid types raises TypeError."""
    tracker = PortalTracker()

    with pytest.raises(TypeError, match="Expected BasicPortal"):
        tracker.add(123)

    with pytest.raises(TypeError, match="Expected BasicPortal"):
        tracker.add(None)

    with pytest.raises(TypeError, match="Expected BasicPortal"):
        tracker.add([])

    with pytest.raises(TypeError, match="Expected BasicPortal"):
        tracker.add("some_string")


def test_update_with_multiple_portals(tmp_path):
    """Test updating tracker with multiple portals at once."""
    with _PortalTester():
        portals = [BasicPortal(tmp_path / f"p{i}") for i in range(4)]
        tracker = PortalTracker()

        tracker.update(portals[:2])
        assert len(tracker) == 2

        tracker.update(portals[2:])
        assert len(tracker) == 4

        for portal in portals:
            assert portal in tracker


def test_discard_existing_portal(tmp_path):
    """Test discarding an existing portal."""
    with _PortalTester():
        portal = BasicPortal(tmp_path)
        tracker = PortalTracker([portal])

        tracker.discard(portal)

        assert len(tracker) == 0
        assert portal not in tracker


def test_discard_non_existing_no_error(tmp_path):
    """Test that discarding non-existing portal raises no error."""
    with _PortalTester():
        p1 = BasicPortal(tmp_path / "p1")
        p2 = BasicPortal(tmp_path / "p2")
        tracker = PortalTracker([p1])

        # Should not raise
        tracker.discard(p2)

        assert len(tracker) == 1
        assert p1 in tracker


def test_contains_with_portal_instance(tmp_path):
    """Test __contains__ with portal instances."""
    with _PortalTester():
        p1 = BasicPortal(tmp_path / "p1")
        p2 = BasicPortal(tmp_path / "p2")
        tracker = PortalTracker([p1])

        assert p1 in tracker
        assert p2 not in tracker


def test_subtraction_operator(tmp_path):
    """Test set difference using subtraction operator."""
    with _PortalTester():
        p1 = BasicPortal(tmp_path / "p1")
        p2 = BasicPortal(tmp_path / "p2")
        p3 = BasicPortal(tmp_path / "p3")

        tracker1 = PortalTracker([p1, p2, p3])
        tracker2 = PortalTracker([p2])

        result = tracker1 - tracker2

        assert len(result) == 2
        assert p1 in result
        assert p3 in result
        assert p2 not in result
        # Original trackers unchanged
        assert len(tracker1) == 3
        assert len(tracker2) == 1


def test_equality_same_portals(tmp_path):
    """Test equality when trackers contain same portals."""
    with _PortalTester():
        p1 = BasicPortal(tmp_path / "p1")
        p2 = BasicPortal(tmp_path / "p2")

        tracker1 = PortalTracker([p1, p2])
        tracker2 = PortalTracker([p2, p1])  # Different order

        assert tracker1 == tracker2


def test_equality_different_portals(tmp_path):
    """Test inequality when trackers contain different portals."""
    with _PortalTester():
        p1 = BasicPortal(tmp_path / "p1")
        p2 = BasicPortal(tmp_path / "p2")
        p3 = BasicPortal(tmp_path / "p3")

        tracker1 = PortalTracker([p1, p2])
        tracker2 = PortalTracker([p1, p3])

        assert tracker1 != tracker2


def test_equality_with_non_tracker():
    """Test that equality with non-PortalTracker returns NotImplemented."""
    tracker = PortalTracker()

    assert tracker.__eq__({}) == NotImplemented
    assert tracker.__eq__([]) == NotImplemented
    assert tracker.__eq__(None) == NotImplemented


def test_subtraction_with_invalid_type():
    """Test that subtraction with non-PortalTracker returns NotImplemented."""
    tracker = PortalTracker()

    assert tracker.__sub__({}) == NotImplemented
    assert tracker.__rsub__({}) == NotImplemented


def test_iteration_over_portals(tmp_path):
    """Test iterating over tracker yields portal instances."""
    with _PortalTester():
        portals = [BasicPortal(tmp_path / f"p{i}") for i in range(3)]
        tracker = PortalTracker(portals)

        result = list(tracker)

        assert len(result) == 3
        # Check all portals are present (order may vary)
        assert set(result) == set(portals)
        for portal in result:
            assert isinstance(portal, BasicPortal)


def test_len_returns_correct_count(tmp_path):
    """Test that __len__ returns correct portal count."""
    with _PortalTester():
        portals = [BasicPortal(tmp_path / f"p{i}") for i in range(5)]
        tracker = PortalTracker()

        assert len(tracker) == 0

        for i, portal in enumerate(portals, 1):
            tracker.add(portal)
            assert len(tracker) == i


def test_bool_empty_and_non_empty():
    """Test __bool__ for empty and non-empty trackers."""
    with _PortalTester(BasicPortal) as tester:
        tracker = PortalTracker()

        assert not tracker

        tracker.add(tester.portal)
        assert tracker

        tracker.discard(tester.portal)
        assert not tracker


def test_not_picklable():
    """Test that PortalTracker cannot be pickled."""
    tracker = PortalTracker()

    with pytest.raises(TypeError, match="cannot be pickled"):
        tracker.__getstate__()

    with pytest.raises(TypeError, match="cannot be unpickled"):
        tracker.__setstate__({})


def test_repr(tmp_path):
    """Test that __repr__ includes portal info."""
    with _PortalTester():
        portals = [BasicPortal(tmp_path / f"p{i}") for i in range(2)]
        tracker = PortalTracker(portals)

        repr_str = repr(tracker)

        assert "PortalTracker" in repr_str


def test_repr_empty_tracker():
    """Test __repr__ for empty tracker."""
    tracker = PortalTracker()

    repr_str = repr(tracker)

    assert "PortalTracker" in repr_str
    assert "∅" in repr_str
