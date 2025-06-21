from __future__ import annotations

import random
import sys
from abc import abstractmethod
from pathlib import Path
from typing import TypeVar, Type, Any
import pandas as pd
from parameterizable import ParameterizableClass

from persidict import PersiDict, FileDirDict
from .post_init_metaclass import PostInitMeta
from .not_picklable import NotPicklable
from .._820_strings_signatures_converters import get_hash_signature

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


_all_known_portals: dict[str, BasicPortal] = {}
_active_portals_stack: list = []
_active_portals_counters_stack: list = []
_most_recently_created_portal: BasicPortal | None = None

def number_of_known_portals() -> int:
    """Get the number of portals currently in the system."""
    global _all_known_portals
    return len(_all_known_portals)


def number_of_active_portals() -> int:
    """Get the number of currently active portals."""
    global _active_portals_stack
    return len(set(_active_portals_stack))


def depth_of_active_portal_stack() -> int:
    """Get the depth of the active portal stack."""
    global _active_portals_counters_stack
    return sum(_active_portals_counters_stack)


def most_recently_created_portal() -> BasicPortal|None:
    """Get the most recently created portal, or None if no portals exist."""
    global _most_recently_created_portal
    return _most_recently_created_portal


def active_portal() -> BasicPortal:
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


def nonactive_portals() -> list[BasicPortal]:
    active_portal_str_id = active_portal()._str_id
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
    _str_id_cache: str | None
    _linked_objects: dict | None


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
        self._linked_objects = dict()


    def _post_init_hook(self) -> None:
        global _most_recently_created_portal
        if self._str_id in _all_known_portals:
            self._update_from_twin(_all_known_portals[self._str_id])
        else:
            _all_known_portals[self._str_id] = self
            _most_recently_created_portal = self


    def _update_from_twin(self, other: BasicPortal) -> None:
        """Update the portal's state from another portal."""
        if not type(self) is type(other):
            raise TypeError("Can only update from exactly the same type.")
        self._invalidate_cache()
        assert self._str_id == other._str_id
        self._linked_objects = other._linked_objects


    def linked_objects_ids(self, target_class:type|None = None) -> set[str]:
        """Get the set of known functions' IDs"""
        found_linked_objects = set()
        for object_class, set_of_object_str_ids in self._linked_objects.items():
            if target_class is None:
                found_linked_objects |= set_of_object_str_ids
            elif issubclass(object_class, target_class):
                found_linked_objects |= set_of_object_str_ids
        return found_linked_objects


    def linked_objects(self, target_class:type|None = None) -> list[PortalAwareClass]:
        """Get the list of linked objects of the given class and subclasses."""
        found_linked_objects_ids = self.linked_objects_ids(target_class)
        found_linked_objects = []
        for obj_str_id in found_linked_objects_ids:
            new_object = _all_linked_portal_aware_objects[obj_str_id]
            found_linked_objects.append(new_object)
        return found_linked_objects


    def number_of_linked_objects(self, target_class:type|None = None) -> int:
        """Get the number of linked portal-aware objects of the given class name."""
        linked_objects_counter = 0
        for object_class, set_of_object_str_ids in self._linked_objects.items():
            if target_class is None:
                linked_objects_counter += len(set_of_object_str_ids)
            elif issubclass(object_class,target_class):
                linked_objects_counter += len(set_of_object_str_ids)
        return linked_objects_counter


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
        sorted_params = dict(sorted(params.items()))
        return sorted_params


    @property
    def _ephemeral_param_names(self) -> set[str]:
        """Get the names of the portal's ephemeral parameters"""
        return set()


    @property
    def _str_id(self) -> str:
        """Get the portal's persistent hash"""
        if hasattr(self,"_str_id_cache") and self._str_id_cache is not None:
            return self._str_id_cache
        else:
            params = self.get_portable_params()
            ephemeral_names = self._ephemeral_param_names
            nonephemeral_params = {k:params[k] for k in params
                if k not in ephemeral_names}
            self._str_id_cache = get_hash_signature(nonephemeral_params)
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
        self._linked_objects = None


# A global dictionary to keep track of all portal-aware objects
# that are linked to a portal.
_all_linked_portal_aware_objects: dict[str, PortalAwareClass] = {}

