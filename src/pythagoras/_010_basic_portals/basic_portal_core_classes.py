from __future__ import annotations

import random
import sys
from abc import abstractmethod
from pathlib import Path
from typing import TypeVar, Type, Any, NewType
import pandas as pd
from parameterizable import ParameterizableClass, sort_dict_by_keys

from persidict import PersiDict, FileDirDict
from .post_init_metaclass import PostInitMeta
from .not_picklable_class import NotPicklable
from .._800_signatures_and_converters import get_hash_signature

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


def _get_description_value_by_key(dataframe:pd.DataFrame, key:str) -> Any:
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

PortalStrID = NewType("PortalStrID", str)
PObjectStrID = NewType("PObjectStrID", str)

_all_known_portals: dict[PortalStrID, BasicPortal] = {}
_active_portals_stack: list = []
_active_portals_counters_stack: list = [int]
_most_recently_created_portal: BasicPortal | None = None

def get_number_of_known_portals() -> int:
    """Get the number of portals currently in the system."""
    global _all_known_portals
    return len(_all_known_portals)


def get_all_known_portals() -> list[BasicPortal]:
    """Get a list of all known portals."""
    global _all_known_portals
    return list(_all_known_portals.values())


def get_number_of_portals_in_active_stack() -> int:
    """Get the number of currently active portals."""
    global _active_portals_stack
    return len(set(_active_portals_stack))


def get_depth_of_active_portal_stack() -> int:
    """Get the depth of the active portal stack."""
    global _active_portals_counters_stack
    return sum(_active_portals_counters_stack)


def get_most_recently_created_portal() -> BasicPortal | None:
    """Get the most recently created portal, or None if no portals exist."""
    global _most_recently_created_portal
    return _most_recently_created_portal


def get_active_portal() -> BasicPortal:
    """Get the currently active portal object.

    The active portal is the one that was most recently entered
    using the 'with' statement. If no portal is currently active,
    it finds the most recently created portal and makes it active.
    If there are currently no portals exist in the system,
    it creates and returns the default portal.
    """
    global _most_recently_created_portal, _active_portals_stack

    if len(_active_portals_stack) > 0:
        return _active_portals_stack[-1]

    if _most_recently_created_portal is None:
        sys.modules["pythagoras"].instantiate_default_local_portal()

    _active_portals_stack.append(_most_recently_created_portal)
    _active_portals_counters_stack.append(1)
    return _most_recently_created_portal


def get_nonactive_portals() -> list[BasicPortal]:
    active_portal_str_id = get_active_portal()._str_id
    found_portals = []
    for portal_str_id, portal in _all_known_portals.items():
        if portal_str_id != active_portal_str_id:
            found_portals.append(portal)
    return found_portals


def get_default_portal_base_dir() -> str:
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
    assert isinstance(target_directory_str, str)
    return target_directory_str


