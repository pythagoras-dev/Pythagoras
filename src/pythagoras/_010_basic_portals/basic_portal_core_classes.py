"""Core classes and registry for Pythagoras portal management.

This module provides foundational functionality for working with portals,
including portal stack management and access to the current portal. It tracks
all portals created in the system and manages the stack of entered ('active')
portals. It also provides mechanisms to clear all portals and their state.
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
from .single_thread_enforcer import ensure_single_thread, _reset_single_thread_enforcer
from .._000_supporting_utilities import get_hash_signature
from .portal_description_helpers import (
    _describe_persistent_characteristic,
    _describe_runtime_characteristic)
from .default_portal_base_dir import get_default_portal_base_dir
from .._000_supporting_utilities.cacheable_properties_mixin import CacheablePropertiesMixin

_BASE_DIRECTORY_TXT = "Base directory"
_BACKEND_TYPE_TXT = "Backend type"
_PYTHAGORAS_VERSION_TXT = "Pythagoras version"
MAX_NESTED_PORTALS = 999


PortalStrFingerprint = NewType("PortalStrFingerprint", str)
PAwareObjectStrFingerprint = NewType("PAwareObjectStrFingerprint", str)


class BasicPortal(NotPicklableClass, ParameterizableClass, CacheablePropertiesMixin, metaclass = GuardedInitMeta):
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

        Args:
            root_dict: Root dictionary for persistent storage, path to storage location,
                or None for default location.
        """
        ensure_single_thread()
        self._init_finished = False
        self._entropy_infuser = random.Random()
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


    def __post_init__(self) -> None:
        """Execute post-initialization tasks for the portal.

        This method is automatically called after all __init__() methods
        complete.
        """
        _PORTAL_REGISTRY.register_portal(self)


    def _get_linked_objects_ids(self
            , target_class: type | None = None) -> set[PAwareObjectStrFingerprint]:
        """Get the set of IDs of objects linked to this portal.

        Args:
            target_class: Optional class type filter.

        Returns:
            IDs of objects linked to this portal, filtered by target_class if provided.
        """
        return _PORTAL_REGISTRY.linked_objects_fingerprints(self, target_class)


    def get_linked_objects(self, target_class: type | None = None) -> list[PortalAwareClass]:
        """Get the list of objects linked to this portal.

        Args:
            target_class: Optional class type filter.

        Returns:
            PortalAwareClass instances linked to this portal, filtered by target_class if provided.
        """
        return _PORTAL_REGISTRY.linked_objects(self, target_class)


    def get_number_of_linked_objects(self, target_class: type | None = None) -> int:
        """Get the number of objects linked to this portal.

        Args:
            target_class: Optional class type filter.

        Returns:
            Count of portal-aware objects linked to this portal, filtered by target_class if provided.
        """
        return len(self._get_linked_objects_ids(target_class))


    @property
    def entropy_infuser(self) -> random.Random:
        """The random number generator associated with this portal."""
        if self._entropy_infuser is None:
            raise RuntimeError("Entropy infuser is None. "
                               "Most probably, it was cleared by calling portal._clear(). "
                               "You can't use a portal after calling portal._clear().")

        return self._entropy_infuser


    @property
    def is_current(self) -> bool:
        """True if the portal is the innermost portal in the active stack."""
        return _PORTAL_REGISTRY.is_current_portal(self)

    @property
    def is_active(self) -> bool:
        """True if the portal is in the active portal stack."""
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
        """The portal's persistent hash fingerprint.

        This is an internal identifier used by Pythagoras to uniquely identify
        portals in the registry. It differs from __hash__() and is based on
        the portal's essential parameters.
        """
        if not self._init_finished:
            raise RuntimeError("Portal is not fully initialized yet, "
                               "fingerprint is not available.")
        return PortalStrFingerprint(get_hash_signature(self.get_essential_jsparams()))


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
        """Add the portal to the active stack and set it as the current one.

        Returns:
            The portal instance itself.
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
        ensure_single_thread()
        _PORTAL_REGISTRY.pop_active_portal(self)


    def _clear(self) -> None:
        """Clear and invalidate the portal's state.

        The portal must not be used after calling this method.
        """
        if not self._init_finished:
            return

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
    """Registry maintaining all portal bookkeeping and state for Pythagoras.

    This singleton tracks all portals and portal-aware objects, manages the stack
    of active portals, and provides mechanisms for portal lookup and lifecycle management.

    Attributes:
        known_portals: Maps portal fingerprints to portal instances.
        active_portals_stack: Stack of currently active portals (nested `with` statements).
        active_portals_stack_counters: Re-entrancy counters for each stack level.
        most_recently_created_portal: Last portal instantiated, used for auto-activation.
        links_from_objects_to_portals: Maps object fingerprints to their linked portal fingerprints.
        known_objects: Maps object fingerprints to PortalAwareClass instances.
        default_portal_instantiator: Factory function for creating the default portal.
    """

    def __init__(self) -> None:
        ensure_single_thread()
        self.known_portals: dict[PortalStrFingerprint, BasicPortal] = {}
        self.active_portals_stack: list[BasicPortal] = []
        self.active_portals_stack_counters: list[int] = []
        self.most_recently_created_portal: BasicPortal | None = None
        self.links_from_objects_to_portals: dict[PAwareObjectStrFingerprint, PortalStrFingerprint] = {}
        self.known_objects: dict[PAwareObjectStrFingerprint, PortalAwareClass] = {}
        self.default_portal_instantiator: Callable[[], None] | None = None



    def register_default_portal_instantiator(self, instantiator: Callable[[], None]) -> None:
        """Register a callable that creates the default portal.

        Args:
            instantiator: Factory function that creates the default portal.

        Raises:
            TypeError: If instantiator is not callable.
            RuntimeError: If a default portal instantiator is already registered.
        """
        ensure_single_thread()
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
        """Add the portal to the registry and mark it as most recently created.

        Args:
            portal: The portal instance to register.
        """
        ensure_single_thread()
        self.known_portals[portal.fingerprint] = portal
        self.most_recently_created_portal = portal


    def get_portal_by_fingerprint(self, portal_fingerprint: PortalStrFingerprint, required_portal_type: type[PortalType] = BasicPortal) -> BasicPortal:
        """Get a portal by its fingerprint.

        Args:
            portal_fingerprint: Portal fingerprint to look up.
            required_portal_type: Expected portal type for validation.

        Returns:
            The portal instance matching the fingerprint.

        Raises:
            TypeError: If portal_fingerprint is not a string or portal type mismatches.
            KeyError: If no portal with the given fingerprint exists.
        """
        _validate_required_portal_type(required_portal_type)
        if not isinstance(portal_fingerprint, str):
            raise TypeError(f"Expected PortalStrFingerprint(str), got {type(portal_fingerprint)}")
        if portal_fingerprint not in self.known_portals:
            raise KeyError(f"Portal with fingerprint {portal_fingerprint} not found")
        portal = self.known_portals[portal_fingerprint]
        if not isinstance(portal, required_portal_type):
            raise TypeError(
                f"Found portal {type(portal).__name__} which is not "
                f"an instance of required {required_portal_type.__name__}")
        return portal


    def unregister_portal(self, portal: BasicPortal) -> None:
        """Remove the portal from the registry and try to clear linked objects.

        Args:
            portal: The portal instance to unregister.
        """
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
            required_portal_type: Expected portal type for validation.

        Returns:
            The total count of all known portals in the system.

        Raises:
            TypeError: If any known portal is not an instance of required_portal_type.
        """
        return len(self.all_portals(required_portal_type))

    def all_portals(self, required_portal_type: type[PortalType] = BasicPortal) -> list[PortalType]:
        """Get a list of all portals registered in the system.

        Args:
            required_portal_type: Expected portal type for validation.

        Returns:
            All portal instances currently known to the system.

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

    def all_portal_fingerprints(self, required_portal_type: type[PortalType] = BasicPortal) -> set[PortalStrFingerprint]:
        """Get a set of all portal fingerprints.

        Args:
            required_portal_type: Expected portal type for validation.

        Returns:
            Fingerprints of all portals currently known to the system.

        Raises:
            TypeError: If any known portal is not an instance of required_portal_type.
        """
        _validate_required_portal_type(required_portal_type)
        candidates = set(self.known_portals.keys())
        for fingerprint in candidates:
            portal = self.known_portals[fingerprint]
            if not isinstance(portal, required_portal_type):
                raise TypeError(
                    f"Found portal {type(portal).__name__} which is not "
                    f"an instance of required {required_portal_type.__name__}")
        return candidates

    def push_new_active_portal(self, portal: BasicPortal) -> None:
        """Push the portal onto the active stack, handling re-entrancy.

        Args:
            portal: The portal instance to push.

        Raises:
            RuntimeError: If nesting exceeds MAX_NESTED_PORTALS or portal is unregistered.
        """
        ensure_single_thread()
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
        """Pop the portal from the active stack, maintaining consistency.

        Args:
            portal: The portal instance to pop.

        Raises:
            RuntimeError: If the portal is unregistered or not at the top of the stack.
        """
        ensure_single_thread()
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

        Returns the top portal from the active stack, or activates the most recently
        created portal if the stack is empty. Creates the default portal if none exist.

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
        """Check if the portal is at the top of the active stack.

        Args:
            portal: The portal instance to check.

        Returns:
            True if the portal is current (top of stack), False otherwise.
        """
        return (len(self.active_portals_stack) > 0
                and self.active_portals_stack[-1].fingerprint == portal.fingerprint)


    def unique_active_portals_count(self, required_portal_type: type[PortalType] = BasicPortal) -> int:
        """Count unique portals currently in the active stack.

        Args:
            required_portal_type: Expected portal type for validation.

        Returns:
            The count of unique portals currently in the active portal stack.

        Raises:
            TypeError: If any active portal is not an instance of required_portal_type.
        """
        _validate_required_portal_type(required_portal_type)
        unique_active = {p for p in self.active_portals_stack}
        for p in unique_active:
            if not isinstance(p, required_portal_type):
                raise TypeError( f"Found active portal {type(p).__name__} which is not "
                    f"an instance of required {required_portal_type.__name__}")
        return len(unique_active)


    def active_portals_stack_depth(self,
            required_portal_type: type[PortalType] = BasicPortal
            ) -> int:
        """Calculate the total depth of the active portal stack.

        Args:
            required_portal_type: Expected portal type for validation.

        Returns:
            The total depth (sum of all re-entrancy counters) of the active portal stack.

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

        candidates = [p for p in all_known
            if p.fingerprint not in active_ids]

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
        """Register a portal-aware object in the global registry.

        Args:
            obj: The object instance to register.
        """
        self.known_objects[obj.fingerprint] = obj

    def is_object_registered(self, obj: PortalAwareClass) -> bool:
        """Check if an object is currently registered.

        Args:
            obj: The object instance to check.

        Returns:
            True if the object is registered, False otherwise.
        """
        return obj.fingerprint in self.known_objects

    def register_linked_object(self, portal: BasicPortal, obj:PortalAwareClass) -> None:
        """Link an object to a portal in the registry.

        The linked object will use the portal for all its operations
        unless explicitly configured otherwise.

        Args:
            portal: The portal to link the object to.
            obj: The portal-aware object to link.
        """
        obj_id = obj.fingerprint
        portal_id = portal.fingerprint
        self.known_objects[obj_id] = obj
        self.links_from_objects_to_portals[obj_id] = portal_id


    def unregister_object(self,obj:PortalAwareClass) -> None:
        """Remove an object from the registry.

        Args:
            obj: The object instance to unregister.
        """
        obj_id = obj.fingerprint
        self.known_objects.pop(obj_id, None)
        self.links_from_objects_to_portals.pop(obj_id, None)


    def count_linked_objects(self) -> int:
        """Count the number of objects linked to portals.

        Returns:
            The total count of linked portal-aware objects.
        """
        return len(self.links_from_objects_to_portals)

    def clear(self) -> None:
        """Clear all registry state.

        Primarily used for unit test cleanup.
        """
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
        """Get fingerprints of objects linked to a portal.

        Args:
            portal: The portal to query.
            target_class: Optional class filter. If provided, only objects
                of this type are included.

        Returns:
            A set of object fingerprints linked to the portal.
        """
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
        """Get objects linked to a portal.

        Args:
            portal: The portal to query.
            target_class: Optional class filter. If provided, only objects
                of this type are included.

        Returns:
            A list of portal-aware objects linked to the portal.
        """
        obj_ids = self.linked_objects_fingerprints(portal, target_class)
        result = []
        for obj_id in obj_ids:
            obj = self.known_objects.get(obj_id)
            result.append(obj)
        return result


