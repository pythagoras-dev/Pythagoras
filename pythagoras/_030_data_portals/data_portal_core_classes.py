from __future__ import annotations

import random
from abc import ABC, abstractmethod
from typing import Optional, Callable, Any, Type

import pandas as pd
from persidict import PersiDict, SafeStrTuple, replace_unsafe_chars
from sympy.stats import Probability

from pythagoras._010_basic_portals.portal_aware_dict import PortalAwareDict
from pythagoras._020_ordinary_code_portals import get_normalized_function_source
from pythagoras._820_strings_signatures_converters import get_hash_signature
from pythagoras._010_basic_portals import PortalAwareClass
from pythagoras._010_basic_portals.portal_aware_classes import (
    _noncurrent_portals, find_portal_to_use)

from pythagoras._010_basic_portals.basic_portal_core_classes import (
    PortalType, _describe_persistent_characteristic
    , _describe_runtime_characteristic)
from pythagoras._020_ordinary_code_portals import (
    OrdinaryCodePortal, OrdinaryFn)
from pythagoras._800_persidict_extensions.first_entry_dict import FirstEntryDict

TOTAL_VALUES_TXT = "Values, total"
PROBABILITY_OF_CHECKS_TXT = "Probability of checks"

class DataPortal(OrdinaryCodePortal):
    """A portal that persistently stores values.

    Values are accessible via their hash_address-es,
    which are unique identifiers of the values.

    If the current portal does not contain a specific value,
    referenced by a hash_address, but this value can be retrieved
    from another portal, the value will be automatically copied
    to the current portal.

    A portal can serve as a context manager, enabling the use of the
    'with' statement to support portal-aware code blocks. If some code is
    supposed to explicitly read anything from a portal, it should be wrapped
    in a 'with' statement that marks the portal as the current.
    """

    value_store: PortalAwareDict|None
    config_store: PortalAwareDict|None
    _p_consistency_checks: float|None

    def __init__(self
            , root_dict:PersiDict|str|None = None
            , p_consistency_checks: float | None = None
            ):
        super().__init__(root_dict = root_dict)
        del root_dict

        assert p_consistency_checks is None or 0 <= p_consistency_checks <= 1
        if p_consistency_checks is None:
            p_consistency_checks = 0
        self._p_consistency_checks = p_consistency_checks

        value_store_prototype = self._root_dict.get_subdict("value_store")
        value_store_params = value_store_prototype.get_params()
        value_store_params.update(
            digest_len=0, immutable_items=True, file_type = "pkl")
        value_store = type(self._root_dict)(**value_store_params)
        value_store = FirstEntryDict(value_store, p_consistency_checks)
        value_store = PortalAwareDict(value_store, portal=self)
        self.value_store = value_store

        config_store_prototype = self._root_dict.get_subdict("config_store")
        config_store_params = config_store_prototype.get_params()
        config_store_params.update(
            digest_len=0, immutable_items=False, file_type = "pkl")
        config_store = type(self._root_dict)(**config_store_params)
        config_store = PortalAwareDict(config_store, portal=self)
        self.config_store = config_store


    def get_params(self) -> dict:
        """Get the portal's configuration parameters"""
        params = super().get_params()
        params["p_consistency_checks"] = self.p_consistency_checks
        return params


    def describe(self) -> pd.DataFrame:
        """Get a DataFrame describing the portal's current state"""
        all_params = [super().describe()]

        all_params.append(_describe_persistent_characteristic(
            TOTAL_VALUES_TXT, len(self.value_store)))
        all_params.append(_describe_runtime_characteristic(
            PROBABILITY_OF_CHECKS_TXT, self._p_consistency_checks))

        result = pd.concat(all_params)
        result.reset_index(drop=True, inplace=True)
        return result


    @property
    def p_consistency_checks(self) -> float|None:
        return self._p_consistency_checks


    def _clear(self) -> None:
        """Clear the portal's state"""
        self.value_store = None
        self.config_store = None
        self._p_consistency_checks = 0
        super()._clear()


class StorableFn(OrdinaryFn):

    _addr: ValueAddr

    def __init__(self
        , fn: Callable | str
        , portal: DataPortal | None = None
        ):
        OrdinaryFn.__init__(self, fn=fn, portal=portal)


    @property
    def addr(self) -> ValueAddr:
        if not hasattr(self, "_addr") or self._addr is None:
            self._addr = ValueAddr(self, portal=self.portal)
        return self._addr


    def _invalidate_cache(self):
        if hasattr(self, "_addr"):
            del self._addr
        super()._invalidate_cache()


    def __setstate__(self, state):
        self._invalidate_cache()
        super().__setstate__(state)
        assert state["_source_code"] == get_normalized_function_source(
            state["_source_code"])

    def __getstate__(self):
        return super().__getstate__()



