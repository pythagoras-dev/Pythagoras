"""Mixin for classes that use cached properties and need invalidation.

This module provides CacheableMixin, which adds functionality to track and
invalidate functools.cached_property attributes in a class hierarchy.
"""
from functools import cached_property


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
        cached_names: set[str] = set()
        # Walk through the MRO so that parents are included as well.
        for cls in type(self).mro():
            for name, attr in cls.__dict__.items():
                if isinstance(attr, cached_property):
                    cached_names.add(name)
        return cached_names

    def _invalidate_cache(self) -> None:
        """Invalidate cached values for all cached properties.

        Clears the cached values for every attribute identified by
        `all_cached_properties_names`. This forces re-computation on next access.
        """
        # Remove stored computed values for every cached_property, if present
        for name in self.all_cached_properties_names:
            # Using pop with default avoids KeyError if the property hasn't been accessed yet
            self.__dict__.pop(name, None)
