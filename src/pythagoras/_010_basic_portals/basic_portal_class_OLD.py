from __future__ import annotations

import random
from pathlib import Path
from typing import TypeVar, Type, Any
import pandas as pd
from parameterizable import ParameterizableClass

from persidict import PersiDict, FileDirDict
from .exceptions import NotPicklableObject

def _describe_persistent_characteristic(name, value) -> pd.DataFrame:
    """Create a DataFrame describing a persistent characteristic.

    A helper function used by the describe() method of BasicPortal
    and its subclasses. It creates a DataFrame with a single row
    containing the type, name, and value of the characteristic.
    """
    d = dict(
        type="Disk"
        ,name = [name]
        ,value = [value])
    return pd.DataFrame(d)


def _describe_runtime_characteristic(name, value) -> pd.DataFrame:
    """Create a DataFrame describing a runtime characteristic.

    A helper function used by the describe() method of BasicPortal
    and its subclasses. It creates a DataFrame with a single row
    containing the type, name, and value of the characteristic.
    """
    d = dict(
        type = "Runtime"
        ,name = [name]
        ,value = [value])
    return pd.DataFrame(d)

BASE_DIRECTORY_TXT = "Base directory"
BACKEND_TYPE_TXT = "Backend type"

def get_description_value_by_key(dataframe:pd.DataFrame, key:str) -> Any:
    """
    Retrieves the value corresponding to a given key from a DataFrame.

    Parameters:
    - dataframe (pd.DataFrame): The input DataFrame with at least 4 columns.
    - key (str): The key to search for in the third column of the DataFrame.

    Returns:
    - value (any): The value from the fourth column corresponding to the key.
                   Returns None if the key is not found.
    """
    # Check if the key exists in the 3rd column
    result = dataframe.loc[dataframe.iloc[:, 1] == key]
    if not result.empty:
        return result.iloc[0, 2]  # Return the value from the 4th column
    return None  # Return None if the key does not exist


class BasicPortal(ParameterizableClass):
    """A base class for portal objects that enable access to 'outside' world.

    In a Pythagoras-based application, a portal is the application's 'window'
    into the non-ephemeral world outside the current application execution
    session. It's a connector that enables a link between runtime-only
    ephemeral state and a persistent state that can be saved and loaded
    across multiple runs of the application, and across multiple computers.

    A Pythagoras-based application can have multiple portals,
    and there is usually a current (default) portal, accessible via
    get_current_portal().

    BasicPortal is a base class for all portal objects. It provides foundational
    functionality for managing the portal stack and for accessing the current
    portal. It keeps track of all portals created in the system and manages
    the stack of entered ('active') portals. It also provides a method to
    clear all portals and their state.

    The class is not intended to be used directly. Instead, it should
    be subclassed to provide additional functionality.
    """
    _default_portal: BasicPortal|None = None
    _all_portals: dict = {}
    _entered_portals_stack: list = []
    _entered_portals_counters_stack: list = []
    entropy_infuser: random.Random = random.Random()

    _root_dict: PersiDict

    def __init__(self, root_dict:PersiDict|str|None = None):
        ParameterizableClass.__init__(self)
        if root_dict is None:
            root_dict = self.default_base_dir
        if not isinstance(root_dict, PersiDict):
            root_dict = FileDirDict(base_dir = str(root_dict))
        root_dict_params = root_dict.get_params()
        root_dict_params.update(digest_len=0)
        root_dict = type(root_dict)(**root_dict_params)
        self._root_dict = root_dict
        BasicPortal._all_portals[id(self)] = self

    @property
    def base_url(self) -> str:
        """Get the base URL of the portal"""
        return self._root_dict.base_url

    @property
    def is_current(self) -> bool:
        """Check if the portal is the current one"""
        return (len(BasicPortal._entered_portals_stack) > 0
                and BasicPortal._entered_portals_stack[-1] == self)


    def get_params(self) -> dict:
        """Get the portal's configuration parameters"""
        params = dict(root_dict=self._root_dict)
        return params


    def describe(self) -> pd.DataFrame:
        """Get a DataFrame describing the portal's current state"""
        all_params = []

        all_params.append(_describe_persistent_characteristic(
            BASE_DIRECTORY_TXT, self._root_dict.base_dir))
        all_params.append(_describe_persistent_characteristic(
            BACKEND_TYPE_TXT, self._root_dict.__class__.__name__))

        result = pd.concat(all_params)
        result.reset_index(drop=True, inplace=True)

        return result


    @property
    def default_base_dir(self) -> str:
        """Get the base directory for the default local portal.

        The default base directory is ~/.pythagoras/.default_portal

        Pythagoras connects to the default local portal
        when no other portal is specified in the
        program which uses Pythagoras.
        """
        home_directory = Path.home()
        target_directory = home_directory / ".pythagoras" / ".default_portal"
        target_directory.mkdir(parents=True, exist_ok=True)
        target_directory_str = str(target_directory.resolve())
        return target_directory_str


    @property
    def default_portal(self) -> BasicPortal:
        assert BasicPortal._default_portal is not None
        return BasicPortal._default_portal


    def __enter__(self):
        """Set the portal as the current one"""
        if (len(BasicPortal._entered_portals_stack) == 0 or
                id(BasicPortal._entered_portals_stack[-1]) != id(self)):
            BasicPortal._entered_portals_stack.append(self)
            BasicPortal._entered_portals_counters_stack.append(1)
        else:
            BasicPortal._entered_portals_counters_stack[-1] += 1
        return self


    def __exit__(self, exc_type, exc_val, exc_tb):
        """Remove the portal from the current context"""
        assert BasicPortal._entered_portals_stack[-1] == self, (
            "Inconsistent state of the portal stack. "
            + "Most probably, portal.__enter__() method was called explicitly "
            + "within a 'with' statement with another portal.")
        if BasicPortal._entered_portals_counters_stack[-1] == 1:
            BasicPortal._entered_portals_stack.pop()
            BasicPortal._entered_portals_counters_stack.pop()
        else:
            BasicPortal._entered_portals_counters_stack[-1] -= 1


    def _clear(self) -> None:
        """Clear the portal's state"""
        self._root_dict = None


    @classmethod
    def _clear_all(cls) -> None:
        """Remove all information about all the portals from the system."""
        for portal in BasicPortal._all_portals.values():
            portal._clear()
        BasicPortal._all_portals = dict()
        BasicPortal._entered_portals_stack = list()
        BasicPortal._entered_portals_counters_stack = list()
        BasicPortal.entropy_infuser = random.Random()


    def __getstate__(self):
        raise NotPicklableObject("Portals cannot be pickled.")


    def __setstate__(self, state):
        raise NotPicklableObject("Portals cannot be pickled.")

PortalType = TypeVar("PortalType")