class BasicPortal(NotPicklable,ParameterizableClass, metaclass = PostInitMeta):
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

    _entropy_infuser = random.Random()

    _root_dict: PersiDict | None
    _str_id_cache: PortalStrID | None


    def __init__(self, root_dict:PersiDict|str|None = None):
        ParameterizableClass.__init__(self)
        self._str_id_cache = None
        if root_dict is None:
            root_dict = get_default_portal_base_dir()
        if not isinstance(root_dict, PersiDict):
            root_dict = str(root_dict)
            root_dict = FileDirDict(base_dir = root_dict)
        root_dict_params = root_dict.get_params()
        root_dict_params.update(digest_len=0)
        root_dict = type(root_dict)(**root_dict_params)
        self._root_dict = root_dict


    def _post_init_hook(self) -> None:
        global _most_recently_created_portal, _all_known_portals
        _all_known_portals[self._str_id] = self
        _most_recently_created_portal = self


    def _get_linked_objects_ids(self
            , target_class: type | None = None) -> set[PObjectStrID]:
        """Get the set str_ids of objects, linked to the portal."""
        global _all_links_from_objects_to_portals
        result = set()
        for obj_str_id, portal_str_id in _all_links_from_objects_to_portals.items():
            assert isinstance(obj_str_id, str)
            assert isinstance(portal_str_id, str)
            if portal_str_id == self._str_id:
                if target_class is None:
                    result.add(obj_str_id)
                elif isinstance(target_class, type):
                    result.add(obj_str_id)
        return result


    def get_linked_objects(self, target_class: type | None = None) -> list[PortalAwareClass]:
        """Get the list of objects, linked to the portal"""

        found_linked_objects_ids = self._get_linked_objects_ids(target_class)
        found_linked_objects = []
        for obj_str_id in found_linked_objects_ids:
            new_object = _all_known_portal_aware_objects[obj_str_id]
            found_linked_objects.append(new_object)
        return found_linked_objects


    def get_number_of_linked_objects(self, target_class: type | None = None) -> int:
        """Get the number of linked portal-aware objects of the given class name."""
        return len(self._get_linked_objects_ids())


    @property
    def entropy_infuser(self) -> random.Random:
        return BasicPortal._entropy_infuser


    @property
    def base_url(self) -> str:
        """Get the base URL of the portal"""
        return self._root_dict.base_url


    @property
    def is_active(self) -> bool:
        """Check if the portal is the current one"""
        return (len(_active_portals_stack) > 0
                and _active_portals_stack[-1]._str_id == self._str_id)


    def get_params(self) -> dict:
        """Get the portal's configuration parameters"""
        params = dict(root_dict=self._root_dict)
        sorted_params = sort_dict_by_keys(params)
        return sorted_params


    @property
    def _ephemeral_param_names(self) -> set[str]:
        """Get the names of the portal's ephemeral parameters"""
        return set()


    @property
    def _str_id(self) -> PortalStrID:
        """Get the portal's persistent hash"""
        if hasattr(self,"_str_id_cache") and self._str_id_cache is not None:
            return self._str_id_cache
        else:
            params = self.get_portable_params()
            ephemeral_names = self._ephemeral_param_names
            nonephemeral_params = {k:params[k] for k in params
                if k not in ephemeral_names}
            self._str_id_cache = PortalStrID(
                get_hash_signature(nonephemeral_params))
            return self._str_id_cache


    def _invalidate_cache(self) -> None:
        """Invalidate object's caches"""
        self._str_id_cache = None


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


    def __enter__(self):
        """Set the portal as the current one"""
        global _active_portals_stack, _active_portals_counters_stack
        if (len(_active_portals_stack) == 0 or
                id(_active_portals_stack[-1]) != id(self)):
            _active_portals_stack.append(self)
            _active_portals_counters_stack.append(1)
        else:
            _active_portals_counters_stack[-1] += 1
        return self


    def __exit__(self, exc_type, exc_val, exc_tb):
        """Remove the portal from the current context"""
        global _active_portals_stack, _active_portals_counters_stack
        assert _active_portals_stack[-1] == self, (
            "Inconsistent state of the portal stack. "
            + "Most probably, portal.__enter__() method was called explicitly "
            + "within a 'with' statement with another portal.")
        if _active_portals_counters_stack[-1] == 1:
            _active_portals_stack.pop()
            _active_portals_counters_stack.pop()
        else:
            _active_portals_counters_stack[-1] -= 1


    def _clear(self) -> None:
        """Clear and invalidate the portal's state"""
        self._root_dict = None
        self._str_id_cache = None
        self._entropy_infuser = None
        # self._linked_objects = None


_all_known_portal_aware_objects: dict[PObjectStrID, PortalAwareClass] = dict()
_all_links_from_objects_to_portals: dict[PObjectStrID, PortalStrID] = dict()

def get_number_of_linked_portal_aware_objects() -> int:
    """Get the number of portal-aware objects currently linked to portals."""
    global _all_links_from_objects_to_portals
    return len(_all_links_from_objects_to_portals)


