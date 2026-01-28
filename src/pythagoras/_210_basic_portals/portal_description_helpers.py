"""Helpers for building and querying portal descriptions.

This module provides small utilities used by portal `describe()` methods
to construct a standardized, single-row pandas DataFrame for individual
characteristics and to retrieve values from such DataFrames.

DataFrame schema contract used throughout the project:
- columns: `type`, `name`, `value` (in this exact order)
- `type` indicates the source of the characteristic:
  - "Disk" for persistent, disk-backed properties
  - "Runtime" for properties computed at runtime

These helpers do not mutate portal state; they only format/lookup data.
"""
from __future__ import annotations

from typing import Any

import pandas as pd


def _describe_persistent_characteristic(name: str, value: Any) -> pd.DataFrame:
    """Create a one-row DataFrame for a persistent (disk-backed) property.

    Args:
        name: Characteristic name.
        value: Characteristic value (any pandas-compatible type).

    Returns:
        DataFrame with columns `type`, `name`, `value` where `type` is "Disk".
    """
    d = dict(
        type="Disk",
        name=[name],
        value=[value],
    )
    return pd.DataFrame(d)


def _describe_runtime_characteristic(name: str, value: Any) -> pd.DataFrame:
    """Create a one-row DataFrame for a runtime-computed property.

    Args:
        name: Characteristic name.
        value: Characteristic value (any pandas-compatible type).

    Returns:
        DataFrame with columns `type`, `name`, `value` where `type` is
        "Runtime".
    """
    d = dict(
        type="Runtime",
        name=[name],
        value=[value],
    )
    return pd.DataFrame(d)


def _get_description_value_by_key(dataframe: pd.DataFrame, key: str) -> Any:
    """Return the value associated with a key in a portal description DataFrame.

    Args:
        dataframe: Portal description DataFrame with columns ["type", "name", "value"].
        key: Characteristic name to retrieve.

    Returns:
        The value from the "value" column for the matching row.

    Raises:
        KeyError: If key is not found in the "name" column.
    """
    mask = dataframe["name"] == key
    if not mask.any():
        raise KeyError(f"Key '{key}' not found in portal description.")
    return dataframe.loc[mask].iloc[0, 2]
