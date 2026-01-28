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
from typing import TypeVar, Any, Callable, Iterator, Final
from typing import Self
import pandas as pd
from mixinforge import (NotPicklableMixin, ImmutableParameterizableMixin,
    sort_dict_by_keys, GuardedInitMeta, ImmutableMixin,
    CacheablePropertiesMixin, SingleThreadEnforcerMixin)

from persidict import PersiDict, FileDirDict
from .._110_supporting_utilities import get_hash_signature, get_long_infoname
from .portal_description_helpers import (
    _describe_persistent_characteristic,
    _describe_runtime_characteristic)
from .default_portal_base_dir import get_default_portal_base_dir

_BASE_DIRECTORY_TXT: Final[str] = "Base directory"
_BACKEND_TYPE_TXT: Final[str] = "Backend type"
_PYTHAGORAS_VERSION_TXT: Final[str] = "Pythagoras version"
MAX_NESTED_PORTALS: Final[int] = 999

PortalAwareObjectType = TypeVar("PortalAwareObjectType", bound="PortalAwareObject")


class BasicPortal(NotPicklableMixin,
                  ImmutableParameterizableMixin,
                  SingleThreadEnforcerMixin,
                  CacheablePropertiesMixin,
                  metaclass = GuardedInitMeta):
    """A base class for portal objects that enable access to 'outside' world.

    In a Pythagoras-based application, a portal is the application's 'window'
    into the non-ephemeral world outside the current application execution
    session. It's a connector that enables a link between runtime-only
    ephemeral state and a persistent state that can be saved and loaded
    across multiple runs of the application, and across multiple computers.

    A Pythagoras-based application can have multiple portals,
    and there is usually a current one, accessible via
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
        super().__init__()
        self._init_finished = False
        self._entropy_infuser = random.Random()
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


    def get_linked_objects(self
            , target_class: type[PortalAwareObjectType] | None = None
            ) -> set[PortalAwareObjectType]:
        """Get the set of objects linked to this portal.

        Args:
            target_class: Optional class type filter. Defaults to PortalAwareObject.

        Returns:
            Set of PortalAwareObject instances linked to this portal,
            filtered by target_class if provided.
        """
        if target_class is None:
            target_class = PortalAwareObject
        return _PORTAL_REGISTRY.get_linked_objects(self, target_class)


    def count_linked_objects(self, target_class: type | None = None) -> int:
        """Get the number of objects linked to this portal.

        Args:
            target_class: Optional class type filter.

        Returns:
            Count of portal-aware objects linked to this portal, filtered by target_class if provided.
        """
        return len(self.get_linked_objects(target_class))


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
        return _PORTAL_REGISTRY.portal_stack.contains(self)


    def get_params(self) -> dict[str,Any]:
        """Get the portal's configuration parameters."""
        params = dict(root_dict=self._root_dict)
        sorted_params = sort_dict_by_keys(params)
        return sorted_params


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
    """Validate that the required portal type is a subclass of BasicPortal.

    Args:
        required_portal_type: The type to validate.

    Raises:
        TypeError: If required_portal_type is not a subclass of BasicPortal.
    """
    if not (isinstance(required_portal_type, type) and issubclass(required_portal_type, BasicPortal)):
        raise TypeError(
            f"required_portal_type must be BasicPortal or one of its subclasses, "
            f"got {get_long_infoname(required_portal_type)}")