class HashAddr(SafeStrTuple, PortalAwareClass):
    """A globally unique hash-based address of an object.

    Two objects with exactly the same type and value will always have
    exactly the same HashAddr-es.

    A HashAddr consists of 2 strings: a prefix, and a hash.
    A prefix contains human-readable information about an object's type.
    A hash string contains the object's hash signature. It may begin with
    an optional descriptor, which provides additional human-readable
    information about the object's structure / value.
    """

    def __init__(self, *args, portal:Optional[DataPortal]=None,**kwargs):
        PortalAwareClass.__init__(self, portal=portal)
        SafeStrTuple.__init__(self,*args, **kwargs)


    @property
    def prefix(self) -> str:
        return self.str_chain[0]

    @property
    def hash_signature(self) -> str:
        return self.str_chain[1]

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
                     , portal:Optional[DataPortal] = None
                     ) -> HashAddr:
        """(Re)construct address from text representations of prefix and hash"""

        assert prefix, "prefix must be a non-empty string"
        assert hash_signature, "hash_signature must be a non-empty string"

        address = cls.__new__(cls)
        super(cls, address).__init__(prefix, hash_signature, portal=portal)
        if assert_readiness:
            assert address.ready
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
        return type(self) == type(other) and self.str_chain == other.str_chain

    def __ne__(self, other) -> bool:
        """Return self!=other. """
        return not (self == other)


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
    _ready: bool
    _value: Any

    def __init__(
            self
            , data: Any
            , portal:DataPortal|None):

        portal = find_portal_to_use(suggested_portal=portal)

        if hasattr(data, "get_ValueAddr"):
            data_value_addr = data.get_ValueAddr()
            prefix = data_value_addr.prefix
            hash_signature = data_value_addr.hash_signature
            super().__init__(prefix, hash_signature, portal=portal)
            ##################### REWRITE !!!! #####################
            if portal != data_value_addr.portal and (
                    data_value_addr.portal is not None) and (
                    not self in portal.value_store):
                data = data_value_addr.get()
                portal.value_store[self] = data
                self._ready = True
            ##################### REWRITE !!!! #####################
            return

        assert not isinstance(data, HashAddr), (
                "get_ValueAddr is the only way to "
                + "convert HashAddr into ValueAddr")

        prefix = self._build_prefix(data)
        hash_signature = self._build_hash_signature(data)
        super().__init__(prefix, hash_signature, portal=portal)

        portal.value_store[self] = data
        self._value = data
        self._ready = True


    def _invalidate_cache(self):
        super()._invalidate_cache()
        if hasattr(self, "_value"):
            del self._value
        if hasattr(self, "_ready"):
            del self._ready


    def get_ValueAddr(self):
        return self


    # @property
    # def portal(self) -> DataPortal:
    #     return self._portal_typed(expected_type=DataPortal)


    @property
    def _ready_in_current_portal(self) -> bool:
        with self.finally_bound_portal:
            if not hasattr(self, "_ready"):
                result = self in self.portal.value_store
                if result:
                    self._ready = True
                return result
            assert self._ready
            return True


    @property
    def _ready_in_noncurrent_portals(self) -> bool:
        for portal in _noncurrent_portals(expected_type=DataPortal):
            with portal:
                if self in portal.value_store:
                    data = portal.value_store[self]
                    with self.portal:
                        self.portal.value_store[self] = data
                    self._ready = True
                    return True
        return False


    @property
    def ready(self) -> bool:
        """Check if address points to a value that is ready to be retrieved."""
        if hasattr(self, "_ready"):
            assert self._ready
            return True
        if self._ready_in_current_portal:
            self._ready = True
            return True
        if self._ready_in_noncurrent_portals:
            self._ready = True
            return True
        return False


    def _get_from_current_portal(self, timeout:Optional[int] = None) -> Any:
        """Retrieve value, referenced by the address, from the current portal"""

        if hasattr(self, "_value"):
            return self._value

        with self.finally_bound_portal:
            result = self.portal.value_store[self]
            self._value = result
            return result


    def _get_from_noncurrent_portals(self, timeout:Optional[int] = None) -> Any:
        """Retrieve value, referenced by the address, from noncurrent portals"""
        for portal in _noncurrent_portals(expected_type=DataPortal):
            try:
                with portal:
                    result = portal.value_store[self]
                with self.portal:
                    self.portal.value_store[self] = result
                self._value = result
                return result
            except:
                continue

        raise KeyError(f"ValueAddr {self} not found in any portal")

    def get(self
            , timeout:Optional[int] = None
            , expected_type:Type[T]= Any
            ) -> T:
        """Retrieve value, referenced by the address from any available portal"""

        if hasattr(self, "_value"):
            result = self._value
        else:
            try:
                result = self._get_from_current_portal(timeout)
            except:
                result = self._get_from_noncurrent_portals(timeout)
        if not (expected_type is Any or expected_type is object):
            if not isinstance(result, expected_type):
                raise TypeError(f"Expected type {expected_type}, "
                    +f"but got {type(result)}")
        return result


    def __getstate__(self):
        state = dict(str_chain=self.str_chain)
        return state


    def __setstate__(self, state):
        self.str_chain = state["str_chain"]
        self._portal = None