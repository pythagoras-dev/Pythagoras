"""This module provides foundational functionality for work with portals.

This module specifically handles portal stack management and provides access to the current
portal. It keeps track of all portals created in the system and manages
the stack of entered ('active') portals. It also provides a way to
clear all portals and their state.
"""

from __future__ import annotations

import random
from abc import abstractmethod
from importlib import metadata
from typing import TypeVar, Any, NewType, Callable
import pandas as pd
from parameterizable import NotPicklableClass
from parameterizable import ParameterizableClass, sort_dict_by_keys

from persidict import PersiDict, FileDirDict, SafeStrTuple
from .guarded_init_metaclass import GuardedInitMeta
from .single_thread_enforcer import _ensure_single_thread, _reset_single_thread_enforcer
from .._800_signatures_and_converters import get_hash_signature
from .portal_description_helpers import (
    _describe_persistent_characteristic,
    _describe_runtime_characteristic)
from .default_portal_base_dir import get_default_portal_base_dir

_BASE_DIRECTORY_TXT = "Base directory"
_BACKEND_TYPE_TXT = "Backend type"
_PYTHAGORAS_VERSION_TXT = "Pythagoras version"


PortalStrID = NewType("PortalStrID", str)
PAwareObjectStrID = NewType("PAwareObjectStrID", str)