def number_of_linked_portal_aware_objects() -> int:
    """Get the number of portal-aware objects currently linked to portals."""
    global _all_linked_portal_aware_objects
    return len(_all_linked_portal_aware_objects)


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

    _linked_portal: BasicPortal | None
    _portal_at_init: BasicPortal|None
    _hash_id_cache: str | None
    _visited_portals: set[str] | None

    def __init__(self, portal:BasicPortal|None=None):
        assert portal is None or isinstance(portal, BasicPortal)
        self._linked_portal = portal
        self._portal_at_init = portal
        self._hash_id_cache = None
        self._visited_portals = set()


    def _post_init_hook(self):
        """ This method is called after the object is fully initialized."""
        self._try_to_find_linked_portal_and_register_there()


    def _try_to_find_linked_portal_and_register_there(self):
        if self._str_id in _all_linked_portal_aware_objects:
            self._update_from_twin(_all_linked_portal_aware_objects[self._str_id])
        elif hasattr(self, "_linked_portal") and self._linked_portal is not None:
            self._register_in_portal()


    def _register_in_portal(self):
        """Register the object in the linked portal.
        """
        global _all_linked_portal_aware_objects
        assert hasattr(self, '_linked_portal')
        assert self._linked_portal is not None
        assert isinstance(self._linked_portal, BasicPortal)
        if self._str_id in _all_linked_portal_aware_objects:
            raise ValueError(f"A object with {self._str_id=}"
                "is already registered. It can only be registered once.")
        _all_linked_portal_aware_objects[self._str_id] = self
        portal = self._linked_portal
        if type(self) not in portal._linked_objects:
            portal._linked_objects[type(self)] = set()
        portal._linked_objects[type(self)].add(self._str_id)


    def _update_from_twin(self, other: PortalAwareClass) -> None:
        """Update the object from another one with the same str_id"""
        if self is other:
            return
        if not type(self) is type(other):
            raise TypeError("Can only update from exactly the same type.")
        if not self._str_id == other._str_id:
            raise ValueError("Can only update from a twin.")
        self._invalidate_cache()
        self._linked_portal = other._linked_portal
        self._visited_portals.add(self._linked_portal._str_id)


    @property
    def portal(self) -> BasicPortal:
        if self._linked_portal is None:
            self._try_to_find_linked_portal_and_register_there()
        portal_to_use = self._linked_portal
        if portal_to_use is None:
            portal_to_use = active_portal()
        if portal_to_use._str_id not in self._visited_portals:
            self._first_visit_to_portal(portal_to_use)
        return portal_to_use

    def _first_visit_to_portal(self, portal: BasicPortal) -> None:
        self._visited_portals.add(portal._str_id)


    @portal.setter
    def portal(self, new_portal: BasicPortal|None) -> None:
        """Set the portal to the given one."""
        assert new_portal is not None
        assert not hasattr(self, "_linked_portal") or self._linked_portal is None
        self._linked_portal = new_portal
        self._try_to_find_linked_portal_and_register_there()
        if new_portal._str_id not in self._visited_portals:
            self._first_visit_to_portal(new_portal)

    #
    # def _portal_typed(self
    #         , expected_type: PortalType = BasicPortal
    #         ) -> PortalType:
    #     assert issubclass(expected_type, BasicPortal)
    #     portal = self.portal
    #     assert isinstance(portal, expected_type)
    #     return portal


    @property
    def _str_id(self) -> str:
        """Return the hash ID of the portal-aware object."""
        if hasattr(self, "_str_id_cache") and self._hash_id_cache is not None:
            return self._hash_id_cache
        else:
            self._hash_id_cache = get_hash_signature(self)
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
        self._linked_portal = None
        self._invalidate_cache()
        self._visited_portals = set()


    def _invalidate_cache(self):
        self._hash_id_cache = None


def _clear_all_portals() -> None:
    """Remove all information about all the portals from the system."""
    global _all_known_portals, _active_portals_stack
    global _active_portals_counters_stack
    global _most_recently_created_portal
    global _all_linked_portal_aware_objects

    for portal in _all_known_portals.values():
        portal._clear()
    _all_known_portals = dict()
    _active_portals_stack = list()
    _active_portals_counters_stack = list()
    _most_recently_created_portal = None
    _all_linked_portal_aware_objects = dict()


PortalType = TypeVar("PortalType")