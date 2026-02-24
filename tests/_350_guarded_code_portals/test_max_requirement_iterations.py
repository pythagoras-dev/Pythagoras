"""Tests for MAX_REQUIREMENT_ITERATIONS limit in GuardedFn.execute()."""
from pythagoras._350_guarded_code_portals import *

def test_max_requirement_iterations_constant_exists():
    """Test that MAX_REQUIREMENT_ITERATIONS is exported and has expected value."""
    assert isinstance(MAX_REQUIREMENT_ITERATIONS, int)
    assert MAX_REQUIREMENT_ITERATIONS >= 1
    assert MAX_REQUIREMENT_ITERATIONS <= 1_000_000_000