class PortalAwareClass(metaclass = PostInitMeta):
    """A base class for objects that need to access a portal.

    The class enables functionality for saving and loading its objects.
    When a portal-aware object is saved (pickled), the portal data is not saved,
    and the object is pickled as if it were a regular object.
    After the object is unpickled, the portal is restored to the current portal.

    The "current" portal is the innermost portal
    in the stack of portal "with" statements. It means that
    a portal-aware object can only be unpickled from within a portal context.

    A portal-aware object accepts a portal as an input parameter
    for its constructor. It also supports late portal binding: it
    can be created with `portal=None`, and its portal will be set later
    to the current portal.
    """

    # _linked_portal: BasicPortal | None
    _linked_portal_at_init: BasicPortal|None
    _hash_id_cache: PObjectStrID | None
    _visited_portals: set[str] | None

    def __init__(self, portal:BasicPortal|None=None):
        assert portal is None or isinstance(portal, BasicPortal)
        # self._linked_portal = portal
        self._linked_portal_at_init = portal
        self._hash_id_cache = None
        self._visited_portals = set()


    def _post_init_hook(self):
        """ This method is called after the object is fully initialized."""
        global _all_links_from_objects_to_portals
        global _all_known_portal_aware_objects

        _all_known_portal_aware_objects[self._str_id] = self
        if self._linked_portal_at_init is not None:
            _all_links_from_objects_to_portals[self._str_id
                ] = self._linked_portal_at_init._str_id


    @property
    def _linked_portal(self) -> BasicPortal | None:
        global _all_links_from_objects_to_portals, _all_known_portals
        portal = None
        if self._str_id in _all_links_from_objects_to_portals:
            portal_str_id = _all_links_from_objects_to_portals[self._str_id]
            assert isinstance(portal_str_id, str)
            portal = _all_known_portals[portal_str_id]
        return portal


    @property
    def portal(self) -> BasicPortal:
        # if self._linked_portal is None:
        #     self._try_to_find_linked_portal_and_register_there()
        global _all_links_from_objects_to_portals, _all_known_portals
        portal_to_use = self._linked_portal
        if portal_to_use is None:
            portal_to_use = get_active_portal()
        assert isinstance(portal_to_use, BasicPortal)
        if portal_to_use._str_id not in self._visited_portals:
            self._first_visit_to_portal(portal_to_use)
        return portal_to_use

    def _first_visit_to_portal(self, portal: BasicPortal) -> None:
        global _all_known_portal_aware_objects
        _all_known_portal_aware_objects[self._str_id] = self
        self._visited_portals.add(portal._str_id)


    # @portal.setter
    # def portal(self, new_portal: BasicPortal|None) -> None:
    #     """Set the portal to the given one."""
    #     assert new_portal is not None
    #     assert not hasattr(self, "_linked_portal") or self._linked_portal is None
    #     self._linked_portal = new_portal
    #     self._try_to_find_linked_portal_and_register_there()
    #     if new_portal._str_id not in self._visited_portals:
    #         self._first_visit_to_portal(new_portal)


    @property
    def _str_id(self) -> PObjectStrID:
        """Return the hash ID of the portal-aware object."""
        if hasattr(self, "_str_id_cache") and self._hash_id_cache is not None:
            return self._hash_id_cache
        else:
            self._hash_id_cache = PObjectStrID(get_hash_signature(self))
            return self._hash_id_cache


    @abstractmethod
    def __getstate__(self):
        """This method is called when the object is pickled.

        Make sure NOT to include portal info the object's state
        while pickling it.
        """
        raise NotImplementedError(
            "PortalAwareClass objects are not picklable. "
            "Method __getstate__() must be overridden in subclasses.")


    @abstractmethod
    def __setstate__(self, state):
        """This method is called when the object is unpickled.

        """
        self._invalidate_cache()
        self._visited_portals = set()


    def _invalidate_cache(self):
        self._hash_id_cache = None
        self._visited_portals = set()



def _clear_all_portals() -> None:
    """Remove all information about all the portals from the system."""
    global _all_known_portals, _active_portals_stack
    global _active_portals_counters_stack
    global _most_recently_created_portal
    global _all_links_from_objects_to_portals
    global _all_known_portal_aware_objects

    for obj_str_id in _all_known_portal_aware_objects:
        obj = _all_known_portal_aware_objects[obj_str_id]
        obj._invalidate_cache()

    for portal in _all_known_portals.values():
        portal._clear()
    _all_known_portals = dict()
    _active_portals_stack = list()
    _active_portals_counters_stack = list()
    _most_recently_created_portal = None
    _all_links_from_objects_to_portals = dict()


PortalType = TypeVar("PortalType")