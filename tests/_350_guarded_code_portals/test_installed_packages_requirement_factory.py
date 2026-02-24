"""Tests for installed_packages() requirement factory in basic_requirements.py."""

import pytest
from pythagoras import installed_packages, SimpleRequirementFn, GuardedCodePortal
from pythagoras._210_basic_portals.portal_tester import _PortalTester


def test_installed_packages_returns_list_of_requirements(tmpdir):
    """Test that installed_packages() returns a list of SimpleRequirementFn."""
    with _PortalTester(GuardedCodePortal, root_dict=tmpdir):
        requirements = installed_packages("os", "sys")
        assert isinstance(requirements, list)
        assert len(requirements) == 2
        assert all(isinstance(v, SimpleRequirementFn) for v in requirements)


def test_installed_packages_single_package(tmpdir):
    """Test that installed_packages() works with a single package."""
    with _PortalTester(GuardedCodePortal, root_dict=tmpdir):
        requirements = installed_packages("os")
        assert isinstance(requirements, list)
        assert len(requirements) == 1
        assert isinstance(requirements[0], SimpleRequirementFn)


def test_installed_packages_with_non_string_raises_type_error(tmpdir):
    """Test that passing a non-string raises TypeError."""
    with _PortalTester(GuardedCodePortal, root_dict=tmpdir):
        with pytest.raises(TypeError, match="All package names must be strings"):
            installed_packages("os", 123)

        with pytest.raises(TypeError, match="All package names must be strings"):
            installed_packages(None)

        with pytest.raises(TypeError, match="All package names must be strings"):
            installed_packages("pytest", ["numpy"])


def test_installed_packages_requirements_have_correct_fixed_kwargs(tmpdir):
    """Test that each requirement has the correct package_name in fixed_kwargs."""
    with _PortalTester(GuardedCodePortal, root_dict=tmpdir):
        requirements = installed_packages("pytest", "numpy", "pandas")

        assert requirements[0]._fixed_kwargs == {"package_name": "pytest"}
        assert requirements[1]._fixed_kwargs == {"package_name": "numpy"}
        assert requirements[2]._fixed_kwargs == {"package_name": "pandas"}


def test_installed_packages_empty_args(tmpdir):
    """Test that calling without arguments returns an empty list."""
    with _PortalTester(GuardedCodePortal, root_dict=tmpdir):
        requirements = installed_packages()
        assert requirements == []


def test_installed_packages_mixed_types_raises_on_first_invalid(tmpdir):
    """Test that the first non-string argument raises TypeError."""
    with _PortalTester(GuardedCodePortal, root_dict=tmpdir):
        with pytest.raises(TypeError, match="All package names must be strings"):
            installed_packages("os", "sys", 42, "pytest")