class _PortalStack:
    """Manages the stack of active portals for context manager support.

    Handles pushing/popping portals when entering/exiting `with portal:` blocks,
    including re-entrancy counting for nested uses of the same portal.

    Attributes:
        _stack: List of active portals (most recent at end).
        _counters: Re-entrancy counters matching each stack entry.
    """

    def __init__(self) -> None:
        self._stack: list[BasicPortal] = []
        self._counters: list[int] = []

    def push(self, portal: BasicPortal) -> None:
        """Push a portal onto the stack, handling re-entrancy.

        Args:
            portal: The portal to push.

        Raises:
            RuntimeError: If nesting exceeds MAX_NESTED_PORTALS.
        """
        if self.depth() >= MAX_NESTED_PORTALS:
            raise RuntimeError(
                f"Too many nested portals: current depth is {self.depth()}, "
                f"max allowed is {MAX_NESTED_PORTALS}")
        if self._stack and self._stack[-1] is portal:
            self._counters[-1] += 1
        else:
            self._stack.append(portal)
            self._counters.append(1)
        self._check_consistency()

    def pop(self, portal: BasicPortal) -> None:
        """Pop a portal from the stack.

        Args:
            portal: The portal to pop (must be at top of stack).

        Raises:
            RuntimeError: If the portal is not at the top of the stack.
        """
        if not self._stack or self._stack[-1] is not portal:
            expected = self._stack[-1] if self._stack else None
            raise RuntimeError(
                f"Cannot pop portal from stack: expected {expected}, got {portal}")
        if self._counters[-1] == 1:
            self._stack.pop()
            self._counters.pop()
        else:
            self._counters[-1] -= 1
        self._check_consistency()

    def peek(self) -> BasicPortal | None:
        """Return the portal at the top of the stack, or None if empty."""
        return self._stack[-1] if self._stack else None

    def is_empty(self) -> bool:
        """Return True if the stack is empty."""
        return len(self._stack) == 0

    def depth(self) -> int:
        """Return total depth including re-entrancy counts."""
        return sum(self._counters)

    def unique_count(self) -> int:
        """Return the number of unique portals in the stack."""
        return len(set(self._stack))

    def contains(self, portal: BasicPortal) -> bool:
        """Check if the portal is anywhere in the stack."""
        return portal in self._stack

    def is_top(self, portal: BasicPortal) -> bool:
        """Check if the portal is at the top of the stack."""
        return bool(self._stack) and self._stack[-1] is portal

    def iter_unique(self) -> Iterator[BasicPortal]:
        """Iterate over unique portals in the stack."""
        return iter(set(self._stack))

    def as_set(self) -> set[BasicPortal]:
        """Return the set of unique portals in the stack."""
        return set(self._stack)

    def clear(self) -> None:
        """Clear the stack."""
        self._stack.clear()
        self._counters.clear()

    def _check_consistency(self) -> None:
        """Verify stack and counters are in sync."""
        if len(self._stack) != len(self._counters):
            raise RuntimeError(
                f"Internal error: _stack and _counters are out of sync "
                f"(stack length={len(self._stack)}, counters length={len(self._counters)})")


