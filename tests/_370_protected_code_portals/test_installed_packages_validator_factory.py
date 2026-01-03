"""Tests for installed_packages() validator factory in basic_pre_validators.py."""

import pytest
from pythagoras import installed_packages, SimplePreValidatorFn, ProtectedCodePortal
from pythagoras._210_basic_portals.portal_tester import _PortalTester


def test_installed_packages_returns_list_of_validators(tmpdir):
    """Test that installed_packages() returns a list of SimplePreValidatorFn."""
    with _PortalTester(ProtectedCodePortal, root_dict=tmpdir):
        validators = installed_packages("os", "sys")
        assert isinstance(validators, list)
        assert len(validators) == 2
        assert all(isinstance(v, SimplePreValidatorFn) for v in validators)


def test_installed_packages_single_package(tmpdir):
    """Test that installed_packages() works with a single package."""
    with _PortalTester(ProtectedCodePortal, root_dict=tmpdir):
        validators = installed_packages("os")
        assert isinstance(validators, list)
        assert len(validators) == 1
        assert isinstance(validators[0], SimplePreValidatorFn)


def test_installed_packages_with_non_string_raises_type_error(tmpdir):
    """Test that passing a non-string raises TypeError."""
    with _PortalTester(ProtectedCodePortal, root_dict=tmpdir):
        with pytest.raises(TypeError, match="All package names must be strings"):
            installed_packages("os", 123)

        with pytest.raises(TypeError, match="All package names must be strings"):
            installed_packages(None)

        with pytest.raises(TypeError, match="All package names must be strings"):
            installed_packages("pytest", ["numpy"])


def test_installed_packages_validators_have_correct_fixed_kwargs(tmpdir):
    """Test that each validator has the correct package_name in fixed_kwargs."""
    with _PortalTester(ProtectedCodePortal, root_dict=tmpdir):
        validators = installed_packages("pytest", "numpy", "pandas")

        assert validators[0]._fixed_kwargs == {"package_name": "pytest"}
        assert validators[1]._fixed_kwargs == {"package_name": "numpy"}
        assert validators[2]._fixed_kwargs == {"package_name": "pandas"}


def test_installed_packages_empty_args(tmpdir):
    """Test that calling without arguments returns an empty list."""
    with _PortalTester(ProtectedCodePortal, root_dict=tmpdir):
        validators = installed_packages()
        assert validators == []


def test_installed_packages_mixed_types_raises_on_first_invalid(tmpdir):
    """Test that the first non-string argument raises TypeError."""
    with _PortalTester(ProtectedCodePortal, root_dict=tmpdir):
        with pytest.raises(TypeError, match="All package names must be strings"):
            installed_packages("os", "sys", 42, "pytest")
