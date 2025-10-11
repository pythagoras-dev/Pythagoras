from __future__ import annotations

from .._010_basic_portals import get_active_portal
from .._010_basic_portals.basic_portal_core_classes import _visit_portal
from .._030_data_portals import DataPortal, ValueAddr
from parameterizable import sort_dict_by_keys

class KwArgs(dict):
    """Container for keyword arguments with deterministic ordering and packing.

    Provides utilities to sort keys deterministically and to pack/unpack values
    to and from ValueAddr instances so that argument sets can be compared and
    hashed reliably across runs.
    """


    def __init__(self, *args, **kargs):
        """Create a KwArgs mapping with deterministically sorted keys.

        Args:
            *args: Positional arguments accepted by dict().
            **kargs: Keyword arguments accepted by dict().
        """
        dict.__init__(self)
        tmp_dict = dict(*args, **kargs)
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


    def __setitem__(self, key, value):
        """Set an item enforcing KwArgs invariants.

        Enforces that keys are strings and values are not KwArgs themselves.

        Args:
            key: The key to set; must be a str.
            value: The value to associate with the key.

        Raises:
            KeyError: If the key is not a string.
            ValueError: If the value is a KwArgs (nested KwArgs are disallowed).
        """
        if not isinstance(key, str):
            raise KeyError("Keys must be strings in KwArgs.")
        if isinstance(value, KwArgs):
            raise ValueError("Nested KwArgs are not allowed.")
        super().__setitem__(key, value)


    def __reduce__(self):
        """Support pickling by sorting keys first for stable serialization.

        Returns:
            tuple: Standard pickle reduce tuple from dict.__reduce__().
        """
        self.sort(inplace=True)
        return super().__reduce__()


    def unpack(self) -> UnpackedKwArgs:
        """Return a copy with all ValueAddr values resolved to raw values.

        Returns:
            UnpackedKwArgs: A new mapping where each ValueAddr is replaced with
            its underlying value via ValueAddr.get().
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
        """Pack values into ValueAddr handles, optionally storing them.

        Each argument value is replaced by a ValueAddr pointing to either the
        stored value (when store=True) or a non-stored address (when store=False)
        that can still serve as a stable identifier for hashing/equality.

        Args:
            store: If True, values are stored in the active portal and the
                returned addresses persist across sessions. If False, produces
                non-stored addresses suitable for transient signatures.

        Returns:
            PackedKwArgs: A new mapping with values converted to ValueAddr.
        """
        packed_copy = dict()
        if store:
            portal = get_active_portal()
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
    """KwArgs where all values are ValueAddr instances.

    This is the packed form produced by KwArgs.pack().
    """
    def __init__(self,*args, **kargs):
        """Construct a PackedKwArgs mapping.

        Accepts the same arguments as dict/KwArgs.
        """
        super().__init__(*args, **kargs)


class UnpackedKwArgs(KwArgs):
    """KwArgs where all values are raw (non-ValueAddr) objects.

    This is the unpacked form produced by KwArgs.unpack().
    """
    def __init__(self,*args, **kargs):
        """Construct an UnpackedKwArgs mapping.

        Accepts the same arguments as dict/KwArgs.
        """
        super().__init__(*args, **kargs)