from __future__ import annotations

from .._010_basic_portals import active_portal
from .._030_data_portals import DataPortal, ValueAddr
from .._840_work_with_collections.dict_sort import sort_dict_by_keys

class KwArgs(dict):
    """ A class that encapsulates keyword arguments for a function call.

    It allows to "normalize" the dictionary by sorting the keys
    and replacing values with their hash addresses
    in order to always get the same hash values
    for the same lists of arguments.
    """


    def __init__(self, *args, **kargs):
        dict.__init__(self)
        tmp_dict = dict(*args, **kargs)
        tmp_dict = sort_dict_by_keys(tmp_dict)
        self.update(tmp_dict)


    def sort(self, inplace:bool) -> KwArgs:
        """Sort the keys in the dictionary."""
        if inplace:
            sorted_dict = sort_dict_by_keys(self)
            self.clear()
            self.update(sorted_dict)
            return self
        else:
            return KwArgs(**sort_dict_by_keys(self))


    def __setitem__(self, key, value):
        """Overridden to ensure only string keys are allowed."""
        if not isinstance(key, str):
            raise KeyError("Keys must be strings in KwArgs.")
        if isinstance(value, KwArgs):
            raise ValueError("Nested KwArgs are not allowed.")
        super().__setitem__(key, value)


    def __reduce__(self):
        """ Sort the keys before pickling."""
        self.sort(inplace=True)
        return super().__reduce__()


    def unpack(self) -> UnpackedKwArgs:
        """ Restore values based on their hash addresses."""
        unpacked_copy = dict()
        for k,v in self.items():
            if isinstance(v, ValueAddr):
                unpacked_copy[k] = v.get()
            else:
                unpacked_copy[k] = v
        unpacked_copy = UnpackedKwArgs(**unpacked_copy)
        return unpacked_copy


    def pack(self) -> PackedKwArgs:
        """ Replace values with their hash addresses."""
        portal = active_portal()
        packed_copy = dict()
        with portal:
            for k,v in self.items():
                packed_copy[k] = ValueAddr(v)
        packed_copy = PackedKwArgs(**packed_copy)
        return packed_copy


class PackedKwArgs(KwArgs):
    def __init__(self,*args, **kargs):
        super().__init__(*args, **kargs)


class UnpackedKwArgs(KwArgs):
    def __init__(self,*args, **kargs):
        super().__init__(*args, **kargs)