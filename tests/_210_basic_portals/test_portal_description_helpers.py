"""Tests for portal description helper functions."""

import pandas as pd
import pytest

from pythagoras._210_basic_portals.portal_description_helpers import (
    _describe_persistent_characteristic,
    _describe_runtime_characteristic,
    _get_description_value_by_key,
)


def test_describe_persistent_characteristic_returns_dataframe():
    """Verify _describe_persistent_characteristic returns a DataFrame."""
    result = _describe_persistent_characteristic("test_name", "test_value")
    assert isinstance(result, pd.DataFrame)


def test_describe_persistent_characteristic_schema():
    """Verify the returned DataFrame has correct schema."""
    result = _describe_persistent_characteristic("test_name", "test_value")

    # Should have exactly 3 columns in correct order
    assert list(result.columns) == ["type", "name", "value"]

    # Should have exactly 1 row
    assert len(result) == 1


def test_describe_persistent_characteristic_content():
    """Verify the returned DataFrame contains correct data."""
    result = _describe_persistent_characteristic("my_name", "my_value")

    assert result.iloc[0]["type"] == "Disk"
    assert result.iloc[0]["name"] == "my_name"
    assert result.iloc[0]["value"] == "my_value"


def test_describe_persistent_characteristic_various_value_types():
    """Verify function works with different value types."""
    # String value
    result_str = _describe_persistent_characteristic("key", "string_val")
    assert result_str.iloc[0]["value"] == "string_val"

    # Integer value
    result_int = _describe_persistent_characteristic("key", 42)
    assert result_int.iloc[0]["value"] == 42

    # Path-like object
    from pathlib import Path
    path_val = Path("/test/path")
    result_path = _describe_persistent_characteristic("key", path_val)
    assert result_path.iloc[0]["value"] == path_val


def test_describe_runtime_characteristic_returns_dataframe():
    """Verify _describe_runtime_characteristic returns a DataFrame."""
    result = _describe_runtime_characteristic("test_name", "test_value")
    assert isinstance(result, pd.DataFrame)


def test_describe_runtime_characteristic_schema():
    """Verify the returned DataFrame has correct schema."""
    result = _describe_runtime_characteristic("test_name", "test_value")

    # Should have exactly 3 columns in correct order
    assert list(result.columns) == ["type", "name", "value"]

    # Should have exactly 1 row
    assert len(result) == 1


def test_describe_runtime_characteristic_content():
    """Verify the returned DataFrame contains correct data with Runtime type."""
    result = _describe_runtime_characteristic("my_name", "my_value")

    assert result.iloc[0]["type"] == "Runtime"
    assert result.iloc[0]["name"] == "my_name"
    assert result.iloc[0]["value"] == "my_value"


def test_describe_persistent_vs_runtime_type_difference():
    """Verify persistent and runtime helpers differ only in the type field."""
    persistent = _describe_persistent_characteristic("name", "value")
    runtime = _describe_runtime_characteristic("name", "value")

    assert persistent.iloc[0]["type"] == "Disk"
    assert runtime.iloc[0]["type"] == "Runtime"
    assert persistent.iloc[0]["name"] == runtime.iloc[0]["name"]
    assert persistent.iloc[0]["value"] == runtime.iloc[0]["value"]


def test_get_description_value_by_key_retrieves_value():
    """Verify _get_description_value_by_key returns the correct value."""
    df = pd.DataFrame({
        "type": ["Disk", "Runtime"],
        "name": ["key1", "key2"],
        "value": ["value1", "value2"]
    })

    assert _get_description_value_by_key(df, "key1") == "value1"
    assert _get_description_value_by_key(df, "key2") == "value2"


def test_get_description_value_by_key_raises_on_missing_key():
    """Verify _get_description_value_by_key raises KeyError for missing keys."""
    df = pd.DataFrame({
        "type": ["Disk"],
        "name": ["existing_key"],
        "value": ["some_value"]
    })

    with pytest.raises(KeyError):
        _get_description_value_by_key(df, "nonexistent_key")


def test_get_description_value_by_key_with_empty_dataframe():
    """Verify _get_description_value_by_key raises KeyError on empty DataFrame."""
    df = pd.DataFrame({
        "type": [],
        "name": [],
        "value": []
    })

    with pytest.raises(KeyError):
        _get_description_value_by_key(df, "any_key")


def test_get_description_value_by_key_returns_first_match():
    """Verify function returns first match when duplicate keys exist."""
    df = pd.DataFrame({
        "type": ["Disk", "Runtime"],
        "name": ["duplicate", "duplicate"],
        "value": ["first_value", "second_value"]
    })

    # Should return the first occurrence
    result = _get_description_value_by_key(df, "duplicate")
    assert result == "first_value"
