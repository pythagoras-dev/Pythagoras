"""Mixin for managing cached properties with automatic discovery and invalidation.

This module provides CacheablePropertiesMixin, which adds functionality to track
and invalidate functools.cached_property attributes across a class hierarchy.
The mixin enables efficient cache management by automatically discovering
all cached properties and providing methods to inspect, set, and clear their values.

Note:
    CacheablePropertiesMixin is not thread-safe and should not be used with dynamically
    modified classes. The implementation relies on functools.cached_property
    internals; any refactoring should begin with reviewing those implementation
    details.
"""
from functools import cached_property, cache
from typing import Any


class CacheablePropertiesMixin:
    """Mixin class for automatic management of cached properties.

    Provides methods to discover all functools.cached_property attributes
    in the class hierarchy and to inspect, set, and invalidate their cached
    values. This enables efficient cache management without manual tracking
    of individual cached properties.

    Note:
        This class is not thread-safe and should not be used with dynamically
        modified classes.

        Subclasses using __slots__ MUST include '__dict__' to support
        functools.cached_property, as enforced by _ensure_cache_storage_supported().
    """
    # Use __slots__ = () to prevent implicit addition of __dict__ or __weakref__,
    # allowing subclasses to use __slots__ for memory optimization.
    __slots__ = ()

    def _ensure_cache_storage_supported(self) -> None:
        """Ensure the instance can store cached_property values.

        Raises:
            TypeError: If the instance lacks __dict__, which is required
                for functools.cached_property storage.
        """
        if not hasattr(self, "__dict__"):
            cls_name = type(self).__name__
            raise TypeError(
                f"{cls_name} does not support cached_property caching because "
                f"it lacks __dict__;  add __slots__ = (..., '__dict__') or "
                f"avoid cached_property on this class.")


    @property
    def _all_cached_properties_names(self) -> frozenset[str]:
        """Names of all cached properties in the class hierarchy.

        Returns:
            Frozenset containing names of all functools.cached_property attributes
            in the current class and all its parents.
        """
        self._ensure_cache_storage_supported()
        return self._get_cached_properties_names_for_class(type(self))


    @staticmethod
    @cache
    def _get_cached_properties_names_for_class(cls: type) -> frozenset[str]:
        """Discover and cache all cached_property names for a class.

        Traverses the MRO to find all functools.cached_property attributes,
        including those wrapped by decorators that properly set __wrapped__.

        Args:
            cls: The class to inspect.

        Returns:
            Frozenset of cached property names.

        Note:
            Detection of wrapped cached_property relies on decorators using
            functools.wraps or manually setting __wrapped__. Unwrapping is
            limited to 100 levels to prevent infinite loops.
        """
        cached_names: set[str] = set()
        seen_names: set[str] = set()

        for curr_cls in cls.mro():
            for name, attr in curr_cls.__dict__.items():
                if name in seen_names:
                    continue
                seen_names.add(name)

                if isinstance(attr, cached_property):
                    cached_names.add(name)
                    continue

                # Unwrap decorators to find cached_property
                candidate = attr
                for _ in range(100):  # Prevent infinite loops
                    wrapped = getattr(candidate, "__wrapped__", None)
                    if wrapped is None:
                        break
                    candidate = wrapped

                if isinstance(candidate, cached_property):
                    cached_names.add(name)

        return frozenset(cached_names)


    def _get_all_cached_properties_status(self) -> dict[str, bool]:
        """Get caching status for all cached properties.

        Returns:
            Dictionary mapping property names to their caching status. True indicates
            the property has a cached value, False indicates it needs computation.
        """
        self._ensure_cache_storage_supported()

        return {name: name in self.__dict__
            for name in self._all_cached_properties_names}


    def _get_all_cached_properties(self) -> dict[str, Any]:
        """Retrieve currently cached values for all cached properties.

        Returns:
            Dictionary mapping property names to their cached values.
            Only includes properties that currently have cached values.
        """
        self._ensure_cache_storage_supported()

        vars_dict = self.__dict__
        cached_names = self._all_cached_properties_names

        return {name: vars_dict[name]
                for name in cached_names
                if name in vars_dict}


    def _get_cached_property(self, name: str) -> Any:
        """Retrieve the cached value for a single cached property.

        Args:
            name: The name of the cached property to retrieve.

        Returns:
            The cached value for the specified property.

        Raises:
            ValueError: If the name is not a recognized cached property.
            KeyError: If the property exists but doesn't have a cached value yet.
        """
        self._ensure_cache_storage_supported()

        if name not in self._all_cached_properties_names:
            raise ValueError(
                f"'{name}' is not a cached property")

        if name not in self.__dict__:
            raise KeyError(
                f"Cached property '{name}' has not been computed yet")

        return self.__dict__[name]


    def _get_cached_property_status(self, name: str) -> bool:
        """Check if a cached property has a cached value.

        Args:
            name: The name of the cached property to check.

        Returns:
            True if the property has a cached value, False if it needs computation.

        Raises:
            ValueError: If the name is not a recognized cached property.
        """
        self._ensure_cache_storage_supported()

        if name not in self._all_cached_properties_names:
            raise ValueError(
                f"'{name}' is not a cached property")

        return name in self.__dict__


    def _set_cached_properties(self, **names_values: Any) -> None:
        """Set cached values for cached properties directly.

        Bypasses property computation by writing values directly to __dict__.
        This is useful for restoring cached state or for testing purposes.

        Args:
            **names_values: Property names as keys and their values to cache.

        Raises:
            ValueError: If any provided name is not a recognized cached property.
        """
        self._ensure_cache_storage_supported()

        cached_names = self._all_cached_properties_names

        invalid_names = [name for name in names_values if name not in cached_names]
        if invalid_names:
            raise ValueError(
                f"Cannot set cached values for non-cached properties: {invalid_names}")

        vars_dict = self.__dict__
        for name, value in names_values.items():
            vars_dict[name] = value


    def _invalidate_cache(self) -> None:
        """Clear all cached property values.

        Removes cached values from __dict__, forcing re-computation on next access.
        This is more efficient than delattr as it avoids triggering custom
        __delattr__ logic in subclasses.
        """
        self._ensure_cache_storage_supported()

        vars_dict = self.__dict__
        cached_names = self._all_cached_properties_names

        keys_to_delete = [k for k in vars_dict if k in cached_names]

        for name in keys_to_delete:
            if name in vars_dict:
                del vars_dict[name]