class _PortalRegistry(NotPicklableMixin, SingleThreadEnforcerMixin):
    """Registry maintaining all portal bookkeeping and state for Pythagoras.

    This singleton tracks all portals and portal-aware objects, delegates stack
    management to _PortalStack, and provides mechanisms for portal lookup and
    lifecycle management.

    Attributes:
        known_portals: Set of known (existing in the system) portal instances.
        portal_stack: Stack manager for active portals (nested `with` statements).
        most_recently_created_portal: Last portal instantiated, used for auto-activation.
        links_from_objects_to_portals: Maps linked PortalAwareObject instances to their portals.
        known_objects: Set of known PortalAwareObject instances.
        default_portal_instantiator: Factory function for creating the default portal.
    """

    def __init__(self) -> None:
        super().__init__()
        self.known_portals: set[BasicPortal] = set()
        self.portal_stack: _PortalStack = _PortalStack()
        self.most_recently_created_portal: BasicPortal | None = None
        self.links_from_objects_to_portals: dict[PortalAwareObject, BasicPortal] = {}
        self.known_objects: set[PortalAwareObject] = set()
        self.default_portal_instantiator: Callable[[], None] | None = None



    def register_default_portal_instantiator(self, instantiator: Callable[[], None]) -> None:
        """Register a callable that creates the default portal.

        Args:
            instantiator: Factory function that creates the default portal.

        Raises:
            TypeError: If instantiator is not callable.
            RuntimeError: If a default portal instantiator is already registered.
        """
        self._restrict_to_single_thread()
        if not callable(instantiator):
            raise TypeError(
                f"Default portal instantiator must be callable, "
                f"got {get_long_infoname(instantiator)}")

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
        self._restrict_to_single_thread()
        self.known_portals.add(portal)
        self.most_recently_created_portal = portal


    def unregister_portal(self, portal: BasicPortal) -> None:
        """Remove the portal from the registry and try to clear linked objects.

        Args:
            portal: The portal instance to unregister.
        """
        all_links = list(self.links_from_objects_to_portals.items())
        for obj, linked_portal in all_links:
            if linked_portal == portal:
                obj._clear()

        self.known_portals.discard(portal)
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
        return len(self.get_known_portals(required_portal_type))

    def get_known_portals(self, required_portal_type: type[PortalType] = BasicPortal) -> set[PortalType]:
        """Get all portals registered in the system.

        Args:
            required_portal_type: Expected portal type for validation.

        Returns:
            Set of all portal instances currently known to the system.

        Raises:
            TypeError: If any known portal is not an instance of required_portal_type.
        """
        _validate_required_portal_type(required_portal_type)
        candidates = set(self.known_portals)
        for p in candidates:
            if not isinstance(p, required_portal_type):
                raise TypeError(
                    f"Found portal {type(p).__name__} which is not "
                    f"an instance of required {required_portal_type.__name__}")
        return candidates

    def push_new_active_portal(self, portal: BasicPortal) -> None:
        """Push the portal onto the active stack, handling re-entrancy.

        Args:
            portal: The portal instance to push.

        Raises:
            RuntimeError: If nesting exceeds MAX_NESTED_PORTALS or portal is unregistered.
        """
        self._restrict_to_single_thread()
        if portal not in self.known_portals:
            raise RuntimeError(
                f"Cannot push unregistered portal {portal} onto stack. "
                f"Known portals: {len(self.known_portals)}")
        self.portal_stack.push(portal)


    def pop_active_portal(self, portal: BasicPortal) -> None:
        """Pop the portal from the active stack, maintaining consistency.

        Args:
            portal: The portal instance to pop.

        Raises:
            RuntimeError: If the portal is unregistered or not at the top of the stack.
        """
        self._restrict_to_single_thread()
        if portal not in self.known_portals:
            raise RuntimeError(
                f"Cannot pop unregistered portal {portal} from stack. "
                f"Known portals: {len(self.known_portals)}")
        self.portal_stack.pop(portal)


    def get_current_portal(self) -> BasicPortal:
        """Get the current portal object.

        Returns the top portal from the active stack, or activates the most recently
        created portal if the stack is empty. Creates the default portal if none exist.

        Returns:
            The current portal instance.
        """
        top = self.portal_stack.peek()
        if top is not None:
            return top

        if self.most_recently_created_portal is None:
            if self.default_portal_instantiator is not None:
                self.default_portal_instantiator()
                if self.most_recently_created_portal is None:
                    raise RuntimeError("Default portal instantiator failed to create a portal")
                elif not isinstance(self.most_recently_created_portal, BasicPortal):
                    raise RuntimeError(
                        f"Default portal instantiator created an object of type "
                        f"{get_long_infoname(self.most_recently_created_portal)}, "
                        f"expected BasicPortal")
            else:
                raise RuntimeError(
                    "No portal is active and no default portal instantiator was set "
                    "using _set_default_portal_instantiator()")

        self.portal_stack.push(self.most_recently_created_portal)
        return self.most_recently_created_portal


    def is_current_portal(self, portal: BasicPortal) -> bool:
        """Check if the portal is at the top of the active stack.

        Args:
            portal: The portal instance to check.

        Returns:
            True if the portal is current (top of stack), False otherwise.
        """
        return self.portal_stack.is_top(portal)


    def count_unique_active_portals(self, required_portal_type: type[PortalType] = BasicPortal) -> int:
        """Count unique portals currently in the active stack.

        Args:
            required_portal_type: Expected portal type for validation.

        Returns:
            The count of unique portals currently in the active portal stack.

        Raises:
            TypeError: If any active portal is not an instance of required_portal_type.
        """
        _validate_required_portal_type(required_portal_type)
        unique_active = self.portal_stack.as_set()
        for p in unique_active:
            if not isinstance(p, required_portal_type):
                raise TypeError(
                    f"Found active portal {get_long_infoname(p)} which is not "
                    f"an instance of required {required_portal_type.__name__}")
        return len(unique_active)


    def measure_active_portals_stack_depth(self,
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
        for portal in self.portal_stack.iter_unique():
            if not isinstance(portal, required_portal_type):
                raise TypeError(
                    f"Found active portal {get_long_infoname(portal)} which is not "
                    f"an instance of required {required_portal_type.__name__}")
        return self.portal_stack.depth()

    def get_nonactive_portals(self, required_portal_type: type[PortalType] = BasicPortal) -> set[BasicPortal]:
        """Get all portals that are not in the active stack.

        Args:
            required_portal_type: Expected portal type for validation.

        Returns:
            Set of portal instances not currently in the active portal stack.

        Raises:
            TypeError: If any non-active portal is not an instance of required_portal_type.
        """
        _validate_required_portal_type(required_portal_type)
        active_portals = self.portal_stack.as_set()
        all_known = self.get_known_portals(BasicPortal)

        candidates = {p for p in all_known if p not in active_portals}

        for p in candidates:
            if not isinstance(p, required_portal_type):
                raise TypeError(
                    f"Found non-active portal {get_long_infoname(p)} which is not "
                    f"an instance of required {required_portal_type.__name__}")

        return candidates

    def get_noncurrent_portals(self, required_portal_type: type[PortalType] = BasicPortal) -> set[BasicPortal]:
        """Get all known portals that are not the current portal.

        The current portal is the one at the top of the active stack.
        If the stack is empty, all known portals are returned.

        Args:
            required_portal_type: Expected portal type for validation.

        Returns:
            Set of all known portal instances except the current one.

        Raises:
            TypeError: If any non-current portal is not an instance of required_portal_type.
        """
        _validate_required_portal_type(required_portal_type)
        current_portal = self.portal_stack.peek()

        all_known = self.get_known_portals(BasicPortal)
        candidates = {p for p in all_known if p != current_portal}

        for p in candidates:
            if not isinstance(p, required_portal_type):
                raise TypeError(
                    f"Found non-current portal {get_long_infoname(p)} which is not "
                    f"an instance of required {required_portal_type.__name__}")

        return candidates

    def register_linkfree_object(self, obj: PortalAwareObject) -> None:
        """Register a portal-aware object in the global registry.

        Args:
            obj: The object instance to register.
        """
        if obj._linked_portal is not None:
            raise ValueError(
                f"Cannot register object {obj} as linkfree: "
                f"object is already linked to portal {obj._linked_portal}"
            )

        self.known_objects.add(obj)

    def is_object_registered(self, obj: PortalAwareObject) -> bool:
        """Check if an object is currently registered.

        Args:
            obj: The object instance to check.

        Returns:
            True if the object is registered, False otherwise.
        """
        return obj in self.known_objects

    def register_linked_object(self, portal: BasicPortal, obj:PortalAwareObject) -> None:
        """Link an object to a portal in the registry.

        The linked object will use the portal for all its operations
        unless explicitly configured otherwise.

        Args:
            portal: The portal to link the object to.
            obj: The portal-aware object to link.
        """
        if obj._linked_portal is None:
            raise ValueError(
                f"Cannot register object {obj} as linked: "
                f"object has _linked_portal=None"
            )

        self.known_objects.add(obj)
        self.links_from_objects_to_portals[obj] = portal


    def unregister_object(self, obj:PortalAwareObject) -> None:
        """Remove an object from the registry.

        Args:
            obj: The object instance to unregister.
        """
        self.known_objects.discard(obj)
        self.links_from_objects_to_portals.pop(obj, None)


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
        self.portal_stack.clear()
        self.most_recently_created_portal = None
        self.links_from_objects_to_portals.clear()
        self.known_objects.clear()
        self.default_portal_instantiator = None


    def get_linked_objects(self
            , portal: BasicPortal
            , target_class: type[PortalAwareObjectType] = None
            ) -> set[PortalAwareObjectType]:
        """Get the set of objects linked to a portal.

        Args:
            portal: The portal to query.
            target_class: Optional class filter. If provided, only objects
                of this type are included.

        Returns:
            A set of PortalAwareObject instances linked to the portal.
        """
        objs = {o for o, p in self.links_from_objects_to_portals.items() if p == portal}

        if target_class is None:
            return objs

        return {o for o in objs if isinstance(o, target_class)}


# Singleton instance used by the rest of the module
_PORTAL_REGISTRY = _PortalRegistry()


class PortalAwareObject(CacheablePropertiesMixin,
                        ImmutableMixin,
                        SingleThreadEnforcerMixin,
                        metaclass = GuardedInitMeta):
    """A base class for objects that need to access a portal.

    Objects work with either the current portal or a linked portal
    specified at initialization. Registration with the portal is lazy - it
    happens on first access to the `portal` property, not during `__init__()`.
    """

    _linked_portal: BasicPortal | None
    _visited_portals: set[BasicPortal]

    def __init__(self, portal:BasicPortal|None=None):
        """Initialize a PortalAwareObject instance.

        Args:
            portal: The portal to link this object to, or None to use
                current active portals for operations. Registration happens
                lazily on first `portal` property access.
        """
        super().__init__()
        self._restrict_to_single_thread()
        self._init_finished = False
        if not (portal is None or isinstance(portal, BasicPortal)):
            raise TypeError(
                f"portal must be a BasicPortal or None, "
                f"got {get_long_infoname(portal)}")
        self._linked_portal = portal
        self._visited_portals = set()



    def link_to_portal(self, portal: BasicPortal) -> Self:
        """Create a copy of this object linked to a (new) portal.

        Args:
            portal: The portal to link the new object to.

        Returns:
            This instance if already linked to the specified portal, otherwise
            a new instance linked to the specified portal.

        Raises:
            TypeError: If portal is not a BasicPortal instance.
            RuntimeError: If object is not fully initialized.
        """

        if not self._init_finished:
            raise RuntimeError("Cannot link an uninitialized object to a portal")

        if not isinstance(portal, BasicPortal):
            raise TypeError(
                f"portal must be a BasicPortal, got {get_long_infoname(portal)}")

        # Return self if already linked to the same portal
        if self._linked_portal is portal:
            return self

        # Get current state (excludes portal information per contract)
        state = self.__getstate__()

        # Create new instance with the new portal
        new_obj = type(self).__new__(type(self))
        new_obj.__setstate__(state)
        new_obj._linked_portal = portal

        return new_obj


    @property
    def linked_portal(self) -> BasicPortal | None:
        """The object's preferred portal, or None if using current active portals."""
        linked_portal =  self._linked_portal
        if linked_portal is not None:
            self._visit_portal(linked_portal)
        return linked_portal


    @cached_property
    def is_linked_(self) -> bool:
        """True if the object is linked to a portal, False otherwise."""
        return self._linked_portal is not None


    @cached_property
    def is_linkfree(self) -> bool:
        """True if the object is not linked to a portal, False otherwise."""
        return self._linked_portal is None


    @property
    def portal(self) -> BasicPortal:
        """The portal used by this object's methods.

        Triggers lazy registration on first access. Returns the linked portal
        if available, otherwise the current active portal.
        """
        portal_to_use = self.linked_portal
        if portal_to_use is None:
            portal_to_use = _PORTAL_REGISTRY.get_current_portal()
        self._visit_portal(portal_to_use)
        return portal_to_use


    def _visit_portal(self, portal: BasicPortal) -> None:
        """Register the object with the portal if it's the first visit.

        Args:
            portal: The portal to visit.
        """
        if portal not in self._visited_portals:
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
        if portal in self._visited_portals:
            raise RuntimeError(
                f"Object {self} has already been visited "
                f"and registered in portal {portal}")


        self._visited_portals.add(portal)

        if self._linked_portal is not None:
            _PORTAL_REGISTRY.register_linked_object(
                self._linked_portal, self)
        else:
            _PORTAL_REGISTRY.register_linkfree_object(self)


    def get_identity_key(self) -> Any:
        """Get the identity key (hash signature) of the object.

        Returns:
            The object's hash signature.

        Raises:
            RuntimeError: If the object is not fully initialized.
        """
        if not self._init_finished:
            raise RuntimeError("Object is not fully initialized yet, "
                               "identity_key is not available.")
        return get_hash_signature(self)

    def __repr__(self) -> str:
        """Return a string representation of this portal-aware object."""
        class_name = type(self).__name__
        if self._init_finished:
            state = self.__getstate__()
            return f"{class_name}({state})"
        else:
            return f"{class_name}(<initializing>)"

    @abstractmethod
    def __getstate__(self) -> dict[str, Any]:
        """Prepare the object's state for pickling.

        This method must be overridden in subclasses to ensure that portal
        information is NOT included in the pickled state.
        """
        if type(self) is PortalAwareObject:
            raise NotImplementedError(
                "PortalAwareObject instances are not picklable. "
                "Method __getstate__() must be overridden in subclasses.")
        else:
            return dict()


    @abstractmethod
    def __setstate__(self, state: dict[str, Any]):
        """Restore object state from unpickling.

        Resets portal-related attributes for proper initialization in the new environment.

        Args:
            state: The state dictionary for unpickling.
        """
        self._invalidate_cache()
        self._visited_portals = set()
        self._linked_portal = None



    # TODO: double-check this logic
    @property
    def is_registered(self) -> bool:
        """True if the object has been registered in at least one portal."""
        if len(self._visited_portals) >=1:
            if not _PORTAL_REGISTRY.is_object_registered(self):
                raise RuntimeError(f"Object {self} is expected to be in the activated objects registry")
            return True
        return False


    def _clear(self) -> None:
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
    objects_to_clear = list(_PORTAL_REGISTRY.known_objects)
    portals_to_clear = _PORTAL_REGISTRY.get_known_portals()

    for obj in objects_to_clear:
        obj._clear()

    for portal in portals_to_clear:
        portal._clear()

    _PORTAL_REGISTRY.clear()



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


def count_linked_portal_aware_objects() -> int:
    """Get the count of portal-aware objects currently linked to portals.

    Returns:
        The number of linked objects in the registry.
    """
    return _PORTAL_REGISTRY.count_linked_objects()




