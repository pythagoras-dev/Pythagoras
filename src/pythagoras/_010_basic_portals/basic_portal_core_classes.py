"""This module provides foundational functionality for work with portals.

The module specifically handles portal stack management and provides
access to the current portal. It keeps track of all portals
created in the system and managem the stack of entered ('active') portals.
It also provides a way to clear all portals and their state.
"""

from __future__ import annotations

import random
from abc import abstractmethod
from functools import cached_property
from importlib import metadata
from typing import TypeVar, Any, NewType, Callable, Mapping, Iterable
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
MAX_NESTED_PORTALS = 999


PortalStrFingerprint = NewType("PortalStrFingerprint", str)
PAwareObjectStrFingerprint = NewType("PAwareObjectStrFingerprint", str)


class BasicPortal(NotPicklableClass, ParameterizableClass, metaclass = GuardedInitMeta):
    """A base class for portal objects that enable access to 'outside' world.

    In a Pythagoras-based application, a portal is the application's 'window'
    into the non-ephemeral world outside the current application execution
    session. It's a connector that enables a link between runtime-only
    ephemeral state and a persistent state that can be saved and loaded
    across multiple runs of the application, and across multiple computers.

    A Pythagoras-based application can have multiple portals,
    and there is usually a current active one, accessible via
    get_current_portal().

    BasicPortal is a base class for all portal objects.

    The class is not intended to be used directly. Instead, it should
    be subclassed to provide additional functionality.
    """

    _entropy_infuser: random.Random | None

    _root_dict: PersiDict | None
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
            # If no root_dict provided, default to the standard local directory.
            root_dict = get_default_portal_base_dir()
        if not isinstance(root_dict, PersiDict):
            root_dict = str(root_dict)
            root_dict = FileDirDict(base_dir = root_dict)
        root_dict_params = root_dict.get_params()
        root_dict_params.update(digest_len=0)
        root_dict = type(root_dict)(**root_dict_params)
        self._root_dict = root_dict


    def __post_init__(self) -> None:
        """Execute post-initialization tasks for the portal.

        This method is automatically called after all __init__() methods are
        complete. It registers the portal in the global registry and updates
        the most recently created portal reference.
        """
        _PORTAL_REGISTRY.register_portal(self)


    def _get_linked_objects_ids(self
            , target_class: type | None = None) -> set[PAwareObjectStrFingerprint]:
        """Get the set of string IDs of objects linked to this portal.

        Args:
            target_class: The class type to filter for, or None to include
                all linked objects regardless of type.

        Returns:
            A set of string IDs representing objects linked to this portal,
            optionally filtered by the specified target class.
        """
        return _PORTAL_REGISTRY.linked_objects_fingerprints(self, target_class)


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
        """Get the random number generator associated with this portal.

        Returns:
            A Random instance used for generating random values and entropy
            within this portal's context.
        """
        if self._entropy_infuser is None:
            raise RuntimeError("Entropy infuser is None. "
                               "Most probably, it was cleared by calling portal._clear(). "
                               "You can't use a portal after calling portal._clear().")

        return self._entropy_infuser


    @property
    def is_current(self) -> bool:
        """Check if the portal is the current one.

        The 'current active' portal is the innermost portal
        in the stack of portal's 'with' statements.
        """
        return _PORTAL_REGISTRY.is_current_portal(self)
    
    @property
    def is_active(self) -> bool:
        """Check if the portal is currently active.
        A portal is considered 'active' if it is present
        in the stack of portal's 'with' statements.
        """
        active_fingerprints = {p.fingerprint for p
                               in _PORTAL_REGISTRY.active_portals_stack}
        return self.fingerprint in active_fingerprints


    def get_params(self) -> dict[str,Any]:
        """Get the portal's configuration parameters."""
        params = dict(root_dict=self._root_dict)
        sorted_params = sort_dict_by_keys(params)
        return sorted_params


    @cached_property
    def fingerprint(self) -> PortalStrFingerprint:
        """Get the portal's persistent hash fingerprint.

        It's an internal hash used by Pythagoras and is different from .__hash__()

        This property should only be accessed after the portal has been fully initialized.
        """
        if not self._init_finished:
            raise RuntimeError("Portal is not fully initialized yet, "
                               "fingerprint is not available.")
        return PortalStrFingerprint(get_hash_signature(self.get_essential_jsparams()))


    def _invalidate_cache(self) -> None:
        """Invalidate the portal's attribute cache.

        If the portal's attribute named ATTR is cached,
        its cached value will be stored in an attribute named _ATTR_cache
        This method should delete all such attributes.
        """
        pass


    def describe(self) -> pd.DataFrame:
        """Get a DataFrame describing the portal's current state."""
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
        """Set the portal as the current one and add it to the active stack.

        Returns:
            The portal instance itself (self).
        """
        _PORTAL_REGISTRY.push_new_active_portal(self)
        return self


    def __exit__(self, exc_type, exc_val, exc_tb):
        """Pop the portal from the stack of active ones.

        Args:
            exc_type: Exception type if an exception occurred, None otherwise.
            exc_val: Exception value if an exception occurred, None otherwise.
            exc_tb: Exception traceback if an exception occurred, None otherwise.
        """
        _ensure_single_thread()
        _PORTAL_REGISTRY.pop_active_portal(self)


    def _clear(self) -> None:
        """Clear and invalidate the portal's state.

        The portal must not be used after this method is called.
        """
        if not self._init_finished:
            return  # Already cleared or never initialized

        _PORTAL_REGISTRY.unregister_portal(self)

        self._invalidate_cache()
        self._root_dict = None
        self._entropy_infuser = None
        self._init_finished = False


