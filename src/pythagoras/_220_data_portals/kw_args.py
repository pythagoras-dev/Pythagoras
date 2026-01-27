"""Keyword argument containers with deterministic ordering and value packing.

This module provides KwArgs and its variants (PackedKwArgs, UnpackedKwArgs)
to manage function keyword arguments in a way that enables reliable hashing,
comparison, and content-addressable storage.

Key Features:
- Deterministic key ordering for consistent hashing and equality checks
- Packing: convert values to ValueAddr handles for content-addressable storage
- Unpacking: resolve ValueAddr handles back to raw values
- Type safety: prevents nested KwArgs and enforces string keys

Design Rationale:
    Standard Python dicts have non-deterministic iteration order in older
    versions and no built-in mechanism for content-addressable value storage.
    KwArgs addresses both issues by sorting keys deterministically and
    providing pack/unpack methods that convert between raw values and
    their content-addressed representations (ValueAddr).
"""

from __future__ import annotations

from typing import Any

from .._210_basic_portals import (
    get_current_portal,
    PortalAwareObject,
    BasicPortal,
    )
from .data_portal_core_classes import ValueAddr, DataPortal, HashAddr
from mixinforge import sort_dict_by_keys
from mixinforge.utility_functions import find_instances_inside_composite_object

class KwArgs(dict):
    """Container for keyword arguments with deterministic ordering and packing.

    Provides utilities to sort keys deterministically and to pack/unpack values
    to and from ValueAddr instances so that argument sets can be compared and
    hashed reliably across runs.

    Class Invariants:
        1. **String keys only**: All keys must be strings (enforced in __setitem__).
        2. **Deterministic ordering**: Keys are sorted alphabetically upon
           initialization and before pickling for consistent serialization.
        3. **Equality independence**: Two KwArgs with the same key-value pairs
           are equal regardless of insertion order.
        4. **Pickle stability**: Pickling produces identical bytes for instances
           with same content but different insertion order.
    """


    def __init__(self, *args, **kwargs):
        """Create a KwArgs mapping with deterministically sorted keys.

        Args:
            *args: Positional arguments accepted by dict().
            **kwargs: Keyword arguments accepted by dict().
        """
        dict.__init__(self)
        tmp_dict = dict(*args, **kwargs)
        tmp_dict = sort_dict_by_keys(tmp_dict)
        self.update(tmp_dict)


    def sort(self, inplace: bool) -> KwArgs:
        """Return a version with keys sorted, optionally in place.

        Args:
            inplace: If True, sorts this instance and returns it. If False,
                returns a new KwArgs instance with sorted keys.

        Returns:
            KwArgs: The sorted KwArgs (self when inplace=True, otherwise a new instance).
        """
        if inplace:
            sorted_dict = sort_dict_by_keys(self)
            self.clear()
            self.update(sorted_dict)
            return self
        else:
            return KwArgs(**sort_dict_by_keys(self))


    def copy(self) -> KwArgs:
        """Create a shallow copy of this KwArgs instance.

        Returns a new instance of the same class type (KwArgs, PackedKwArgs, or
        UnpackedKwArgs) with the same keys and values. Keys are deterministically
        sorted in the copy.

        Returns:
            KwArgs: A new instance of the same type as self with copied contents.

        Example:
            >>> kwargs = KwArgs(x=5, y="hello")
            >>> copy = kwargs.copy()
            >>> assert copy == kwargs
            >>> assert copy is not kwargs
            >>>
            >>> packed = kwargs.pack()
            >>> packed_copy = packed.copy()
            >>> assert isinstance(packed_copy, PackedKwArgs)
        """
        return type(self)(**self)


    def __setitem__(self, key, value):
        """Set an item enforcing KwArgs invariants.

        Enforces that keys are strings and values are not base KwArgs instances.
        PackedKwArgs and UnpackedKwArgs are allowed as values since they represent
        immutable data types rather than structural nesting.

        Args:
            key: The key to set; must be a str.
            value: The value to associate with the key.

        Raises:
            KeyError: If the key is not a string.
            ValueError: If the value is a base KwArgs instance (nested KwArgs are disallowed).
        """
        if not isinstance(key, str):
            raise KeyError("Keys must be strings in KwArgs.")
        if type(value) is KwArgs:
            raise ValueError("Nested KwArgs are not allowed.")
        super().__setitem__(key, value)


    def update(self, *args, **kwargs):
        """Update the dictionary with new keys and values.

        Args:
            *args: Positional arguments (other dict or iterable of pairs).
            **kwargs: Keyword arguments.
        """
        if args:
            if len(args) > 1:
                raise TypeError("update expected at most 1 arguments, "
                                f"got {len(args)}")
            other = dict(args[0])
            for key in other:
                self[key] = other[key]
        for key in kwargs:
            self[key] = kwargs[key]


    def __reduce__(self):
        """Support pickling by sorting keys first for stable serialization.

        Returns:
            tuple: Standard pickle reduce tuple from dict.__reduce__().
        """
        self.sort(inplace=True)
        return super().__reduce__()


    def unpack(self) -> UnpackedKwArgs:
        """Resolve all ValueAddr values to their underlying raw values.

        This is the inverse of pack(). It retrieves the actual values from
        storage, enabling function execution with the original arguments.

        Returns:
            UnpackedKwArgs: A new mapping where each ValueAddr is replaced with
            its underlying value via ValueAddr.get().

        Example:
            >>> packed = KwArgs(x=5, y="hello").pack()
            >>> unpacked = packed.unpack()
            >>> assert unpacked["x"] == 5
            >>> assert unpacked["y"] == "hello"
        """
        unpacked_copy = dict()
        for k, v in self.items():
            if isinstance(v, ValueAddr):
                unpacked_copy[k] = v.get()
            else:
                unpacked_copy[k] = v
        unpacked_copy = UnpackedKwArgs(**unpacked_copy)
        return unpacked_copy


    def pack(self, store = True) -> PackedKwArgs:
        """Convert values to ValueAddr handles for content-addressable storage.

        This enables reliable equality checks and hashing based on content
        rather than object identity. When store=True, values are persisted
        to the portal's storage backend and can be retrieved in future
        sessions. When store=False, produces transient addresses useful
        for identifying argument sets without persistence.

        Args:
            store: If True, values are stored in the active portal and the
                returned addresses persist across sessions. If False, produces
                non-stored addresses suitable for transient signatures.

        Returns:
            PackedKwArgs: A new mapping with values converted to ValueAddr.

        Example:
            >>> kwargs = KwArgs(x=5, y="hello")
            >>> packed = kwargs.pack(store=True)  # Values stored in portal
            >>> # packed can be hashed, compared, or unpacked later
        """
        packed_copy = dict()
        if store:
            portal = get_current_portal()
            _visit_portal(self, portal)
            with portal:
                for k,v in self.items():
                    packed_copy[k] = ValueAddr(v,store=True)
        else:
            for k, v in self.items():
                packed_copy[k] = ValueAddr(v, store=False)
        packed_copy = PackedKwArgs(**packed_copy)
        return packed_copy


