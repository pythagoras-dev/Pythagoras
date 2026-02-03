"""Tests for MAX_PRE_VALIDATION_ITERATIONS limit in ProtectedFn.execute()."""
from pythagoras._350_protected_code_portals import *

def test_max_pre_validation_iterations_constant_exists():
    """Test that MAX_PRE_VALIDATION_ITERATIONS is exported and has expected value."""
    assert isinstance(MAX_PRE_VALIDATION_ITERATIONS, int)
    assert MAX_PRE_VALIDATION_ITERATIONS >= 1
    assert MAX_PRE_VALIDATION_ITERATIONS <= 1_000_000_000
