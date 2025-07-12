"""This modukle provides foundational functionality for wotk with portals,
specifically for managing the portal stack and for accessing the current
portal. It keeps track of all portals created in the system and manages
the stack of entered ('active') portals. It also provides a method to
clear all portals and their state.
"""

from __future__ import annotations

import collections
import random
import sys
from abc import abstractmethod
from pathlib import Path
from typing import TypeVar, Type, Any, NewType
import pandas as pd
from parameterizable import ParameterizableClass, sort_dict_by_keys

from persidict import PersiDict, FileDirDict, SafeStrTuple
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
    """Get the number of portals in a stack."""
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
        sys.modules["pythagoras"]._instantiate_default_local_portal()

    _active_portals_stack.append(_most_recently_created_portal)
    _active_portals_counters_stack.append(1)
    return _most_recently_created_portal


def get_nonactive_portals() -> list[BasicPortal]:
    """Get a list of all portals that are not in the active stack."""
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
    get_active_portal().

    BasicPortal is a base class for all portal objects.

    The class is not intended to be used directly. Instead, it should
    be subclassed to provide additional functionality.
    """

    _entropy_infuser = random.Random()

    _root_dict: PersiDict | None
    _str_id_cache: PortalStrID


    def __init__(self, root_dict:PersiDict|str|None = None):
        ParameterizableClass.__init__(self)
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
        """This method is always called after all __init__() methods"""
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
            new_object = _all_activated_portal_aware_objects[obj_str_id]
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
        """Check if the portal is the current one.

        The 'active' portal is the innermost portal
        in the stack of portal's 'with' statements.
        """
        return (len(_active_portals_stack) > 0
                and _active_portals_stack[-1]._str_id == self._str_id)


    def get_params(self) -> dict:
        """Get the portal's configuration parameters"""
        params = dict(root_dict=self._root_dict)
        sorted_params = sort_dict_by_keys(params)
        return sorted_params


    @property
    def _ephemeral_param_names(self) -> set[str]:
        """Get the names of the portal's ephemeral parameters.

        Portal's ephemeral parameters are not stored persistently.
        They affect behaviour of a portal object in an application session,
        but they do not affect behaviour of the actual portal across multiple runs.
        """
        return set()


    @property
    def _str_id(self) -> PortalStrID:
        """Get the portal's persistent hash.

        It's an internal hash used by Pythagoras and is different from .__hash__()
        """
        if not hasattr(self,"_str_id_cache"):
            params = self.get_portable_params()
            ephemeral_names = self._ephemeral_param_names
            nonephemeral_params = {k:params[k] for k in params
                if k not in ephemeral_names}
            self._str_id_cache = PortalStrID(
                get_hash_signature(nonephemeral_params))
        return self._str_id_cache


    def _invalidate_cache(self) -> None:
        """Invalidate the portal's attribute cache.

        If the portal's attribute named ATTR is cached,
        its cached value will be stored in an attribute named _ATTR_cache
        This method should delete all such attributes.
        """
        if hasattr(self, "_str_id_cache"):
            del self._str_id_cache


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
        """Set the portal as the active one and add it to the stack"""
        global _active_portals_stack, _active_portals_counters_stack
        if (len(_active_portals_stack) == 0 or
                id(_active_portals_stack[-1]) != id(self)):
            _active_portals_stack.append(self)
            _active_portals_counters_stack.append(1)
        else:
            _active_portals_counters_stack[-1] += 1
        return self


    def __exit__(self, exc_type, exc_val, exc_tb):
        """Pop the portal from the stack of active ones"""
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
        self._invalidate_cache()
        self._root_dict = None
        self._entropy_infuser = None


_all_activated_portal_aware_objects: dict[PObjectStrID, PortalAwareClass] = dict()
_all_links_from_objects_to_portals: dict[PObjectStrID, PortalStrID] = dict()

def get_number_of_linked_portal_aware_objects() -> int:
    """Get the number of portal-aware objects currently linked to portals."""
    global _all_links_from_objects_to_portals
    return len(_all_links_from_objects_to_portals)


