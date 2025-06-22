from __future__ import annotations

from abc import abstractmethod
from typing import Optional, Callable, Any, Type

import pandas as pd
from persidict import PersiDict, SafeStrTuple, replace_unsafe_chars, DELETE_CURRENT
from persidict import KEEP_CURRENT, Joker

from .. import BasicPortal
from .._010_basic_portals import get_active_portal, get_nonactive_portals
from .._820_strings_signatures_converters import get_hash_signature

from .._010_basic_portals.basic_portal_class_OLD import (
    _describe_persistent_characteristic
    , _describe_runtime_characteristic)
from .._020_ordinary_code_portals import (
    get_normalized_function_source
    ,OrdinaryCodePortal
    ,OrdinaryFn)
from .._800_persidict_extensions.first_write_once_dict import WriteOnceDict

TOTAL_VALUES_TXT = "Values, total"
PROBABILITY_OF_CHECKS_TXT = "Probability of checks"


class DataPortal(OrdinaryCodePortal):
    """A portal that persistently stores values.

    Values are accessible via their hash_address-es,
    which are unique identifiers of the values.

    If the current portal does not contain a specific value,
    referenced by a hash_address, but this value can be retrieved
    from another portal known to the program,
    the value will be automatically copied to the current portal.

    A portal can serve as a context manager, enabling the use of the
    'with' statement to support portal-aware code blocks. If some code is
    supposed to explicitly read anything from a portal, it should be wrapped
    in a 'with' statement that marks the portal as the current.
    """

    _value_store: WriteOnceDict | None
    _config_settings: PersiDict | None
    _config_settings_cache: dict

    _ephemeral_config_params_at_init: dict[str, Any] | None

    def __init__(self
            , root_dict: PersiDict|str|None = None
            , p_consistency_checks: float|Joker = KEEP_CURRENT
            ):
        OrdinaryCodePortal.__init__(self, root_dict = root_dict)
        del root_dict
        self._ephemeral_config_params_at_init = dict()
        self._config_settings_cache = dict()

        config_settings_prototype = self._root_dict.get_subdict("config_settings")
        config_settings_params = config_settings_prototype.get_params()
        config_settings_params.update(
            digest_len=0, immutable_items=False, file_type="pkl")
        config_settings = type(self._root_dict)(**config_settings_params)
        self._config_settings = config_settings

        if not (isinstance(p_consistency_checks, Joker)
                or 0 <= p_consistency_checks <= 1):
            raise ValueError("p_consistency_checks must be a float in [0,1] "
                +f"or a Joker, but got {p_consistency_checks}")

        self._ephemeral_config_params_at_init["p_consistency_checks"
            ] = p_consistency_checks

        value_store_prototype = self._root_dict.get_subdict("value_store")
        value_store_params = value_store_prototype.get_params()
        value_store_params.update(
            digest_len=0, immutable_items=True, file_type = "pkl")
        value_store = type(self._root_dict)(**value_store_params)
        value_store = WriteOnceDict(value_store, 0)
        self._value_store = value_store


    def _persist_initial_config_params(self) -> None:
        for key, value in self._ephemeral_config_params_at_init.items():
            self._set_config_setting(key, value)


    def _post_init_hook(self) -> None:
        """Hook to be called after all __init__ methods are done"""
        super()._post_init_hook()
        self._persist_initial_config_params()
        self._value_store.p_consistency_checks = self.p_consistency_checks



    def get_params(self) -> dict:
        """Get the portal's configuration parameters"""
        params = super().get_params()
        params.update(self._ephemeral_config_params_at_init)
        sorted_params = dict(sorted(params.items()))
        return sorted_params


    @property
    def _ephemeral_param_names(self) -> set[str]:
        names = super()._ephemeral_param_names
        names.update(self._ephemeral_config_params_at_init)
        return names


    def _update_from_twin(self, other: DataPortal) -> None:
        super()._update_from_twin(other)
        self._value_store = other._value_store
        self._config_settings = other._config_settings
        self._config_settings_cache = other._config_settings_cache


    def _get_config_setting(self, key: SafeStrTuple|str) -> Any:
        """Get a configuration setting from the portal's config store"""
        if not isinstance(key, (str,SafeStrTuple)):
            raise TypeError("key must be a SafeStrTuple or a string")

        if key in self._config_settings_cache:
            value = self._config_settings_cache[key]
        elif key in self._config_settings:
            value = self._config_settings[key]
            self._config_settings_cache[key] = value
        else:
            value = None
            self._config_settings_cache[key] = None
        return value


    def _set_config_setting(self, key: SafeStrTuple|str, value: Any) -> None:
        """Set a configuration setting in the portal's config store"""
        if not isinstance(key, (str,SafeStrTuple)):
            raise TypeError("key must be a SafeStrTuple or a string")

        if value is KEEP_CURRENT:
            return

        self._config_settings[key] = value
        self._config_settings_cache[key] = value

        if value is DELETE_CURRENT:
            del self._config_settings_cache[key]


    def _invalidate_cache(self):
        """Invalidate the portal's cache"""
        super()._invalidate_cache()
        self._config_settings_cache = dict()


    def describe(self) -> pd.DataFrame:
        """Get a DataFrame describing the portal's current state"""
        all_params = [super().describe()]

        all_params.append(_describe_persistent_characteristic(
            TOTAL_VALUES_TXT, len(self._value_store)))
        all_params.append(_describe_runtime_characteristic(
            PROBABILITY_OF_CHECKS_TXT, self.p_consistency_checks))

        result = pd.concat(all_params)
        result.reset_index(drop=True, inplace=True)
        return result


    @property
    def p_consistency_checks(self) -> float|None:
        p = self._get_config_setting("p_consistency_checks")
        if p is None:
            p = 0.0
        return p


    def _clear(self) -> None:
        """Clear the portal's state"""
        self._value_store = None
        self._config_settings = None
        self._ephemeral_config_params_at_init = None
        self._invalidate_cache()
        super()._clear()


