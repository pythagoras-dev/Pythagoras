from functools import cached_property


class CacheableMixin:
    @property
    def all_cached_properties_names(self) -> set[str]:
        """
        Collect names of all attributes that are declared as
        `functools.cached_property` in the current class hierarchy.

        Returns
        -------
        set[str]
            A set containing the attribute names of every cached_property
            defined on this class or any of its parent classes.
        """
        cached_names: set[str] = set()
        # Walk through the MRO so that parents are included as well.
        for cls in type(self).mro():
            for name, attr in cls.__dict__.items():
                if isinstance(attr, cached_property):
                    cached_names.add(name)
        return cached_names

    def _invalidate_cache(self):
        """
        Invalidates cached values for all @cached_property properties
        in this class and its descendants.
        """
        # Remove stored computed values for every cached_property, if present
        for name in self.all_cached_properties_names:
            # Using pop with default avoids KeyError if the property hasn't been accessed yet
            self.__dict__.pop(name, None)