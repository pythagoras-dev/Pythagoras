"""Tests for unused_ram() requirement factory in basic_requirements.py."""

import pytest
from pythagoras import unused_ram, SimpleRequirementFn, GuardedCodePortal
from pythagoras._210_basic_portals.portal_tester import _PortalTester


def test_unused_ram_returns_simple_requirement_fn(tmpdir):
    """Test that unused_ram() returns a SimpleRequirementFn."""
    with _PortalTester(GuardedCodePortal, root_dict=tmpdir):
        requirement = unused_ram(1)
        assert isinstance(requirement, SimpleRequirementFn)


def test_unused_ram_with_non_integer_raises_type_error():
    """Test that passing a non-integer raises TypeError."""
    with pytest.raises(TypeError, match="Gb must be an int"):
        unused_ram(1.5)

    with pytest.raises(TypeError, match="Gb must be an int"):
        unused_ram("1")

    with pytest.raises(TypeError, match="Gb must be an int"):
        unused_ram(None)


def test_unused_ram_with_zero_raises_value_error():
    """Test that Gb <= 0 raises ValueError."""
    with pytest.raises(ValueError, match="Gb must be > 0"):
        unused_ram(0)


def test_unused_ram_with_negative_raises_value_error():
    """Test that negative Gb raises ValueError."""
    with pytest.raises(ValueError, match="Gb must be > 0"):
        unused_ram(-1)

    with pytest.raises(ValueError, match="Gb must be > 0"):
        unused_ram(-10)


def test_unused_ram_requirement_has_fixed_kwargs(tmpdir):
    """Test that the requirement has the correct fixed_kwargs."""
    with _PortalTester(GuardedCodePortal, root_dict=tmpdir):
        requirement = unused_ram(2)
        assert requirement._fixed_kwargs == {"x": 2}


def test_unused_ram_multiple_instances_independent(tmpdir):
    """Test that multiple requirement instances have independent configurations."""
    with _PortalTester(GuardedCodePortal, root_dict=tmpdir):
        requirement_1 = unused_ram(1)
        requirement_16 = unused_ram(16)

        assert requirement_1._fixed_kwargs == {"x": 1}
        assert requirement_16._fixed_kwargs == {"x": 16}


def test_unused_ram_with_bool_raises_type_error():
    """Test that passing a boolean raises TypeError (bool is subclass of int)."""
    with pytest.raises(TypeError, match="Gb must be an int"):
        unused_ram(True)

    with pytest.raises(TypeError, match="Gb must be an int"):
        unused_ram(False)