class PackedKwArgs(KwArgs):
    """KwArgs container where all values are ValueAddr instances.

    This specialized subclass represents function arguments in their packed
    form, where each value has been converted to a ValueAddr handle. This
    enables content-based hashing, equality checks, and persistent storage
    of argument sets.

    Created by calling KwArgs.pack(). Should not typically be instantiated
    directly by user code.

    Class Invariants (in addition to KwArgs invariants):
        1. **String keys only**: All keys must be strings (inherited from KwArgs).
        2. **ValueAddr values only**: All values must be ValueAddr instances.
           No other types are permitted.
        3. **Deterministic ordering**: Keys are sorted alphabetically (inherited).
        4. **Equality independence**: Equal regardless of insertion order (inherited).
        5. **Pickle stability**: Identical serialization for same content (inherited).
        6. **Idempotent packing**: pack().pack() produces equivalent content to pack().
        7. **Reversible**: unpack() produces UnpackedKwArgs that can be packed again.

    Example:
        >>> original = KwArgs(x=5, y=[1, 2, 3])
        >>> packed = original.pack()  # Returns PackedKwArgs
        >>> assert isinstance(packed, PackedKwArgs)
        >>> assert all(isinstance(v, ValueAddr) for v in packed.values())
    """
    def __init__(self, *args, **kwargs):
        """Construct a PackedKwArgs mapping.

        Accepts the same arguments as dict/KwArgs.
        """
        super().__init__(*args, **kwargs)


    def __setitem__(self, key, value):
        """Set an item enforcing PackedKwArgs invariants.

        PackedKwArgs must only contain ValueAddr instances as values.

        Args:
            key: The key to set; must be a str.
            value: The value to associate with the key; must be a ValueAddr.

        Raises:
            KeyError: If the key is not a string.
            ValueError: If the value is not a ValueAddr instance.
        """
        if not isinstance(key, str):
            raise KeyError("Keys must be strings in PackedKwArgs.")
        if not isinstance(value, ValueAddr):
            raise ValueError("PackedKwArgs can only contain ValueAddr instances.")
        dict.__setitem__(self, key, value)


