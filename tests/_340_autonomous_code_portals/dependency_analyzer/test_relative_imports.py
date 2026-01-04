"""Tests for relative import detection and handling in autonomous functions."""
import pytest
from pythagoras._340_autonomous_code_portals.names_usage_analyzer import _analyze_names_in_function
from pythagoras._340_autonomous_code_portals import AutonomousFn
from pythagoras._310_ordinary_code_portals import FunctionError


# Test functions for the analyzer (without trying to make them autonomous)

def func_with_relative_import_current():
    """Function with relative import from current package."""
    from . import utils
    return utils.helper()


def func_with_relative_import_parent():
    """Function with relative import from parent package."""
    from .. import config
    return config.get_value()


def func_with_relative_import_submodule():
    """Function with relative import from submodule."""
    from .submodule import helper
    return helper()


def func_with_relative_import_parent_submodule():
    """Function with relative import from parent's submodule."""
    from ..sibling import data
    return data


def func_with_absolute_import():
    """Function with absolute import (should work fine)."""
    from math import sqrt
    return sqrt(4)


def func_with_mixed_imports():
    """Function with both absolute and relative imports."""
    from math import sqrt  # absolute
    from . import utils    # relative
    return sqrt(utils.value)


# Analyzer tests - verify detection without autonomy enforcement

def test_analyzer_detects_relative_import_current():
    """Verify analyzer detects 'from . import x'."""
    analyzer = _analyze_names_in_function(func_with_relative_import_current)["analyzer"]
    assert analyzer.names.has_relative_imports is True
    assert "utils" in analyzer.names.imported


def test_analyzer_detects_relative_import_parent():
    """Verify analyzer detects 'from .. import x'."""
    analyzer = _analyze_names_in_function(func_with_relative_import_parent)["analyzer"]
    assert analyzer.names.has_relative_imports is True
    assert "config" in analyzer.names.imported


def test_analyzer_detects_relative_import_submodule():
    """Verify analyzer detects 'from .submodule import x'."""
    analyzer = _analyze_names_in_function(func_with_relative_import_submodule)["analyzer"]
    assert analyzer.names.has_relative_imports is True
    assert "helper" in analyzer.names.imported
    # Should track "submodule" as the top-level package
    assert "submodule" in analyzer.imported_packages_deep


def test_analyzer_detects_relative_import_parent_submodule():
    """Verify analyzer detects 'from ..sibling import x'."""
    analyzer = _analyze_names_in_function(func_with_relative_import_parent_submodule)["analyzer"]
    assert analyzer.names.has_relative_imports is True
    assert "data" in analyzer.names.imported
    assert "sibling" in analyzer.imported_packages_deep


def test_analyzer_absolute_import_no_flag():
    """Verify analyzer does NOT flag absolute imports."""
    analyzer = _analyze_names_in_function(func_with_absolute_import)["analyzer"]
    assert analyzer.names.has_relative_imports is False
    assert "sqrt" in analyzer.names.imported
    assert "math" in analyzer.imported_packages_deep


def test_analyzer_mixed_imports():
    """Verify analyzer detects relative imports even when mixed with absolute."""
    analyzer = _analyze_names_in_function(func_with_mixed_imports)["analyzer"]
    assert analyzer.names.has_relative_imports is True
    assert "sqrt" in analyzer.names.imported
    assert "utils" in analyzer.names.imported
    assert "math" in analyzer.imported_packages_deep


# Autonomy enforcement tests - verify AutonomousFn rejects relative imports

def test_autonomous_rejects_relative_import_current():
    """AutonomousFn should reject 'from . import x'."""
    with pytest.raises(FunctionError) as exc_info:
        AutonomousFn(func_with_relative_import_current)

    error_msg = str(exc_info.value)
    assert "relative imports" in error_msg.lower()
    assert "not autonomous" in error_msg.lower()
    # Check that helpful guidance is provided
    assert "absolute imports" in error_msg.lower()


def test_autonomous_rejects_relative_import_parent():
    """AutonomousFn should reject 'from .. import x'."""
    with pytest.raises(FunctionError) as exc_info:
        AutonomousFn(func_with_relative_import_parent)

    error_msg = str(exc_info.value)
    assert "relative imports" in error_msg.lower()
    assert "not autonomous" in error_msg.lower()


def test_autonomous_rejects_relative_import_submodule():
    """AutonomousFn should reject 'from .submodule import x'."""
    with pytest.raises(FunctionError) as exc_info:
        AutonomousFn(func_with_relative_import_submodule)

    error_msg = str(exc_info.value)
    assert "relative imports" in error_msg.lower()


def test_autonomous_rejects_mixed_imports():
    """AutonomousFn should reject functions with any relative imports."""
    with pytest.raises(FunctionError) as exc_info:
        AutonomousFn(func_with_mixed_imports)

    error_msg = str(exc_info.value)
    assert "relative imports" in error_msg.lower()


def test_autonomous_accepts_absolute_import():
    """AutonomousFn should accept functions with only absolute imports."""
    # This should NOT raise an error
    fn = AutonomousFn(func_with_absolute_import)
    assert fn.name == "func_with_absolute_import"
    # Just verify it was created successfully; execution requires portal setup
    # which is beyond the scope of this import validation test


# Edge case: package name extraction consistency

def func_with_nested_package_import():
    """Function importing from nested package."""
    from os.path import join
    return join("a", "b")


def test_package_name_extraction_consistency():
    """Verify consistent package name extraction between Import and ImportFrom.

    Both should extract the top-level package name (not the last component).
    """
    # Test ImportFrom
    analyzer1 = _analyze_names_in_function(func_with_nested_package_import)["analyzer"]
    assert "os" in analyzer1.imported_packages_deep  # Should be "os", not "path"
    assert "path" not in analyzer1.imported_packages_deep

    # Compare with equivalent Import
    def func_with_import():
        import os.path
        return os.path.join("a", "b")

    analyzer2 = _analyze_names_in_function(func_with_import)["analyzer"]
    assert "os" in analyzer2.imported_packages_deep

    # Both should track the same top-level package
    assert analyzer1.imported_packages_deep == analyzer2.imported_packages_deep


# No crash test: ensure the original bug is fixed

def test_no_crash_on_relative_imports():
    """Verify that analyzing relative imports doesn't crash (the original bug).

    Before the fix, this would raise AttributeError: 'NoneType' object has no attribute 'split'
    """
    # This should complete without crashing
    try:
        analyzer = _analyze_names_in_function(func_with_relative_import_current)["analyzer"]
        # If we get here, the crash is fixed
        assert analyzer.names.has_relative_imports is True
    except AttributeError as e:
        if "'NoneType' object has no attribute 'split'" in str(e):
            pytest.fail("Original crash bug still exists: attempting to call .split() on None")
        else:
            raise