class StorableFn(OrdinaryFn):

    _addr_cache: ValueAddr
    _ephemeral_config_params_at_init: dict[str, Any] | None

    def __init__(self
        , fn: Callable | str
        , portal: DataPortal | None = None
        ):
        OrdinaryFn.__init__(self, fn=fn, portal=portal)
        self._ephemeral_config_params_at_init = dict()


    def _post_init_hook(self):
        super()._post_init_hook()
        portal_to_use = self._linked_portal
        if portal_to_use is None:
            portal_to_use = get_active_portal()
        self._persist_initial_config_params(portal_to_use)
        self._visited_portals.add(portal_to_use._str_id)


    def _persist_initial_config_params(self, portal:DataPortal) -> None:
        for key, value in self._ephemeral_config_params_at_init.items():
            self._set_config_setting(key, value, portal)


    def _first_visit_to_portal(self, portal: BasicPortal) -> None:
        self._persist_initial_config_params(portal)


    @property
    def portal(self) -> DataPortal:
        return OrdinaryFn.portal.__get__(self)


    @portal.setter
    def portal(self, new_portal: DataPortal) -> None:
        if not isinstance(new_portal, DataPortal):
            raise TypeError("portal must be a DataPortal instance")
        OrdinaryFn.portal.__set__(self, new_portal)


    def _get_config_setting(self, key: SafeStrTuple, portal:DataPortal) -> Any:
        if not isinstance(key, (str,SafeStrTuple)):
            raise TypeError("key must be a SafeStrTuple or a string")

        portal_wide_value = portal._get_config_setting(key)
        if portal_wide_value is not None:
            return portal_wide_value

        function_specific_value = portal._get_config_setting(
            self.addr + key)

        return function_specific_value


    def _set_config_setting(self
            , key: SafeStrTuple|str
            , value: Any
            , portal:DataPortal) -> None:
        if not isinstance(key, (SafeStrTuple, str)):
            raise TypeError("key must be a SafeStrTuple or a string")
        portal._set_config_setting(ValueAddr(self) + key, value)


    @property
    def addr(self) -> ValueAddr:
        with self.portal:
            if not hasattr(self, "_addr_cache") or self._addr_cache is None:
                self._addr_cache = ValueAddr(self)
            return self._addr_cache


    def _invalidate_cache(self):
        if hasattr(self, "_addr_cache"):
            del self._addr_cache
        super()._invalidate_cache()


    def __setstate__(self, state):
        super().__setstate__(state)
        if not state["_source_code"] == get_normalized_function_source(
            state["_source_code"]):
            raise ValueError("Source code is not normalized. ")
        self._ephemeral_config_params_at_init = dict()


    def __getstate__(self):
        return super().__getstate__()