class PortalAwareClass(metaclass = PostInitMeta):
    """A base class for objects that need to access a portal.

    These objects either always work with a currently active portal,
    or they have a preferred (linked) portal which they activate every
    time their methods are called.
    """

    # _linked_portal: BasicPortal | None
    _linked_portal_at_init: BasicPortal|None
    _hash_id_cache: PObjectStrID
    _visited_portals: set[str] | None

    def __init__(self, portal:BasicPortal|None=None):
        assert portal is None or isinstance(portal, BasicPortal)
        self._linked_portal_at_init = portal
        # self._hash_id_cache = None
        self._visited_portals = set()


    def _post_init_hook(self):
        """ This method is called after all object's .__init__() methods."""
        global _all_links_from_objects_to_portals
        global _all_activated_portal_aware_objects
        if self._linked_portal_at_init is not None:
            _all_links_from_objects_to_portals[self._str_id
                ] = self._linked_portal_at_init._str_id
            self._first_visit_to_portal(self._linked_portal_at_init)


    @property
    def _linked_portal(self) -> BasicPortal | None:
        """Get the portal's preferred (linked) portal.

        If the linked portal is not None, the object will activate
        this portal every time the object's methods are called.
        If it's None, the object will never try to change the active portal.
        """
        global _all_links_from_objects_to_portals, _all_known_portals
        portal = None
        if (self._linked_portal_at_init is not None
                and self._str_id not in _all_links_from_objects_to_portals):
            _all_links_from_objects_to_portals[self._str_id
                ] = self._linked_portal_at_init._str_id
            self._visit_portal(self._linked_portal_at_init)
            portal = self._linked_portal_at_init
        elif self._str_id in _all_links_from_objects_to_portals:
            portal_str_id = _all_links_from_objects_to_portals[self._str_id]
            assert isinstance(portal_str_id, str)
            portal = _all_known_portals[portal_str_id]
        return portal


    @property
    def portal(self) -> BasicPortal:
        """Get the portal which the object's methods will be using.

        It's either the object's linked portal or
        (if the linked portal is None) the currently active portal.
        """
        global _all_links_from_objects_to_portals, _all_known_portals
        portal_to_use = self._linked_portal
        if portal_to_use is None:
            portal_to_use = get_active_portal()
        self._visit_portal(portal_to_use)
        return portal_to_use


    def _visit_portal(self, portal: BasicPortal) -> None:
        if portal._str_id not in self._visited_portals:
            self._first_visit_to_portal(portal)


    def _first_visit_to_portal(self, portal: BasicPortal) -> None:
        """Register an object in a portal that the object has not seen before."""
        global _all_activated_portal_aware_objects
        _all_activated_portal_aware_objects[self._str_id] = self
        self._visited_portals.add(portal._str_id)


    @property
    def _str_id(self) -> PObjectStrID:
        """Return the hash ID of the portal-aware object.

        It's an internal hash used by Pythagoras and is different from .__hash__()
        """
        if not hasattr(self, "_str_id_cache"):
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
        """This method is called when the object is unpickled."""
        self._invalidate_cache()
        self._visited_portals = set()
        self._linked_portal_at_init = None


    def _invalidate_cache(self):
        """Invalidate the object's attribute cache.

        If the object's attribute named ATTR is cached,
        its cached value will be stored in an attribute named _ATTR_cache
        This method should delete all such attributes.
        """
        if hasattr(self, "_hash_id_cache"):
            del self._hash_id_cache


    @property
    def is_activated(self) -> bool:
        """Return True if the object has been registered in at least one of the portals."""
        global _all_activated_portal_aware_objects
        if len(self._visited_portals) >=1:
            assert self._str_id in _all_activated_portal_aware_objects
            return True
        return False


    def _deactivate(self):
        """Mark the object as not activated.

        Empty the list of portals it has been registered into.
        """
        global _all_activated_portal_aware_objects
        assert self.is_activated
        del _all_activated_portal_aware_objects[self._str_id]
        self._invalidate_cache()
        self._visited_portals = set()


def _clear_all_portals() -> None:
    """Remove all information about all the portals from the system."""
    global _all_known_portals, _active_portals_stack
    global _active_portals_counters_stack
    global _most_recently_created_portal
    global _all_links_from_objects_to_portals
    global _all_activated_portal_aware_objects

    for obj in list(_all_activated_portal_aware_objects.values()):
        obj._deactivate()

    for portal in _all_known_portals.values():
        portal._clear()

    _all_known_portals.clear()
    _active_portals_stack.clear()
    _active_portals_counters_stack.clear()
    _most_recently_created_portal = None
    _all_links_from_objects_to_portals.clear()
    _all_activated_portal_aware_objects.clear()


PortalType = TypeVar("PortalType")


##################################################

def _visit_portal(obj:Any, portal:BasicPortal) -> None:
    return _visit_portal_impl(obj, portal=portal)


def _visit_portal_impl(obj:Any, portal:BasicPortal, seen=None)->None:
    if seen is None:
        seen = set()

    if id(obj) in seen:
        return

    if isinstance(obj, (str, range, bytearray, bytes)):
        return

    if isinstance(obj, SafeStrTuple):
        return

    seen.add(id(obj))

    if isinstance(obj, PortalAwareClass):
        obj._visit_portal(portal)
        return

    if isinstance(obj, (list, tuple)):
        for item in obj:
            _visit_portal_impl(item, portal, seen)
        return

    if isinstance(obj, dict):
        for item in obj.values():
            _visit_portal_impl(item, portal, seen)
        return

    # TODO: decide how to deal with Sequences/Mappings
    # if isinstance(obj, collections.abc.Sequence):
    #     raise TypeError("Unsupported Sequence type: " + str(type(obj)))
    #
    # if isinstance(obj, collections.abc.Mapping):
    #     raise TypeError("Unsupported Mapping type: " + str(type(obj)))