class _PortalRegistry(NotPicklableClass):
    """
    A container for every piece of mutable “portal bookkeeping”
    needed by Pythagoras.

    Stored data
    -----------
    known_portals : dict[PortalStrID, BasicPortal]
        All portals that have been instantiated in the system.
    active_stack : list[BasicPortal]
        Stack that mirrors nested ``with portal:`` blocks.
    active_counters : list[int]
        Re-entrancy counters that align one-to-one with *active_stack*.
    most_recently_created : BasicPortal | None
        Last portal created in the system.
    links_obj2portal : dict[PObjectStrID, PortalStrID]
        Mapping from object identifier to the str-id of its linked portal.
    activated_objects : dict[PObjectStrID, PortalAwareClass]
        Reverse lookup from object identifier to the actual object instance.
    default_portal_instantiator : Callable[[], None] | None
        A callable that creates a default portal when none exists.
    """

    def __init__(self) -> None:
        _ensure_single_thread()
        self.known_portals: dict[PortalStrID, BasicPortal] = {}
        self.active_portals_stack: list[BasicPortal] = []
        self.active_portals_stack_counters: list[int] = []
        self.most_recently_created_portal: BasicPortal | None = None
        self.links_from_objects_to_portals: dict[PAwareObjectStrID, PortalStrID] = {}
        self.known_objects: dict[PAwareObjectStrID, PortalAwareClass] = {}
        self.default_portal_instantiator: Callable[[], None] | None = None


    def register_default_portal_instantiator(self, instantiator: Callable[[], None]) -> None:
        """Register a callable that creates (and usually enters) the default portal."""
        _ensure_single_thread()
        if not callable(instantiator):
            raise TypeError(
                f"Default portal instantiator must be callable, got {type(instantiator)}")

        if self.default_portal_instantiator is not None:
            raise RuntimeError(
                "Default portal instantiator is already set; "
                "resetting is not permitted."
            )

        self.default_portal_instantiator = instantiator


    def register_portal(self, portal: BasicPortal) -> None:
        """Add *portal* to the registry and remember it as the most recent one."""
        _ensure_single_thread()
        self.known_portals[portal._str_id] = portal
        self.most_recently_created_portal = portal

    def count_known_portals(self) -> int:
        return len(self.known_portals)

    def all_portals(self) -> list[BasicPortal]:
        return list(self.known_portals.values())

    def push_new_active_portal(self, portal: BasicPortal) -> None:
        """Put *portal* on top of the active-stack, handling re-entrancy."""
        _ensure_single_thread()
        if not portal._str_id in self.known_portals:
            raise RuntimeError(f"Attempt to push an unregistered portal onto the stack")
        if self.active_portals_stack and self.active_portals_stack[-1] is portal:
            self.active_portals_stack_counters[-1] += 1
        else:
            self.active_portals_stack.append(portal)
            self.active_portals_stack_counters.append(1)

        if len(self.active_portals_stack) != len(self.active_portals_stack_counters):
            raise RuntimeError("Internal error: active_stack and active_counters are out of sync")

    def pop_active_portal(self, portal: BasicPortal) -> None:
        """Remove the current active portal, keeping the stack consistent."""
        _ensure_single_thread()
        if not portal._str_id in self.known_portals:
            raise RuntimeError(f"Attempt to pop an unregistered portal from the stack")

        if not self.active_portals_stack or self.active_portals_stack[-1] is not portal:
            raise RuntimeError("Attempt to pop an unexpected portal from the stack")

        if self.active_portals_stack_counters[-1] == 1:
            self.active_portals_stack.pop()
            self.active_portals_stack_counters.pop()
        else:
            self.active_portals_stack_counters[-1] -= 1

        if len(self.active_portals_stack) != len(self.active_portals_stack_counters):
            raise RuntimeError("Internal error: active_stack and active_counters are out of sync")


    def current_active_portal(self) -> BasicPortal:
        """Get the currently active portal object.

        The active portal is the one that was most recently entered
        using the 'with' statement. If no portal is currently active,
        it finds the most recently created portal and makes it current active.
        If there are currently no portals exist in the system,
        it creates and returns the default portal.

        Returns:
            The currently active portal instance.
        """
        if self.active_portals_stack:
            return self.active_portals_stack[-1]

        if self.most_recently_created_portal is None:
            if self.default_portal_instantiator is not None:
                self.default_portal_instantiator()
                if self.most_recently_created_portal is None:
                    raise RuntimeError("Default portal instantiator failed to create a portal")
                elif not isinstance(self.most_recently_created_portal, BasicPortal):
                    raise RuntimeError(
                        f"Default portal instantiator created an object of type "
                        f"{type(self.most_recently_created_portal).__name__}, "
                        f"expected BasicPortal")
            else:
                raise RuntimeError(
                    "No portal is active and no default portal instantiator was set "
                    "using _set_default_portal_instantiator()")

        self.active_portals_stack.append(self.most_recently_created_portal)
        self.active_portals_stack_counters.append(1)
        return self.most_recently_created_portal

    def is_current_active_portal(self, portal: BasicPortal) -> bool:
        """Check if *portal* is the currently active one."""
        return (len(self.active_portals_stack) > 0
                and self.active_portals_stack[-1]._str_id == portal._str_id)

    def unique_active_portals_count(self) -> int:
        return len(set(self.active_portals_stack))

    def active_portals_stack_depth(self) -> int:
        return sum(self.active_portals_stack_counters)

    def register_linked_object(self, portal: BasicPortal, obj:PortalAwareClass) -> None:
        """Record that *obj* (identified by *obj_id*) is linked to *portal*.

        An object being linked to a portal means that it will use that portal
        for all its operations unless explicitly told otherwise.
        """
        obj_id = obj._str_id
        portal_id = portal._str_id
        self.links_from_objects_to_portals[obj_id] = portal_id
        #TODO: should we do some registration / activation here?
        self.known_objects[obj_id] = obj


    def count_linked_objects(self) -> int:
        return len(self.links_from_objects_to_portals)

    def clear(self) -> None:
        """Erase every stored entry – mainly for unit-test clean-up."""
        self.known_portals.clear()
        self.active_portals_stack.clear()
        self.active_portals_stack_counters.clear()
        self.most_recently_created_portal = None
        self.links_from_objects_to_portals.clear()
        self.known_objects.clear()
        self.default_portal_instantiator = None


    def linked_objects_ids(self
            , portal: BasicPortal
            , target_class: type | None = None) -> set[PAwareObjectStrID]:
        """Get IDs of objects linked to the specified portal, optionally filtered by class."""
        obj_ids = (o for o, p in self.links_from_objects_to_portals.items() if p == portal._str_id)

        if target_class is None:
            return set(obj_ids)

        result = set()
        for obj_id in obj_ids:
            if isinstance(self.known_objects[obj_id], target_class):
                result.add(obj_id)
        return result

    def linked_objects(self
            , portal: BasicPortal
            , target_class: type | None = None) -> list[PortalAwareClass]:
        """Get objects linked to the specified portal, optionally filtered by class."""
        obj_ids = self.linked_objects_ids(portal, target_class)
        result = []
        for obj_id in obj_ids:
            obj = self.known_objects.get(obj_id)
            result.append(obj)
        return result

    def fetch_linked_portal(self, obj: PortalAwareClass) -> BasicPortal | None:
        """Get the portal linked to the object, handling lazy registration."""
        portal = None
        if (obj._linked_portal_at_init is not None
                and obj._str_id not in self.links_from_objects_to_portals):
            self.register_linked_object(
                obj._str_id, obj._linked_portal_at_init, obj)
            obj._visit_portal(obj._linked_portal_at_init)
            portal = obj._linked_portal_at_init
        elif obj._str_id in self.links_from_objects_to_portals:
            portal_str_id = self.links_from_objects_to_portals[obj._str_id]
            if not isinstance(portal_str_id, str):
                raise TypeError(f"Expected portal_str_id to be str, got {type(portal_str_id).__name__}")
            portal = self.known_portals[portal_str_id]
        return portal

    def register_object(self, obj: PortalAwareClass) -> None:
        """Register an object as activated."""
        self.known_objects[obj._str_id] = obj

    def is_object_registered(self, obj: PortalAwareClass) -> bool:
        """Check if an object is currently activated."""
        return obj._str_id in self.known_objects


