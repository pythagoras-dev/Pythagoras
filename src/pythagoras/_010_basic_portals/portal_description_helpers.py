from __future__ import annotations

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

from typing import Any

import pandas as pd


def _describe_persistent_characteristic(name, value) -> pd.DataFrame:
    """Create a one-row DataFrame for a persistent (disk-backed) property.

    Args:
        name: The characteristic name (e.g., base directory path label).
        value: The characteristic value. Can be any object that pandas can
            store in a single cell (typically str, int, Path, etc.).

    Returns:
        A pandas DataFrame with columns `type`, `name`, `value` and a single
        row where `type` is "Disk".
    """
    d = dict(
        type="Disk",
        name=[name],
        value=[value],
    )
    return pd.DataFrame(d)


def _describe_runtime_characteristic(name, value) -> pd.DataFrame:
    """Create a one-row DataFrame for a runtime-computed property.

    Args:
        name: The characteristic name (e.g., backend type, version).
        value: The characteristic value. Can be any object that pandas can
            store in a single cell.

    Returns:
        A pandas DataFrame with columns `type`, `name`, `value` and a single
        row where `type` is "Runtime".
    """
    d = dict(
        type="Runtime",
        name=[name],
        value=[value],
    )
    return pd.DataFrame(d)


def _get_description_value_by_key(dataframe: pd.DataFrame, key: str) -> Any:
    """Return the value for a characteristic identified by its name.

    This function expects a DataFrame produced by portal `describe()` logic
    that follows the standard schema: columns `type`, `name`, `value`.

    Args:
        dataframe: A pandas DataFrame with exactly three columns in the
            order `type`, `name`, `value`.
        key: The characteristic name to look up in the `name` column.

    Returns:
        The corresponding entry from the `value` column if a row with
        `name == key` exists; otherwise, None.
    """
    # Filter rows where the second column (`name`) equals the key
    result = dataframe.loc[dataframe.iloc[:, 1] == key]
    if not result.empty:
        # Return the third column (`value`) of the first matched row
        return result.iloc[0, 2]
    return None
