"""Tests for get_noncurrent_portals function."""
from pythagoras import _PortalTester, BasicPortal, get_noncurrent_portals


class HelperPortal(BasicPortal):
    """BasicPortal subclass for testing."""

    def __init__(self, path="default"):
        super().__init__(root_dict=path)


def test_get_noncurrent_portals_logic(tmp_path):
    """Verify get_noncurrent_portals returns all non-current portals, even if active."""
    with _PortalTester():
        assert len(get_noncurrent_portals()) == 0

        p1 = HelperPortal(str(tmp_path / "p1"))
        assert get_noncurrent_portals() == {p1}

        with p1:
            assert len(get_noncurrent_portals()) == 0

        p2 = HelperPortal(str(tmp_path / "p2"))

        result = get_noncurrent_portals()
        assert len(result) == 2
        assert p1 in result
        assert p2 in result

        with p1:
            assert get_noncurrent_portals() == {p2}

            with p2:
                assert get_noncurrent_portals() == {p1}
