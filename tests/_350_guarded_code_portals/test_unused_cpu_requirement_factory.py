"""Tests for unused_cpu() requirement factory in basic_requirements.py."""

import pytest
from pythagoras import unused_cpu, SimpleRequirementFn, GuardedCodePortal
from pythagoras._210_basic_portals.portal_tester import _PortalTester


def test_unused_cpu_returns_simple_requirement_fn(tmpdir):
    """Test that unused_cpu() returns a SimpleRequirementFn."""
    with _PortalTester(GuardedCodePortal, root_dict=tmpdir):
        requirement = unused_cpu(2)
        assert isinstance(requirement, SimpleRequirementFn)


def test_unused_cpu_with_non_integer_raises_type_error():
    """Test that passing a non-integer raises TypeError."""
    with pytest.raises(TypeError, match="cores must be an int"):
        unused_cpu(2.5)

    with pytest.raises(TypeError, match="cores must be an int"):
        unused_cpu("2")

    with pytest.raises(TypeError, match="cores must be an int"):
        unused_cpu(None)


def test_unused_cpu_with_zero_raises_value_error():
    """Test that cores <= 0 raises ValueError."""
    with pytest.raises(ValueError, match="cores must be > 0"):
        unused_cpu(0)


def test_unused_cpu_with_negative_raises_value_error():
    """Test that negative cores raises ValueError."""
    with pytest.raises(ValueError, match="cores must be > 0"):
        unused_cpu(-1)

    with pytest.raises(ValueError, match="cores must be > 0"):
        unused_cpu(-10)


def test_unused_cpu_requirement_has_fixed_kwargs(tmpdir):
    """Test that the requirement has the correct fixed_kwargs."""
    with _PortalTester(GuardedCodePortal, root_dict=tmpdir):
        requirement = unused_cpu(4)
        assert requirement._fixed_kwargs == {"n": 4}


def test_unused_cpu_multiple_instances_independent(tmpdir):
    """Test that multiple requirement instances have independent configurations."""
    with _PortalTester(GuardedCodePortal, root_dict=tmpdir):
        requirement_2 = unused_cpu(2)
        requirement_8 = unused_cpu(8)

        assert requirement_2._fixed_kwargs == {"n": 2}
        assert requirement_8._fixed_kwargs == {"n": 8}


def test_unused_cpu_with_bool_raises_type_error():
    """Test that passing a boolean raises TypeError (bool is subclass of int)."""
    with pytest.raises(TypeError):
        unused_cpu(True)

    with pytest.raises(TypeError):
        unused_cpu(False)