# Singleton instance used by the rest of the module
_PORTAL_REGISTRY = _PortalRegistry()


class BasicPortal(NotPicklableClass, ParameterizableClass, metaclass = GuardedInitMeta):
    """A base class for portal objects that enable access to 'outside' world.

    In a Pythagoras-based application, a portal is the application's 'window'
    into the non-ephemeral world outside the current application execution
    session. It's a connector that enables a link between runtime-only
    ephemeral state and a persistent state that can be saved and loaded
    across multiple runs of the application, and across multiple computers.

    A Pythagoras-based application can have multiple portals,
    and there is usually a currently active one, accessible via
    get_current_active_portal().

    BasicPortal is a base class for all portal objects.

    The class is not intended to be used directly. Instead, it should
    be subclassed to provide additional functionality.
    """

    _entropy_infuser: random.Random | None

    _root_dict: PersiDict | None
    _str_id_cache: PortalStrID
    _init_finished:bool


    def __init__(self, root_dict:PersiDict|str|None = None):
        """Initialize a BasicPortal instance.

        Sets up the portal with a root dictionary for persistent storage.
        If no root_dict is provided, uses the default portal base directory
        to create a FileDirDict.

        Args:
            root_dict: The root dictionary for persistent storage, a path string,
                or None to use the default location. If a string is provided,
                it will be converted to a FileDirDict using that path.
        """
        _ensure_single_thread()
        self._init_finished = False
        self._entropy_infuser = random.Random()
        ParameterizableClass.__init__(self)
        if root_dict is None:
            root_dict = get_default_portal_base_dir() #TODO: check this logic
        if not isinstance(root_dict, PersiDict):
            root_dict = str(root_dict)
            root_dict = FileDirDict(base_dir = root_dict)
        root_dict_params = root_dict.get_params()
        root_dict_params.update(digest_len=0)
        root_dict = type(root_dict)(**root_dict_params)
        self._root_dict = root_dict


    def __post_init__(self) -> None:
        """Execute post-initialization tasks for the portal.

        This method is automatically called after all __init__() methods
        complete. It registers the portal in the global registry and updates
        the most recently created portal reference.
        """
        _PORTAL_REGISTRY.register_portal(self)


    def _get_linked_objects_ids(self
            , target_class: type | None = None) -> set[PAwareObjectStrID]:
        """Get the set of string IDs of objects linked to this portal.

        Args:
            target_class: The class type to filter for, or None to include
                all linked objects regardless of type.

        Returns:
            A set of string IDs representing objects linked to this portal,
            optionally filtered by the specified target class.
        """
        return _PORTAL_REGISTRY.linked_objects_ids(self, target_class)


    def get_linked_objects(self, target_class: type | None = None) -> list[PortalAwareClass]:
        """Get the list of objects linked to this portal.

        Args:
            target_class: The class type to filter for, or None to include
                all linked objects regardless of type.

        Returns:
            A list of PortalAwareClass instances that are linked to this portal,
            optionally filtered by the specified target class.
        """
        return _PORTAL_REGISTRY.linked_objects(self, target_class)


    def get_number_of_linked_objects(self, target_class: type | None = None) -> int:
        """Get the number of objects linked to this portal.

        Args:
            target_class: The class type to filter for, or None to include
                all linked objects regardless of type.

        Returns:
            The count of portal-aware objects linked to this portal,
            optionally filtered by the specified target class.
        """
        return len(self._get_linked_objects_ids(target_class))


    @property
    def entropy_infuser(self) -> random.Random:
        """Get the shared random number generator for the portal system.

        Returns:
            A Random instance shared across all BasicPortal instances for
            generating random values and entropy when needed.
        """
        if self._entropy_infuser is None:
            raise RuntimeError("Entropy infuser is None."
                               "Most probably, it was cleared by calling portal._clear()"
                               "You cant't use a portal after calling portal._clear()")

        return self._entropy_infuser


    @property
    def is_current_active(self) -> bool:
        """Check if the portal is the current one.

        The 'current active' portal is the innermost portal
        in the stack of portal's 'with' statements.
        """
        return _PORTAL_REGISTRY.is_current_active_portal(self)


    def get_params(self) -> dict[str,Any]:
        """Get the portal's configuration parameters"""
        params = dict(root_dict=self._root_dict)
        sorted_params = sort_dict_by_keys(params)
        return sorted_params


    @property
    def _str_id(self) -> PortalStrID:
        """Get the portal's persistent hash.

        It's an internal hash used by Pythagoras and is different from .__hash__()

        The method should only be called after the portal has been fully initialized.
        """
        if not self._init_finished:
            raise RuntimeError("Portal is not fully initialized yet, "
                               "_str_id is not available.")
        if not hasattr(self,"_str_id_cache"):
            self._str_id_cache = PortalStrID(
                get_hash_signature(self.get_essential_jsparams()))
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

        all_params.append(_describe_runtime_characteristic(
            _PYTHAGORAS_VERSION_TXT, metadata.version("pythagoras")))
        all_params.append(_describe_persistent_characteristic(
            _BASE_DIRECTORY_TXT, self._root_dict.base_dir))
        all_params.append(_describe_persistent_characteristic(
            _BACKEND_TYPE_TXT, self._root_dict.__class__.__name__))

        result = pd.concat(all_params)
        result.reset_index(drop=True, inplace=True)

        return result


    def __enter__(self):
        """Set the portal as the active one and add it to the stack"""
        _PORTAL_REGISTRY.push_new_active_portal(self)
        return self


    def __exit__(self, exc_type, exc_val, exc_tb):
        """Pop the portal from the stack of active ones"""
        _ensure_single_thread()
        _PORTAL_REGISTRY.pop_active_portal(self)


    def _clear(self) -> None:
        """Clear and invalidate the portal's state.

        The portal must not be used after this method is called.
        """
        self._invalidate_cache()
        self._root_dict = None
        self._entropy_infuser = None
        self._init_finished = False