class HashAddr(SafeStrTuple):
    """A globally unique hash-based address of an object.

    Two objects with exactly the same type and value will always have
    exactly the same HashAddr-es.

    A HashAddr consists of 2 components: a prefix, and a hash.
    A prefix contains human-readable information about an object's type.
    A hash string contains the object's hash signature. It may begin with
    an optional descriptor, which provides additional human-readable
    information about the object's structure / value.
    """

    def __init__(self, prefix:str
                 , hash_signature:str):
        if not isinstance(prefix, str) or not isinstance(hash_signature, str):
            raise TypeError("prefix and hash_signature must be strings")
        if len(prefix) == 0 or len(hash_signature) == 0:
            raise ValueError("prefix and hash_signature must not be empty")
        SafeStrTuple.__init__(self,prefix,hash_signature)


    @property
    def prefix(self) -> str:
        return self.strings[0]

    @property
    def hash_signature(self) -> str:
        return self.strings[1]

    @staticmethod
    def _build_prefix(x: Any) -> str:
        """Create a short human-readable summary of an object."""

        if (hasattr(x, "__hash_signature_prefix__")
                and callable(x.__hash_signature_prefix__)):
            prfx = x.__hash_signature_prefix__()
        else:
            prfx = x.__class__.__name__.lower()

        return prfx


    @staticmethod
    def _build_hash_signature(x: Any) -> str:
        """Create a URL-safe hashdigest for an object."""

        if (hasattr(x, "shape") and hasattr(x.shape, "__iter__")
                and callable(x.shape.__iter__) and not callable(x.shape)):
            descriptor, connector = "shape_", "_x_"
            for n in x.shape:
                descriptor += str(n) + connector
            descriptor = descriptor[:-len(connector)] + "_"
        elif hasattr(x, "__len__") and callable(x.__len__):
            descriptor = "len_" + str(len(x)) + "_"
        else:
            descriptor = ""

        descriptor = replace_unsafe_chars(descriptor, replace_with="_")
        raw_hash_signature = get_hash_signature(x)
        hash_signature = descriptor + raw_hash_signature

        return hash_signature


    @classmethod
    def from_strings(cls, *
                     , prefix:str
                     , hash_signature:str
                     , assert_readiness:bool=True
                     ) -> HashAddr:
        """(Re)construct address from text representations of prefix and hash"""

        if not isinstance(prefix, str) or not isinstance(hash_signature, str):
            raise TypeError("prefix and hash_signature must be strings")

        if len(prefix) == 0 or len(hash_signature) == 0:
            raise ValueError("prefix and hash_signature must not be empty")

        address = cls.__new__(cls)
        super(cls, address).__init__(prefix, hash_signature)
        if assert_readiness:
            if not address.ready:
                raise ValueError("Address is not ready for retrieving data")
        return address


    @property
    @abstractmethod
    def ready(self) -> bool:
        """Check if address points to a value that is ready to be retrieved."""
        # TODO: decide whether we need .ready() at the base class
        raise NotImplementedError


    @abstractmethod
    def get(self, timeout:Optional[int] = None, expected_type:Type[T]= Any) -> T:
        """Retrieve value, referenced by the address"""
        raise NotImplementedError


    def __eq__(self, other) -> bool:
        """Return self==other. """
        return type(self) == type(other) and self.strings == other.strings


    def __ne__(self, other) -> bool:
        """Return self!=other. """
        return not (self == other)


    def _invalidate_cache(self):
        pass


