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
    """Return the value associated with *key* in a portal‐description DataFrame.

    The DataFrame must follow the schema produced by portal ``describe()``
    implementations: three columns ``["type", "name", "value"]``.

    Parameters
    ----------
    dataframe : pandas.DataFrame
        Portal description table.
    key : str
        Characteristic name to retrieve.

    Returns
    -------
    Any
        The value stored in the ``"value"`` column for the matching row.

    Raises
    ------
    KeyError
        If *key* is not present in the ``"name"`` column.
    """
    mask = dataframe.iloc[:, 1] == key
    if not mask.any():
        raise KeyError(f"Key '{key}' not found in portal description.")
    return dataframe.loc[mask].iloc[0, 2]