PortalType = TypeVar("PortalType", bound=BasicPortal)

def _validate_required_portal_type(required_portal_type: PortalType) -> None:
    if not (isinstance(required_portal_type, type) and issubclass(required_portal_type, BasicPortal)):
        raise TypeError(
            "required_portal_type must be BasicPortal or one of its (grand)children")

class _PortalRegistry(NotPicklableClass):
    """
    A container for every piece of mutable “portal bookkeeping”
    needed by Pythagoras. It maintains the current state of Pythagoras.

    Stored data
    -----------
    known_portals : dict[PortalStrFingerprint, BasicPortal]
        All portals that have been instantiated in the system.
    active_portals_stack : list[BasicPortal]
        Stack that mirrors nested ``with portal:`` blocks.
    active_portals_stack_counters : list[int]
        Re-entrancy counters that align one-to-one with *active_portals_stack*.
    most_recently_created : BasicPortal | None
        Last portal created in the system.
    links_obj2portal : dict[PAwareObjectStrFingerprint, PortalStrFingerprint]
        Mapping from object identifier to the str-id of its linked portal.
    activated_objects : dict[PAwareObjectStrFingerprint, PortalAwareClass]
        Reverse lookup from object identifier to the actual object instance.
    default_portal_instantiator : Callable[[], None] | None
        A callable that creates a default portal when none exists.
    """

    def __init__(self) -> None:
        _ensure_single_thread()
        self.known_portals: dict[PortalStrFingerprint, BasicPortal] = {}
        self.active_portals_stack: list[BasicPortal] = []
        self.active_portals_stack_counters: list[int] = []
        self.most_recently_created_portal: BasicPortal | None = None
        self.links_from_objects_to_portals: dict[PAwareObjectStrFingerprint, PortalStrFingerprint] = {}
        self.known_objects: dict[PAwareObjectStrFingerprint, PortalAwareClass] = {}
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
        self.known_portals[portal.fingerprint] = portal
        self.most_recently_created_portal = portal

    def unregister_portal(self, portal: BasicPortal) -> None:
        """Remove *portal* from the registry and reset any objects linked to it."""
        portal_id_to_remove = portal.fingerprint
        all_links = list(self.links_from_objects_to_portals.items())
        for obj_id, portal_id in all_links:
            if portal_id == portal_id_to_remove:
                obj = self.known_objects[obj_id]
                obj._clear()

        self.known_portals.pop(portal.fingerprint, None)
        if self.most_recently_created_portal is portal:
            self.most_recently_created_portal = None

    def count_known_portals(self, required_portal_type: type[PortalType] = BasicPortal) -> int:
        """Get the number of portals registered in the system.

        Args:
            required_portal_type: Class to validate portals. Default is BasicPortal.
                If any known portal is not an instance of this class (or subclass),
                a TypeError is raised.

        Returns:
            The total count of all known portals in the system.

        Raises:
            TypeError: If any known portal is not an instance of required_portal_type.
        """
        return len(self.all_portals(required_portal_type))

    def all_portals(self, required_portal_type: type[PortalType] = BasicPortal) -> list[PortalType]:
        """Get a list of all portals registered in the system.

        Args:
            required_portal_type: Class to validate portals. Default is BasicPortal.
                If any known portal is not an instance of this class (or subclass),
                a TypeError is raised.

        Returns:
            A list containing all portal instances currently known to the system.

        Raises:
            TypeError: If any known portal is not an instance of required_portal_type.
        """
        _validate_required_portal_type(required_portal_type)
        candidates = list(self.known_portals.values())
        for p in candidates:
            if not isinstance(p, required_portal_type):
                raise TypeError(
                    f"Found portal {type(p).__name__} which is not "
                    f"an instance of required {required_portal_type.__name__}")
        return candidates

    def push_new_active_portal(self, portal: BasicPortal) -> None:
        """Put *portal* on top of the active-stack, handling re-entrancy."""
        _ensure_single_thread()
        if self.active_portals_stack_depth() >= MAX_NESTED_PORTALS:
            raise RuntimeError(f"Too many nested portals: {MAX_NESTED_PORTALS}")
        if not portal.fingerprint in self.known_portals:
            raise RuntimeError(f"Attempt to push an unregistered portal onto the stack")
        if self.active_portals_stack and self.active_portals_stack[-1] is portal:
            self.active_portals_stack_counters[-1] += 1
        else:
            self.active_portals_stack.append(portal)
            self.active_portals_stack_counters.append(1)

        if len(self.active_portals_stack) != len(self.active_portals_stack_counters):
            raise RuntimeError("Internal error: active_stack and active_counters are out of sync")

    def pop_active_portal(self, portal: BasicPortal) -> None:
        """Remove the current active portal, keeping the stack consistent.

        Raises:
            RuntimeError: If *portal* is not the current top of the stack.
        """
        _ensure_single_thread()
        if not portal.fingerprint in self.known_portals:
            raise RuntimeError(f"Attempt to pop an unregistered portal from the stack")

        if not self.active_portals_stack or self.active_portals_stack[-1] is not portal:
            raise RuntimeError("Attempt to pop an unexpected portal from the stack")

        if self.active_portals_stack_counters[-1] == 1:
            self.active_portals_stack.pop()
            self.active_portals_stack_counters.pop()
        else:
            self.active_portals_stack_counters[-1] -= 1

        if len(self.active_portals_stack) != len(self.active_portals_stack_counters):
            raise RuntimeError("Internal error: active_portals_stack and active_portals_stack_counters are out of sync")


    def current_portal(self) -> BasicPortal:
        """Get the current portal object.

        The current portal is the one that was most recently entered
        using the 'with' statement. If no portal was entered yet,
        it finds the most recently created portal and makes it current.
        If no portals exist in the system, it creates and returns
        the default portal.

        Returns:
            The current portal instance.
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

    def is_current_portal(self, portal: BasicPortal) -> bool:
        """Check if *portal* is the current one."""
        return (len(self.active_portals_stack) > 0
                and self.active_portals_stack[-1].fingerprint == portal.fingerprint)

    def unique_active_portals_count(self, required_portal_type: type[PortalType] = BasicPortal) -> int:
        """Count unique portals currently in the active stack.

        Args:
            required_portal_type: Class to validate portals. Default is BasicPortal.
                If any active portal is not an instance of this class (or subclass),
                a TypeError is raised.

        Returns:
            The count of unique portals currently in the active portal stack.

        Raises:
            TypeError: If any active portal is not an instance of required_portal_type.
        """
        _validate_required_portal_type(required_portal_type)
        unique_active = {p for p in self.active_portals_stack}
        for p in unique_active:
            if not isinstance(p, required_portal_type):
                raise TypeError(
                    f"Found active portal {type(p).__name__} which is not "
                    f"an instance of required {required_portal_type.__name__}")
        return len(unique_active)

    def active_portals_stack_depth(self, required_portal_type: type[PortalType] = BasicPortal) -> int:
        """Calculate the total depth of the active portal stack.

        Args:
            required_portal_type: Class to validate portals. Default is BasicPortal.
                If any active portal is not an instance of this class (or subclass),
                a TypeError is raised.

        Returns:
            The total depth (sum of all counters) of the active portal stack.

        Raises:
            TypeError: If any active portal is not an instance of required_portal_type.
        """
        _validate_required_portal_type(required_portal_type)
        
        total_depth = 0
        for portal, count in zip(self.active_portals_stack, self.active_portals_stack_counters):
            if not isinstance(portal, required_portal_type):
                raise TypeError(
                    f"Found active portal {type(portal).__name__} which is not "
                    f"an instance of required {required_portal_type.__name__}")
            total_depth += count
        return total_depth

    def nonactive_portals(self, required_portal_type: type[PortalType] = BasicPortal) -> list[BasicPortal]:
        """Get a list of all portals that are not in the active stack.

        Args:
            required_portal_type: Class to validate portals. Default is BasicPortal.
                If any non-active portal is not an instance of this class (or subclass),
                a TypeError is raised.

        Returns:
            A list of portal instances that are not currently in the active portal stack.

        Raises:
            TypeError: If any non-active portal is not an instance of required_portal_type.
        """
        _validate_required_portal_type(required_portal_type)
        active_ids = {p.fingerprint for p in self.active_portals_stack}
        all_known = self.all_portals(BasicPortal)

        candidates = [
            p for p in all_known
            if p.fingerprint not in active_ids
        ]

        for p in candidates:
            if not isinstance(p, required_portal_type):
                raise TypeError(
                    f"Found non-active portal {type(p).__name__} which is not "
                    f"an instance of required {required_portal_type.__name__}")

        return candidates

    def noncurrent_portals(self, required_portal_type: type[PortalType] = BasicPortal) -> list[BasicPortal]:
        """Get a list of all known portals that are not the current portal.

        The current portal is the one at the top of the active stack.
        If the stack is empty, all known portals are returned.

        Args:
            required_portal_type: Class to validate portals. Default is BasicPortal.
                If any non-current portal is not an instance of this class (or subclass),
                a TypeError is raised.

        Returns:
            A list of all known portal instances but the current one.

        Raises:
            TypeError: If any non-current portal is not an instance of required_portal_type.
        """
        _validate_required_portal_type(required_portal_type)
        current_id = None
        if len(self.active_portals_stack) > 0:
            current_id = self.active_portals_stack[-1].fingerprint

        all_known = self.all_portals(BasicPortal)
        candidates = [p for p in all_known if p.fingerprint != current_id]

        for p in candidates:
            if not isinstance(p, required_portal_type):
                raise TypeError(
                    f"Found non-current portal {type(p).__name__} which is not "
                    f"an instance of required {required_portal_type.__name__}")

        return candidates

    def register_object(self, obj: PortalAwareClass) -> None:
        """Register an object in the global registry."""
        self.known_objects[obj.fingerprint] = obj

    def is_object_registered(self, obj: PortalAwareClass) -> bool:
        """Check if an object is currently registered."""
        return obj.fingerprint in self.known_objects

    def register_linked_object(self, portal: BasicPortal, obj:PortalAwareClass) -> None:
        """Record that *obj* (identified by *obj_id*) is linked to *portal*.

        An object being linked to a portal means that it will use that portal
        for all its operations unless explicitly told otherwise.
        """
        obj_id = obj.fingerprint
        portal_id = portal.fingerprint
        self.known_objects[obj_id] = obj
        self.links_from_objects_to_portals[obj_id] = portal_id


    def unregister_object(self,obj:PortalAwareClass) -> None:
        """Unregister an object from the registry."""
        obj_id = obj.fingerprint
        self.known_objects.pop(obj_id, None)
        self.links_from_objects_to_portals.pop(obj_id, None)


    def count_linked_objects(self) -> int:
        """Count the number of objects linked to portals."""
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


    def linked_objects_fingerprints(self
            , portal: BasicPortal
            , target_class: type | None = None
            ) -> set[PAwareObjectStrFingerprint]:
        """Get IDs of objects linked to the specified portal, optionally filtered by class."""
        obj_ids = (o for o, p in self.links_from_objects_to_portals.items() if p == portal.fingerprint)

        if target_class is None:
            return set(obj_ids)

        result = set()
        for obj_id in obj_ids:
            if isinstance(self.known_objects[obj_id], target_class):
                result.add(obj_id)
        return result

    def linked_objects(self
            , portal: BasicPortal
            , target_class: type | None = None
            ) -> list[PortalAwareClass]:
        """Get objects linked to the specified portal, optionally filtered by class."""
        obj_ids = self.linked_objects_fingerprints(portal, target_class)
        result = []
        for obj_id in obj_ids:
            obj = self.known_objects.get(obj_id)
            result.append(obj)
        return result


# Singleton instance used by the rest of the module
_PORTAL_REGISTRY = _PortalRegistry()


class PortalAwareClass(metaclass = GuardedInitMeta):
    """A base class for objects that need to access a portal.

    These objects either always work with a current portal,
    or they have a preferred (linked) portal which they activate every
    time their methods are called.
    """

    _linked_portal_at_init: BasicPortal|None
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
        self._visited_portals = set()


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
        """Get the object's preferred (linked) portal.

        If the linked portal is not None, the object will activate
        this portal every time the object's methods are called.
        If it's None, the object will never try to change the active portal.
        """

        linked_portal =  self._linked_portal_at_init
        if linked_portal is not None:
            self._visit_portal(linked_portal)
        return linked_portal


    @property
    def portal(self) -> BasicPortal:
        """Get the portal which the object's methods will be using.

        It's either the object's linked portal or
        (if the linked portal is None) the currently active portal.
        """
        portal_to_use = self._linked_portal
        if portal_to_use is None:
            portal_to_use = _PORTAL_REGISTRY.current_portal()
        self._visit_portal(portal_to_use)
        return portal_to_use


    def _visit_portal(self, portal: BasicPortal) -> None:
        """Visit a portal and register the object if this is the first visit.

        Checks if the object has previously visited the specified portal.
        If this is the first visit, registers the object with that portal.

        Args:
            portal: The BasicPortal instance to visit.
        """
        if portal.fingerprint not in self._visited_portals:
            self._first_visit_to_portal(portal)


    def _first_visit_to_portal(self, portal: BasicPortal) -> None:
        """Mark the portal as visited and ensure the object is registered in the global registry."""
        if not self._init_finished:
            raise RuntimeError("Object is not fully initialized yet, "
                               "_first_visit_to_portal() can't be called.")
        if portal.fingerprint in self._visited_portals:
            raise RuntimeError(
                f"Object with id {self.fingerprint} has already been visited "
                f"and registered in portal {portal.fingerprint}")

        self._visited_portals.add(portal.fingerprint)

        if self._linked_portal_at_init is not None:
            _PORTAL_REGISTRY.register_linked_object(
                self._linked_portal_at_init, self)
        else:
            _PORTAL_REGISTRY.register_object(self)


    @cached_property
    def fingerprint(self) -> PAwareObjectStrFingerprint:
        """Return the hash fingerprint of the portal-aware object.

        It's an internal hash used by Pythagoras and is different from .__hash__()

        This property should only be accessed after the portal has been fully initialized.
        """
        if not self._init_finished:
            raise RuntimeError("Object is not fully initialized yet, "
                               "fingerprint is not available.")
        return PAwareObjectStrFingerprint(get_hash_signature(self))


    @abstractmethod
    def __getstate__(self):
        """Prepare the object's state for pickling.

        This method must be overridden in subclasses to ensure that portal
        information is NOT included in the pickled state.
        """
        raise NotImplementedError(
            "PortalAwareClass objects are not picklable. "
            "Method __getstate__() must be overridden in subclasses.")


    @abstractmethod
    def __setstate__(self, state: dict[str, Any]):
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
        its cached value will be stored in an attribute named _ATTR_cache.
        This method should delete all such attributes.
        """
        pass


    @property
    def is_registered(self) -> bool:
        """Return True if the object has been registered in at least one of the portals."""
        if len(self._visited_portals) >=1:
            if not _PORTAL_REGISTRY.is_object_registered(self):
                raise RuntimeError(f"Object with id {self.fingerprint} is expected to be in the activated objects registry")
            return True
        return False


    def _clear(self):
        """Mark the object as not registered.

        Empty the list of portals it has been registered into.
        """
        if not self._init_finished:
            return  # Already cleared or never initialized
        _PORTAL_REGISTRY.unregister_object(self)
        self._invalidate_cache()
        self._visited_portals = set()
        self._init_finished = False


