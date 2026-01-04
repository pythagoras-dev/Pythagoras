"""Tests for unused_ram() validator factory in basic_pre_validators.py."""

import pytest
from pythagoras import unused_ram, SimplePreValidatorFn, ProtectedCodePortal
from pythagoras._210_basic_portals.portal_tester import _PortalTester


def test_unused_ram_returns_simple_pre_validator_fn(tmpdir):
    """Test that unused_ram() returns a SimplePreValidatorFn."""
    with _PortalTester(ProtectedCodePortal, root_dict=tmpdir):
        validator = unused_ram(1)
        assert isinstance(validator, SimplePreValidatorFn)


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


def test_unused_ram_validator_has_fixed_kwargs(tmpdir):
    """Test that the validator has the correct fixed_kwargs."""
    with _PortalTester(ProtectedCodePortal, root_dict=tmpdir):
        validator = unused_ram(2)
        assert validator._fixed_kwargs == {"x": 2}


def test_unused_ram_multiple_instances_independent(tmpdir):
    """Test that multiple validator instances have independent configurations."""
    with _PortalTester(ProtectedCodePortal, root_dict=tmpdir):
        validator_1 = unused_ram(1)
        validator_16 = unused_ram(16)

        assert validator_1._fixed_kwargs == {"x": 1}
        assert validator_16._fixed_kwargs == {"x": 16}