class UnpackedKwArgs(KwArgs):
    """KwArgs container where all values are raw (non-ValueAddr) objects.

    This specialized subclass represents function arguments in their unpacked
    form, ready for execution. All ValueAddr handles have been resolved to
    their underlying values.

    Created by calling KwArgs.unpack() or PackedKwArgs.unpack(). Should not
    typically be instantiated directly by user code.

    Class Invariants:
        1. **String keys only**: All keys must be strings (inherited from KwArgs).
        2. **No ValueAddr values**: Values cannot be ValueAddr instances.
           ValueAddr must be resolved before storage.
        3. **Deterministic ordering**: Keys are sorted alphabetically (inherited).
        4. **Equality independence**: Equal regardless of insertion order (inherited).
        5. **Pickle stability**: Identical serialization for same content (inherited).
        6. **Idempotent unpacking**: unpack().unpack() produces equivalent content.
        7. **Reversible**: pack() produces PackedKwArgs that can be unpacked again.

    Example:
        >>> packed = KwArgs(x=5, y=[1, 2, 3]).pack()
        >>> unpacked = packed.unpack()  # Returns UnpackedKwArgs
        >>> assert isinstance(unpacked, UnpackedKwArgs)
        >>> assert unpacked["x"] == 5
    """
    def __init__(self, *args, **kwargs):
        """Construct an UnpackedKwArgs mapping.

        Accepts the same arguments as dict/KwArgs.
        """
        super().__init__(*args, **kwargs)


    def __setitem__(self, key, value):
        """Set an item enforcing UnpackedKwArgs invariants.

        UnpackedKwArgs must only contain raw values. ValueAddr and base KwArgs are rejected,
        but PackedKwArgs and UnpackedKwArgs are allowed as they represent data values.

        Args:
            key: The key to set; must be a str.
            value: The value to associate with the key; must not be ValueAddr or base KwArgs.

        Raises:
            KeyError: If the key is not a string.
            ValueError: If the value is a ValueAddr or base KwArgs instance.
        """
        if not isinstance(key, str):
            raise KeyError("Keys must be strings in UnpackedKwArgs.")
        if isinstance(value, ValueAddr) or type(value) is KwArgs:
            raise ValueError("UnpackedKwArgs cannot contain ValueAddr or base KwArgs instances.")
        dict.__setitem__(self, key, value)


def _visit_portal(obj: Any, portal: DataPortal) -> None:
    """Traverse an object structure and register all found PortalAwareObjects with the portal.

    This function makes sure the object, including all its (recursively)
    nested/referenced PortalAwareObject (sub)objects, has completed all necessary
    registration steps with the given portal, so it can be safely used within
    the context of the portal. This includes copying the object, its subobjects,
    and any data referenced by HashAddr instances to the portal's storage backend.

    Args:
        obj: The object structure to traverse.
        portal: The portal to register found objects with.
    """
    all_items:dict[int, Any] = dict()
    queued_items_ids:set[int] = set()
    processed_items_ids:set[int] = set()

    def pre_process_object(obj: Any) -> None:
        for item in find_instances_inside_composite_object(
                obj, (PortalAwareObject,BasicPortal, HashAddr), deep_search=False):
            if id(item) not in all_items:
                all_items[id(item)] = item
                queued_items_ids.add(id(item))

    pre_process_object(obj)

    while queued_items_ids:
        for work_item_id in list(queued_items_ids):
            queued_items_ids.remove(work_item_id)

            if work_item_id in processed_items_ids:
                continue
            else:
                processed_items_ids.add(work_item_id)

            work_item = all_items[work_item_id]
            if isinstance(work_item, BasicPortal):
                continue
            elif isinstance(work_item, PortalAwareObject):
                work_item._visit_portal(portal)
            elif isinstance(work_item, HashAddr):
                if work_item.ready:
                    with portal:
                        # Ensure the item will be copied to the current portal
                        # if retrieved from a different one
                        work_item = work_item.get()
                    pre_process_object(work_item)