from __future__ import annotations

from typing import Any

from persidict import PersiDict

from persidict.persi_dict import PersiDictKey

from .. import BasicPortal, PortalAwareClass


class PortalAwareDict(PersiDict):
    """A dictionary that allows its values to be portal-aware.

    The class is a wrapper around a PersiDict object.
    When a value is retrieved from the dictionary, and the value is a
    PortalAwareClass object, the dictionary sets the portal attribute
    of the object to the current portal.
    """

    _portal: BasicPortal
    _wrapped_dict: PersiDict


    def __init__(self
                 , wrapped_dict:PersiDict
                 , portal: BasicPortal):
        assert isinstance(wrapped_dict, PersiDict)
        self._wrapped_dict = wrapped_dict
        assert isinstance(portal, BasicPortal)
        self._portal = portal

        PersiDict.__init__(self
            , base_class_for_values=wrapped_dict.base_class_for_values
            , immutable_items=wrapped_dict.immutable_items
            , digest_len=wrapped_dict.digest_len)


    def __getitem__(self, key: PersiDictKey) -> Any:
        with self._portal:
            item = self._wrapped_dict[key]
            if isinstance(item, PortalAwareClass):
                item.portal = self._portal
            return item

    def __setitem__(self, key: PersiDictKey, value: Any):
        with self._portal:
            self._wrapped_dict[key] = value

    def __contains__(self, item):
        with self._portal:
            return item in self._wrapped_dict

    def __len__(self):
        with self._portal:
            return len(self._wrapped_dict)

    def _generic_iter(self, iter_type: str):
        with self._portal:
            return self._wrapped_dict._generic_iter(iter_type)

    def timestamp(self, key:PersiDictKey) -> float:
        with self._portal:
            return self._wrapped_dict.timestamp(key)

    def __getattr__(self, name):
        # Forward attribute access to the wrapped object
        return getattr(self._wrapped_dict, name)

    def get_subdict(self, prefix_key:PersiDictKey) -> PortalAwareDict:
        subdict = self._wrapped_dict.get_subdict(prefix_key)
        result = PortalAwareDict(subdict, portal = self._portal)
        return result

    @property
    def base_dir(self):
        return self._wrapped_dict.base_dir

    @property
    def base_url(self):
        return self._wrapped_dict.base_url