# Singleton instance used by the rest of the module
_PORTAL_REGISTRY = _PortalRegistry()


class PortalAwareClass(CacheablePropertiesMixin, metaclass = GuardedInitMeta):
    """A base class for objects that need to access a portal.

    These objects either always work with a current portal,
    or they have a preferred (linked) portal which they activate every
    time their methods are called.
    """

    _linked_portal_at_init: BasicPortal|None
    _visited_portals: set[str] | None

    def __init__(self, portal:BasicPortal|None=None):
        """Initialize a PortalAwareClass instance.

        Args:
            portal: The portal to link this object to, or None to use
                current active portals for operations.
        """
        ensure_single_thread()
        self._init_finished = False
        if not (portal is None or isinstance(portal, BasicPortal)):
            raise TypeError(f"portal must be a BasicPortal or None, got {type(portal).__name__}")
        self._linked_portal_at_init = portal
        self._visited_portals = set()


    def __post_init__(self):
        """Execute post-initialization tasks for the portal-aware object.

        This method is automatically called after all __init__() methods complete.
        It registers the object with its linked portal if one was provided.
        """
        if self._linked_portal_at_init is not None:
            _PORTAL_REGISTRY.register_linked_object(
                self._linked_portal_at_init, self)
            self._first_visit_to_portal(self._linked_portal_at_init)



    @property
    def _linked_portal(self) -> BasicPortal | None:
        """The object's preferred portal, or None if using current active portals."""
        linked_portal =  self._linked_portal_at_init
        if linked_portal is not None:
            self._visit_portal(linked_portal)
        return linked_portal


    @property
    def portal(self) -> BasicPortal:
        """The portal used by this object's methods.

        Returns the linked portal if available, otherwise the current active portal.
        """
        portal_to_use = self._linked_portal
        if portal_to_use is None:
            portal_to_use = _PORTAL_REGISTRY.current_portal()
        self._visit_portal(portal_to_use)
        return portal_to_use


    def _visit_portal(self, portal: BasicPortal) -> None:
        """Register the object with the portal on first visit.

        Args:
            portal: The portal to visit.
        """
        if portal.fingerprint not in self._visited_portals:
            self._first_visit_to_portal(portal)


    def _first_visit_to_portal(self, portal: BasicPortal) -> None:
        """Handle the first visit to a portal by registering the object.

        Args:
            portal: The portal being visited for the first time.

        Raises:
            RuntimeError: If object is not initialized or portal already visited.
        """
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
        """The hash fingerprint of the portal-aware object.

        This is an internal identifier used by Pythagoras for object tracking
        in the registry. It differs from __hash__() and is based on the object itself.
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
        """Restore object state from unpickling.

        Resets portal-related attributes for proper initialization in the new environment.

        Args:
            state: The state dictionary for unpickling.
        """
        self._invalidate_cache()
        self._visited_portals = set()
        self._linked_portal_at_init = None


    @property
    def is_registered(self) -> bool:
        """True if the object has been registered in at least one portal."""
        if len(self._visited_portals) >=1:
            if not _PORTAL_REGISTRY.is_object_registered(self):
                raise RuntimeError(f"Object with id {self.fingerprint} is expected to be in the activated objects registry")
            return True
        return False


    def _clear(self):
        """Clear the object's registration state.

        Unregisters the object from all portals.
        """
        if not self._init_finished:
            return
        _PORTAL_REGISTRY.unregister_object(self)
        self._invalidate_cache()
        self._visited_portals = set()
        self._init_finished = False


def _clear_all_portals() -> None:
    """Clear all portals and portal-aware objects from the system.

    Primarily used for unit test cleanup.
    """
    objects_to_clear = list(_PORTAL_REGISTRY.known_objects.values())
    portals_to_clear = _PORTAL_REGISTRY.all_portals()

    for obj in objects_to_clear:
        obj._clear()

    for portal in portals_to_clear:
        portal._clear()

    _PORTAL_REGISTRY.clear()

    _reset_single_thread_enforcer()



##################################################



def get_most_recently_created_portal() -> BasicPortal | None:
    """Get the most recently created portal.

    Returns:
        The most recently created portal instance, or None if no portals exist.
    """
    return _PORTAL_REGISTRY.most_recently_created_portal


def _set_default_portal_instantiator(instantiator: Callable[[], None]) -> None:
    """Register a callable that creates the default portal.

    The callable is invoked lazily when get_current_portal() is called
    and no portals exist in the system.

    Args:
        instantiator: Zero-argument function that creates (and optionally enters)
            the default portal.

    Raises:
        TypeError: If instantiator is not callable.
        RuntimeError: If a default instantiator has already been registered.
    """
    _PORTAL_REGISTRY.register_default_portal_instantiator(instantiator)


def get_number_of_linked_portal_aware_objects() -> int:
    """Get the count of portal-aware objects currently linked to portals.

    Returns:
        The number of linked objects in the registry.
    """
    return _PORTAL_REGISTRY.count_linked_objects()


def _visit_portal(obj:Any, portal:BasicPortal) -> None:
    """Register all PortalAwareClass instances nested within an object.

    Recursively traverses the object structure and registers any found
    portal-aware objects with the specified portal.

    Args:
        obj: The object structure to traverse.
        portal: The portal to register found objects with.
    """
    return _visit_portal_impl(obj, portal=portal)


def _visit_portal_impl(obj: Any, portal: BasicPortal, seen: set[int] | None = None) -> None:
    """Recursively traverse an object and register PortalAwareClass instances.

    Args:
        obj: The object to check and traverse.
        portal: The portal to register with.
        seen: Set of object IDs already visited to handle cycles.
    """
    ensure_single_thread()

    if seen is None:
        seen = set()

    if id(obj) in seen:
        return

    if isinstance(obj, (str, range, bytearray, bytes, SafeStrTuple)):
        return

    seen.add(id(obj))

    if isinstance(obj, PortalAwareClass):
        obj._visit_portal(portal)
        return

    if isinstance(obj, Mapping):
        for key, value in obj.items():
            _visit_portal_impl(key, portal, seen)
            _visit_portal_impl(value, portal, seen)
        return

    if isinstance(obj, Iterable):
        for item in obj:
            _visit_portal_impl(item, portal, seen)
        return
