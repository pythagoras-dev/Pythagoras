"""Tests for portal type validation in accessor functions."""
import pytest
from pythagoras import (
    BasicPortal,
    _PortalTester,
    count_known_portals,
    get_known_portals,
    count_active_portals,
    measure_active_portals_stack,
    get_nonactive_portals,
    get_noncurrent_portals
)


class NotAPortal:
    """Non-portal class for testing type validation."""
    pass


def test_validation_errors(tmpdir):
    """Verify accessor functions raise TypeError for invalid portal types."""
    with _PortalTester():
        # Prepare some invalid inputs
        # We need a portal instance for one of the checks
        portal_instance = BasicPortal(tmpdir)
        
        invalid_inputs = [
            int,
            str,
            object,
            NotAPortal,
            123,
            "some string",
            portal_instance # An instance, not a class
        ]

        functions_to_test = [
            count_known_portals,
            get_known_portals,
            count_active_portals,
            measure_active_portals_stack,
            get_nonactive_portals,
            get_noncurrent_portals
        ]
        
        for func in functions_to_test:
            for invalid_input in invalid_inputs:
                with pytest.raises(TypeError):
                    func(required_portal_type=invalid_input)