class ValueAddr(HashAddr):
    """A globally unique address of an immutable value.

    ValueAddr is a universal global identifier of any (constant) value.
    Using only the value's hash should (theoretically) be enough to
    uniquely address all possible data objects that the humanity  will create
    in the foreseeable future (see, for example ipfs.io).

    However, an address also includes a prefix and an optional descriptor.
    It makes it easier for humans to interpret an address,
    and further decreases collision risk.
    """
    _containing_portals_cache: set[str]
    _value_cache: Any

    def __init__(self, data: Any):

        if hasattr(data, "get_ValueAddr"):
            data_value_addr = data.get_ValueAddr()
            prefix = data_value_addr.prefix
            hash_signature = data_value_addr.hash_signature
            HashAddr.__init__(self
                , prefix=prefix
                , hash_signature=hash_signature)
            return

        assert not isinstance(data, HashAddr), (
                "get_ValueAddr is the only way to "
                + "convert HashAddr into ValueAddr")

        prefix = self._build_prefix(data)
        hash_signature = self._build_hash_signature(data)
        HashAddr.__init__(self
            , prefix=prefix
            , hash_signature=hash_signature)

        portal = get_active_portal()
        portal._value_store[self] = data
        self._value_cache = data
        self._containing_portals_cache = set()
        self._containing_portals_cache.add(portal._str_id)


    def _invalidate_cache(self):
        super()._invalidate_cache()
        if hasattr(self, "_value_cache"):
            del self._value_cache
        if hasattr(self, "_containing_portals_cache"):
            del self._containing_portals_cache


    def get_ValueAddr(self):
        return self


    @property
    def _ready_in_active_portal(self) -> bool:
        portal = get_active_portal()
        portal_id = portal._str_id
        if portal_id in self._containing_portals_cache:
            return True
        result = self in portal._value_store
        if result:
            self._containing_portals_cache.add(portal_id)
        return result


    @property
    def _ready_in_nonactive_portals(self) -> bool:
        for portal in get_nonactive_portals():
            if self in portal._value_store:
                value = portal._value_store[self]
                get_active_portal()._value_store[self] = value
                new_ids = {portal._str_id, get_active_portal()._str_id}
                self._containing_portals_cache |= new_ids
                self._value_cache = value
                return True
        return False


    @property
    def ready(self) -> bool:
        """Check if address points to a value that is ready to be retrieved."""
        if not hasattr(self, "_containing_portals_cache"):
            self._containing_portals_cache = set()

        if self._ready_in_active_portal:
            return True
        if self._ready_in_nonactive_portals:
            return True
        return False


    def _get_from_active_portal(self) -> Any:
        """Retrieve value, referenced by the address, from the current portal"""

        if hasattr(self, "_value_cache"):
            if get_active_portal()._str_id in self._containing_portals_cache:
                return self._value_cache
            else:
                get_active_portal()._value_store[self] = self._value_cache
                self._containing_portals_cache |= {get_active_portal()._str_id}
                return self._value_cache

        value = get_active_portal()._value_store[self]
        self._value_cache = value
        self._containing_portals_cache |= {get_active_portal()._str_id}
        return value


    def _get_from_nonactive_portals(self) -> Any:
        """Retrieve value, referenced by the address, from noncurrent portals"""

        for portal in get_nonactive_portals():
            try:
                value = portal._value_store[self]
                get_active_portal()._value_store[self] = value
                self._value_cache = value
                new_ids = {portal._str_id, get_active_portal()._str_id}
                self._containing_portals_cache |= new_ids
                return value
            except:
                continue

        raise KeyError(f"ValueAddr {self} not found in any portal")


    def get(self
            , timeout:int|None = None
            , expected_type:Type[T]= Any
            ) -> T:
        """Retrieve value, referenced by the address from any available portal"""

        if not hasattr(self, "_containing_portals_cache"):
            self._containing_portals_cache = set()

        try:
            result = self._get_from_active_portal()
        except:
            result = self._get_from_nonactive_portals()

        if not (expected_type is Any or expected_type is object):
            if not isinstance(result, expected_type):
                raise TypeError(f"Expected type {expected_type}, "
                    +f"but got {type(result)}")
        return result


    def __getstate__(self):
        state = dict(strings=self.strings)
        return state


    def __setstate__(self, state):
        self._invalidate_cache()
        self.strings = state["strings"]