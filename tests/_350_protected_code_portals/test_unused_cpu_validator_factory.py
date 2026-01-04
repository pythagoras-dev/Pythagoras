"""Tests for unused_cpu() validator factory in basic_pre_validators.py."""

import pytest
from pythagoras import unused_cpu, SimplePreValidatorFn, ProtectedCodePortal
from pythagoras._210_basic_portals.portal_tester import _PortalTester


def test_unused_cpu_returns_simple_pre_validator_fn(tmpdir):
    """Test that unused_cpu() returns a SimplePreValidatorFn."""
    with _PortalTester(ProtectedCodePortal, root_dict=tmpdir):
        validator = unused_cpu(2)
        assert isinstance(validator, SimplePreValidatorFn)


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


def test_unused_cpu_validator_has_fixed_kwargs(tmpdir):
    """Test that the validator has the correct fixed_kwargs."""
    with _PortalTester(ProtectedCodePortal, root_dict=tmpdir):
        validator = unused_cpu(4)
        assert validator._fixed_kwargs == {"n": 4}


def test_unused_cpu_multiple_instances_independent(tmpdir):
    """Test that multiple validator instances have independent configurations."""
    with _PortalTester(ProtectedCodePortal, root_dict=tmpdir):
        validator_2 = unused_cpu(2)
        validator_8 = unused_cpu(8)

        assert validator_2._fixed_kwargs == {"n": 2}
        assert validator_8._fixed_kwargs == {"n": 8}
