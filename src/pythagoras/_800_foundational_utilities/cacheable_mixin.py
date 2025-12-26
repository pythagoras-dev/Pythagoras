"""Mixin for classes that use cached properties and need invalidation.

This module provides CacheableMixin, which adds functionality to track and
invalidate functools.cached_property attributes in a class hierarchy.

Note: the CacheableMixin class is not thread-safe.
     Also, the CacheableMixin is not supposed to be used with
     dynamically modified classes.
"""
from functools import cached_property, cache


class CacheableMixin:
    """Mixin class for automatic management of cached properties.

    This class provides methods to discover all attributes decorated with
    `functools.cached_property` in the class hierarchy and to invalidate
    their cached values.

    Note: the CacheableMixin class is not thread-safe.
       Also, the CacheableMixin is not supposed to be used with
       dynamically modified classes.
    """
    # We use __slots__ = () to ensure that this mixin doesn't implicitly
    # add __dict__ or __weakref__ to subclasses. This allows subclasses
    # to use __slots__ for memory optimization if they wish.
    # Note: subclasses that use __slots__ MUST include '__dict__' in their
    # slots to support functools.cached_property, as enforced by
    # _ensure_cache_storage_supported().
    __slots__ = ()

    def _ensure_cache_storage_supported(self) -> None:
        """Ensure the instance can store cached_property values.

        Standard functools.cached_property requires a writable __dict__.
        Raise a clear error for classes that omit __dict__
        (e.g., __slots__ without __dict__).
        """
        if not hasattr(self, "__dict__"):
            cls_name = type(self).__name__
            raise TypeError(
                f"{cls_name} does not support cached_property caching because "
                f"it lacks __dict__;  add __slots__ = (..., '__dict__') or "
                f"avoid cached_property on this class.")


    @property
    def _all_cached_properties_names(self) -> frozenset[str]:
        """Set of names of all cached properties in the class hierarchy.

        Includes attributes declared as `functools.cached_property` in the
        current class and all its parents.
        """
        self._ensure_cache_storage_supported()
        return self._get_cached_properties_names_for_class(type(self))


    @staticmethod
    @cache
    def _get_cached_properties_names_for_class(cls: type) -> frozenset[str]:
        """Helper to cache property discovery for each class.

        Note:
            This correctly detects `functools.cached_property`. If a cached_property
            is wrapped by another decorator, detection relies on the wrapper
            setting `__wrapped__` correctly (e.g., using `functools.wraps`).
        """
        cached_names: set[str] = set()
        seen_names: set[str] = set()

        for curr_cls in cls.mro():
            for name, attr in curr_cls.__dict__.items():
                if name in seen_names:
                    continue
                seen_names.add(name)

                # Fast path: direct check
                if isinstance(attr, cached_property):
                    cached_names.add(name)
                    continue

                # Slow path: unwrap decorators
                candidate = attr
                # Add a depth limit to avoid infinite loops with malformed __wrapped__
                for _ in range(100):
                    wrapped = getattr(candidate, "__wrapped__", None)
                    if wrapped is None:
                        break
                    candidate = wrapped

                if isinstance(candidate, cached_property):
                    cached_names.add(name)

        return frozenset(cached_names)


    def _get_cached_values_status(self) -> dict[str, bool]:
        """Get the status of all cached properties.

        Returns:
            Dictionary mapping property names to whether they are currently cached.

        Note:
            Standard functools.cached_property requires __dict__ to function.
            If the instance has no __dict__, properties are considered not cached.
        """
        self._ensure_cache_storage_supported()

        return {name: name in self.__dict__
            for name in self._all_cached_properties_names}


    def _invalidate_cache(self) -> None:
        """Invalidate cached values for all cached properties.

        Clears the cached values for every attribute identified by
        `all_cached_properties_names`. This forces re-computation on next access.
        """
        self._ensure_cache_storage_supported()

        # Only delete attributes that are actually currently cached
        # This avoids the overhead of try/except AttributeError loops
        vars_dict = self.__dict__
        cached_names = self._all_cached_properties_names

        keys_to_delete = [k for k in vars_dict if k in cached_names]

        for name in keys_to_delete:
            # Directly delete from __dict__.
            # This is cleaner for a cache mechanism and avoids triggering
            # custom __delattr__ logic defined in subclasses.
            if name in vars_dict:
                del vars_dict[name]