def _clear_all_portals() -> None:
    """Remove all information about all the portals from the system."""

    # Take snapshots before clearing to avoid iteration issues
    objects_to_clear = list(_PORTAL_REGISTRY.known_objects.values())
    portals_to_clear = _PORTAL_REGISTRY.all_portals()

    # Clean up objects first (while registry is still intact)
    for obj in objects_to_clear:
        obj._clear()

    for portal in portals_to_clear:
        portal._clear()

    # Clear remaining registry state (should be mostly empty now)
    _PORTAL_REGISTRY.clear()

    _reset_single_thread_enforcer()


PortalType = TypeVar("PortalType")


##################################################




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

    Args:
        instantiator: Zero-argument function that establishes the default portal.

    Raises:
        TypeError: If *instantiator* is not callable.
        RuntimeError: If a default instantiator has already been registered.
    """
    _PORTAL_REGISTRY.register_default_portal_instantiator(instantiator)




def get_number_of_linked_portal_aware_objects() -> int:
    """Get the number of portal-aware objects currently linked to portals."""
    return _PORTAL_REGISTRY.count_linked_objects()


def _visit_portal(obj:Any, portal:BasicPortal) -> None:
    """Register all PortalAwareClass instances nested within `obj` with `portal`.

    Args:
        obj: The object structure to traverse (can be nested).
        portal: The portal to register found objects with.
    """
    return _visit_portal_impl(obj, portal=portal)


def _visit_portal_impl(obj: Any, portal: BasicPortal, seen: set[int] | None = None) -> None:
    """Recursively traverse `obj` and register any PortalAwareClass instances found.

    Args:
        obj: The object to check.
        portal: The portal to register with.
        seen: A set of object IDs already visited (to handle cycles).
    """
    _ensure_single_thread()

    if seen is None:
        seen = set()

    if id(obj) in seen:
        return

    # Treat strings, bytes, and other specific types as leaf nodes
    if isinstance(obj, (str, range, bytearray, bytes, SafeStrTuple)):
        return

    seen.add(id(obj))

    if isinstance(obj, PortalAwareClass):
        obj._visit_portal(portal)
        return

    # Handle Mappings (dictionaries, etc.) by visiting both keys and values
    if isinstance(obj, Mapping):
        for key, value in obj.items():
            _visit_portal_impl(key, portal, seen)
            _visit_portal_impl(value, portal, seen)
        return

    # Handle generic Iterables (lists, tuples, sets, etc.)
    if isinstance(obj, Iterable):
        for item in obj:
            _visit_portal_impl(item, portal, seen)
        return
