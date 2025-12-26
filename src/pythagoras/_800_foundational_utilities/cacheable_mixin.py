"""Mixin for classes that use cached properties and need invalidation.

This module provides CacheableMixin, which adds functionality to track and
invalidate functools.cached_property attributes in a class hierarchy.
"""
from functools import cached_property, cache


class CacheableMixin:
    """Mixin class for automatic management of cached properties.

    This class provides methods to discover all attributes decorated with
    `functools.cached_property` in the class hierarchy and to invalidate
    their cached values.
    """

    @property
    def all_cached_properties_names(self) -> set[str]:
        """Set of names of all cached properties in the class hierarchy.

        Includes attributes declared as `functools.cached_property` in the
        current class and all its parents.
        """
        return self._get_cached_properties_for_class(type(self))


    @staticmethod
    @cache
    def _get_cached_properties_for_class(cls: type) -> set[str]:
        """Helper to cache property discovery for each class."""
        cached_names: set[str] = set()
        seen_names: set[str] = set()

        # Walk MRO to respect inheritance and shadowing
        for curr_cls in cls.mro():
            for name, attr in curr_cls.__dict__.items():
                if name in seen_names:
                    continue
                seen_names.add(name)

                if isinstance(attr, cached_property):
                    cached_names.add(name)

        return cached_names


    def get_cached_values_status(self) -> dict[str, bool]:
        """Get the status of all cached properties.

        Returns:
            Dictionary mapping property names to whether they are currently cached.

        Note:
            For classes using __slots__ without __dict__, this checks if the
            attribute has been set, which indicates it's been cached.
        """
        status = {}

        if hasattr(self, '__dict__'):
            # Standard case: check in __dict__
            for name in self.all_cached_properties_names:
                status[name] = name in self.__dict__
        else:
            # For __slots__-only classes, check using hasattr on the instance's
            # actual storage, not the descriptor
            for name in self.all_cached_properties_names:
                # Check if the slot has been assigned without triggering the descriptor
                try:
                    # Access via object.__getattribute__ to bypass the descriptor
                    object.__getattribute__(self, name)
                    status[name] = True
                except AttributeError:
                    status[name] = False

        return status


    def _invalidate_cache(self) -> None:
        """Invalidate cached values for all cached properties.

        Clears the cached values for every attribute identified by
        `all_cached_properties_names`. This forces re-computation on next access.
        """
        # Check if instance has __dict__ (not using __slots__)
        if not hasattr(self, '__dict__'):
            # For classes with __slots__, attempt to delete individual attributes
            for name in self.all_cached_properties_names:
                try:
                    delattr(self, name)
                except AttributeError:
                    pass  # Not cached yet
        else:
            for name in self.all_cached_properties_names:
                self.__dict__.pop(name, None)
