"""Tests for strict portal type checking in accessor functions."""
import pytest
from pythagoras import (
    BasicPortal,
    _PortalTester,
    get_known_portals,
    count_known_portals,
    count_active_portals,
    measure_active_portals_stack,
    get_nonactive_portals,
    get_noncurrent_portals
)


class PortalA(BasicPortal):
    """Test portal subclass A."""
    pass


class PortalB(BasicPortal):
    """Test portal subclass B."""
    pass


def test_strict_type_checking(tmpdir):
    """Verify accessor functions enforce strict portal type matching."""
    with _PortalTester():
        pA = PortalA(tmpdir + "/a")
        _pB = PortalB(tmpdir + "/b")

        with pytest.raises(TypeError):
            get_known_portals(required_portal_type=PortalA)

        with pytest.raises(TypeError):
            count_known_portals(required_portal_type=PortalA)

        with pytest.raises(TypeError):
            get_nonactive_portals(required_portal_type=PortalA)

        with pytest.raises(TypeError):
            get_noncurrent_portals(required_portal_type=PortalA)

        with pA:
            with pytest.raises(TypeError):
                count_active_portals(required_portal_type=PortalB)

            with pytest.raises(TypeError):
                measure_active_portals_stack(required_portal_type=PortalB)

            assert count_active_portals(required_portal_type=PortalA) == 1
            assert measure_active_portals_stack(required_portal_type=PortalA) == 1