class PortalAwareClass(metaclass = GuardedInitMeta):
    """A base class for objects that need to access a portal.

    These objects either always work with a currently active portal,
    or they have a preferred (linked) portal which they activate every
    time their methods are called.
    """

    _linked_portal_at_init: BasicPortal|None
    _hash_id_cache: PAwareObjectStrID
    _visited_portals: set[str] | None

    def __init__(self, portal:BasicPortal|None=None):
        """Initialize a PortalAwareClass instance.

        Sets up the object with an optional linked portal. If a portal is provided,
        the object will be linked to that portal and will use it for all operations.
        If no portal is provided, the object will use currently active portals.

        Args:
            portal: The portal to link this object to, or None to use
                current active portals for operations.
        """
        _ensure_single_thread()
        self._init_finished = False
        if not (portal is None or isinstance(portal, BasicPortal)):
            raise TypeError(f"portal must be a BasicPortal or None, got {type(portal).__name__}")
        self._linked_portal_at_init = portal
        # self._hash_id_cache = None
        self._visited_portals = set()
        self._init_finished = False


    def __post_init__(self):
        """Execute post-initialization tasks for the portal-aware object.

        This method is automatically called after all object's __init__() methods
        complete. It registers the object with its linked portal if one was provided
        during initialization, establishing the connection between the object and portal.
        """
        if self._linked_portal_at_init is not None:
            _PORTAL_REGISTRY.register_linked_object(
                self._linked_portal_at_init, self)
            self._first_visit_to_portal(self._linked_portal_at_init)


    @property
    def _linked_portal(self) -> BasicPortal | None:
        """Get the portal's preferred (linked) portal.

        If the linked portal is not None, the object will activate
        this portal every time the object's methods are called.
        If it's None, the object will never try to change the active portal.
        """
        return _PORTAL_REGISTRY.fetch_linked_portal(self)


    @property
    def portal(self) -> BasicPortal:
        """Get the portal which the object's methods will be using.

        It's either the object's linked portal or
        (if the linked portal is None) the currently active portal.
        """
        portal_to_use = self._linked_portal
        if portal_to_use is None:
            portal_to_use = get_current_active_portal()
        self._visit_portal(portal_to_use)
        return portal_to_use


    def _visit_portal(self, portal: BasicPortal) -> None:
        """Visit a portal and register the object if this is the first visit.

        Checks if the object has previously visited the specified portal.
        If this is the first visit, registers the object with that portal.

        Args:
            portal: The BasicPortal instance to visit.
        """
        if portal._str_id not in self._visited_portals:
            self._first_visit_to_portal(portal)


    def _first_visit_to_portal(self, portal: BasicPortal) -> None:
        """Register an object in a portal that the object has not seen before."""
        if portal._str_id in self._visited_portals:
            raise RuntimeError(
                f"Object with id {self._str_id} has already been visited "
                "and registered in portal {portal._str_id}")
        _PORTAL_REGISTRY.register_object(self)
        self._visited_portals.add(portal._str_id)


    @property
    def _str_id(self) -> PAwareObjectStrID:
        """Return the hash ID of the portal-aware object.

        It's an internal hash used by Pythagoras and is different from .__hash__()
        """
        if not self._init_finished:
            raise RuntimeError("Object is not fully initialized yet, "
                               "_str_id is not available.")
        if not hasattr(self, "_str_id_cache"):
            self._str_id_cache = PAwareObjectStrID(get_hash_signature(self))
        return self._str_id_cache


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

        Restores the object's state from unpickling and resets portal-related
        attributes to ensure proper initialization in the new environment.

        Args:
            state: The state dictionary used for unpickling the object.
        """
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
        if len(self._visited_portals) >=1:
            if not _PORTAL_REGISTRY.is_object_registered(self):
                raise RuntimeError(f"Object with id {self._str_id} is expected to be in the activated objects registry")
            return True
        return False


    def _deactivate(self):
        """Mark the object as not activated.

        Empty the list of portals it has been registered into.
        """
        _ensure_single_thread()
        if not self.is_activated:
            raise RuntimeError(f"Object with id {self._str_id} is not activated")

        self._invalidate_cache()
        self._visited_portals = set()


def _clear_all_portals() -> None:
    """Remove all information about all the portals from the system."""
    
    for obj in list(_PORTAL_REGISTRY.known_objects.values()):
        obj._deactivate()

    for portal in _PORTAL_REGISTRY.known_portals.values():
        portal._clear()
    
    _PORTAL_REGISTRY.clear()
    _reset_single_thread_enforcer()


PortalType = TypeVar("PortalType")


##################################################


def get_number_of_known_portals() -> int:
    """Get the number of portals currently in the system.

    Returns:
        The total count of all known portals in the system.
    """
    return _PORTAL_REGISTRY.count_known_portals()


def get_all_known_portals() -> list[BasicPortal]:
    """Get a list of all known portals.

    Returns:
        A list containing all portal instances currently known to the system.
    """
    return _PORTAL_REGISTRY.all_portals()


def get_number_of_portals_in_active_stack() -> int:
    """Get the number of unique portals in the active stack.

    Returns:
        The count of unique portals currently in the active portal stack.
    """
    return _PORTAL_REGISTRY.unique_active_portals_count()


def get_depth_of_active_portal_stack() -> int:
    """Get the depth of the active portal stack.

    Returns:
        The total depth (sum of all counters) of the active portal stack.
    """
    return _PORTAL_REGISTRY.active_portals_stack_depth()


def get_most_recently_created_portal() -> BasicPortal | None:
    """Get the most recently created portal.

    Returns:
        The most recently created portal instance, or None if no portals exist.
    """
    return _PORTAL_REGISTRY.most_recently_created_portal


def _set_default_portal_instantiator(instantiator: Callable[[], None]) -> None:
    """Register a callable that creates (and usually enters) the default portal.

    The callable is executed lazily the first time ``get_current_active_portal()`` is
    invoked while no portals exist.  It must:

    1. Accept **no arguments**.
    2. Create a portal instance.
    3. Optionally call ``__enter__`` on that instance (typical for a global
       default).
    4. Return **None**.

    Parameters
    ----------
    instantiator : Callable[[], None]
        Zero-argument function that establishes the default portal.

    Raises
    ------
    TypeError
        If *instantiator* is not callable.
    RuntimeError
        If a default instantiator has already been registered.
    """
    _PORTAL_REGISTRY.register_default_portal_instantiator(instantiator)


def get_current_active_portal() -> BasicPortal:
    """Get the current active portal object.

    The current active portal is the one that was most recently entered
    using the 'with' statement. If no portal is currently active,
    it finds the most recently created portal and makes it active (and current).
    If there are currently no portals exist in the system,
    it creates and the default portal, makes it active an current.

    Returns:
        The current active portal.
    """
    return _PORTAL_REGISTRY.current_active_portal()


def get_nonactive_portals() -> list[BasicPortal]:
    """Get a list of all portals that are not in the active stack.

    Returns:
        A list of portal instances that are not currently in the active portal stack.
    """
    _ensure_single_thread()
    active_ids = {p._str_id for p in _PORTAL_REGISTRY.active_portals_stack}
    return [
        p for p in _PORTAL_REGISTRY.known_portals.values()
        if p._str_id not in active_ids
    ]


def get_number_of_linked_portal_aware_objects() -> int:
    """Get the number of portal-aware objects currently linked to portals."""
    return _PORTAL_REGISTRY.count_linked_objects()


def _visit_portal(obj:Any, portal:BasicPortal) -> None:
    """Register all PortalAwareClass instances nested within `obj` with `portal`."""
    return _visit_portal_impl(obj, portal=portal)


def _visit_portal_impl(obj:Any, portal:BasicPortal, seen=None)->None:
    """Recursively traverse `obj` and register any PortalAwareClass instances found."""
    _ensure_single_thread()

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