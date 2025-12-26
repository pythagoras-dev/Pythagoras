from __future__ import annotations

from abc import abstractmethod
from typing import Optional, Callable, Any, Type

from persidict import PersiDict, SafeStrTuple, replace_unsafe_chars, DELETE_CURRENT
from persidict import KEEP_CURRENT, Joker

from .._010_basic_portals import *
# from .._010_basic_portals.basic_portal_accessors import *
from .._800_foundational_utilities import get_hash_signature, get_node_signature

from .._010_basic_portals.basic_portal_core_classes import (
    _describe_persistent_characteristic
    , _describe_runtime_characteristic)
from .._020_ordinary_code_portals import OrdinaryCodePortal ,OrdinaryFn
from persidict import WriteOnceDict

_TOTAL_VALUES_TXT = "Values, total"
_PROBABILITY_OF_CHECKS_TXT = "Probability of consistency checks"


def get_number_of_known_data_portals() -> int:
    """Get the number of known DataPortals.

    Returns:
        The total count of all known portals in the system.

    Raises:
        TypeError: If any known portal is not an instance of DataPortal.
    """
    return get_number_of_known_portals(DataPortal)


def get_all_known_data_portals() -> list[DataPortal]:
    """Get a list of all known DataPortals.

    Returns:
        A list containing all portal instances currently known to the system.

    Raises:
        TypeError: If any known portal is not an instance of DataPortal.
    """
    return get_all_known_portals(DataPortal)


def get_number_of_active_data_portals() -> int:
    """Get the number of unique DataPortals in the active stack.

    Returns:
        The count of unique portals currently in the active portal stack.

    Raises:
        TypeError: If any active portal is not an instance of DataPortal.
    """
    return get_number_of_active_portals(DataPortal)


def get_depth_of_active_data_portal_stack() -> int:
    """Get the depth of the active DataPortal stack.

    Returns:
        The total depth (sum of all counters) of the active portal stack.

    Raises:
        TypeError: If any active portal is not an instance of DataPortal.
    """
    return get_depth_of_active_portal_stack(DataPortal)


def get_current_data_portal() -> DataPortal:
    """Get the current portal object.

    The current portal is the one that was most recently entered
    using the 'with' statement. If no portal is currently active,
    it finds the most recently created portal and makes it active (and current).
    If currently no portals exist in the system,
    it creates the default portal, and makes it active and current.

    Returns:
        The current active DataPortal.

    Raises:
        TypeError: If the current portal is not a DataPortal.
    """
    portal = get_current_portal()
    if not isinstance(portal, DataPortal):
        raise TypeError(f"The current portal is {type(portal).__name__}, "
                           f"but a DataPortal was expected.")
    return portal


def get_nonactive_data_portals() -> list[DataPortal]:
    """Get a list of all DataPortals that are not in the active stack.

    Returns:
        A list of portal instances that are not currently in the active portal stack.

    Raises:
        TypeError: If any non-active portal is not an instance of DataPortal.
    """
    return get_nonactive_portals(DataPortal)


def get_noncurrent_data_portals() -> list[DataPortal]:
    """Get a list of all DataPortals that are not the current portal.

    Returns:
        A list of all known portal instances but the current one.

    Raises:
        TypeError: If any non-current portal is not an instance of DataPortal.
    """
    return get_noncurrent_portals(DataPortal)


class DataPortal(OrdinaryCodePortal):
    """A portal that persistently stores and retrieves immutable values.

    A DataPortal is responsible for addressing, storing, and retrieving
    values by their content-derived addresses. It exposes a context manager
    interface so that code running within a "with portal:" block treats that
    portal as the active one.

    Behavior overview:
    - Content-addressed storage: immutable values are referenced by a
      HashAddr/ValueAddr that is derived from the value's bytes and a
      human-readable descriptor.
    - Transparent fetch and replication: if a value is not present in the
      active portal but exists in any other known portal, it is fetched
      and copied into the active portal on demand.
    - Config settings: portal-specific and function-specific settings are
      persisted in a dedicated config store.
    - Consistency checks: the underlying persistent dictionary can perform
      random, probabilistic consistency checks controlled by the
      p_consistency_checks parameter.

    Note:
        Use the portal as a context manager whenever code performs I/O with
        the portal (reading or storing values):

        with portal:
            addr = ValueAddr(data)
            value = addr.get()

    """

    _value_store: WriteOnceDict | None
    _portal_config_settings: PersiDict | None
    _portal_config_settings_cache: dict

    _auxiliary_config_params_at_init: dict[str, Any] | None

    def __init__(self
            , root_dict: PersiDict|str|None = None
            , p_consistency_checks: float|Joker = KEEP_CURRENT
            ):
        """Initialize a DataPortal.

        Args:
            root_dict: Prototype PersiDict or a path/URI used to create
                a persistent dictionary for internal stores. If None, uses
                the parent's default.
            p_consistency_checks: Probability in [0, 1] or KEEP_CURRENT Joker
                that controls random consistency checks of the value store.

        Raises:
            ValueError: If p_consistency_checks is not in [0, 1] and not a Joker.
        """
        OrdinaryCodePortal.__init__(self, root_dict = root_dict)
        del root_dict
        self._auxiliary_config_params_at_init = dict()
        self._portal_config_settings_cache = dict()

        portal_config_settings_prototype = self._root_dict.get_subdict("portal_cfg")
        portal_config_settings_params = portal_config_settings_prototype.get_params()
        portal_config_settings_params.update(
            digest_len=0, append_only=False, serialization_format="pkl")
        portal_config_settings = type(self._root_dict)(**portal_config_settings_params)
        self._portal_config_settings = portal_config_settings

        if not (isinstance(p_consistency_checks, Joker)
                or 0 <= p_consistency_checks <= 1):
            raise ValueError("p_consistency_checks must be a float in [0,1] "
                +f"or a Joker, but got {p_consistency_checks}")

        self._auxiliary_config_params_at_init["p_consistency_checks"
            ] = p_consistency_checks

        node_config_prototype = self._root_dict.get_subdict("node_cfg")
        node_config_prototype = (
            node_config_prototype.get_subdict(get_node_signature()[:8])                              )
        node_config_params = node_config_prototype.get_params()
        node_config_params.update(
            digest_len=0, append_only=False, serialization_format="pkl")
        node_config_settings = type(self._root_dict)(**node_config_params)
        self._node_config_settings = node_config_settings


        #TODO: refactor
        self._local_node_store = node_config_settings

        value_store_prototype = self._root_dict.get_subdict("value_store")
        value_store_params = value_store_prototype.get_params()
        value_store_params.update(
            digest_len=0, append_only=True, serialization_format = "pkl")
        value_store = type(self._root_dict)(**value_store_params)
        value_store = WriteOnceDict(value_store, 0)
        self._value_store = value_store


    def _persist_initial_config_params(self) -> None:
        for key, value in self._auxiliary_config_params_at_init.items():
            self._set_portal_config_setting(key, value)


    def __post_init__(self) -> None:
        """Finalize initialization after __init__ completes across the MRO.

        Ensures that auxiliary configuration parameters are persisted and that
        the value store is configured according to the portal's
        p_consistency_checks setting.
        """
        super().__post_init__()
        self._persist_initial_config_params()
        self._value_store.p_consistency_checks = self.p_consistency_checks


    def get_params(self) -> dict:
        """Return the portal's configuration parameters.

        Returns:
            dict: A sorted dictionary of base parameters augmented with
            auxiliary config entries defined at initialization.
        """
        params = super().get_params()
        params.update(self._auxiliary_config_params_at_init)
        sorted_params = sort_dict_by_keys(params)
        return sorted_params


    @property
    def auxiliary_param_names(self) -> set[str]:
        names = super().auxiliary_param_names
        names.update(self._auxiliary_config_params_at_init)
        return names


    def _get_portal_config_setting(self, key: SafeStrTuple | str) -> Any:
        """Get a configuration setting from the portal's config store"""
        if not isinstance(key, (str,SafeStrTuple)):
            raise TypeError("key must be a SafeStrTuple or a string")

        if key in self._portal_config_settings_cache:
            value = self._portal_config_settings_cache[key]
        elif key in self._portal_config_settings:
            value = self._portal_config_settings[key]
            self._portal_config_settings_cache[key] = value
        else:
            value = None
            self._portal_config_settings_cache[key] = None
        return value


    def _set_portal_config_setting(self, key: SafeStrTuple | str, value: Any) -> None:
        """Set a configuration setting in the portal's config store"""
        if not isinstance(key, (str,SafeStrTuple)):
            raise TypeError("key must be a SafeStrTuple or a string")

        if value is KEEP_CURRENT:
            return

        self._portal_config_settings[key] = value
        self._portal_config_settings_cache[key] = value

        if value is DELETE_CURRENT:
            del self._portal_config_settings_cache[key]


    def _invalidate_cache(self):
        """Invalidate the portal's cache"""
        super()._invalidate_cache()
        self._portal_config_settings_cache = dict()


    def describe(self) -> pd.DataFrame:
        """Get a DataFrame describing the portal's current state"""
        all_params = [super().describe()]

        all_params.append(_describe_persistent_characteristic(
            _TOTAL_VALUES_TXT, len(self._value_store)))
        all_params.append(_describe_runtime_characteristic(
            _PROBABILITY_OF_CHECKS_TXT, self.p_consistency_checks))

        result = pd.concat(all_params)
        result.reset_index(drop=True, inplace=True)
        return result


    @property
    def p_consistency_checks(self) -> float|None:
        p = self._get_portal_config_setting("p_consistency_checks")
        if p is None:
            p = 0.0
        return p


    def _clear(self) -> None:
        """Clear the portal's state.

        The portal must not be used after this method is called.
        """
        super()._clear()
        self._auxiliary_config_params_at_init = None
        self._value_store = None
        self._portal_config_settings = None


class StorableFn(OrdinaryFn):
    """An ordinary function that can be persistently stored in a DataPortal."""

    _addr_cache: ValueAddr
    _auxiliary_config_params_at_init: dict[str, Any] | None

    def __init__(self
        , fn: Callable | str
        , portal: DataPortal | None = None
        ):
        """Create a storable wrapper around an ordinary function.

        Args:
            fn: A Python function or its source code (normalized) as a string.
            portal: Optional DataPortal to bind the function to.
        """
        OrdinaryFn.__init__(self, fn=fn, portal=portal)
        self._auxiliary_config_params_at_init = dict()


    def _first_visit_to_portal(self, portal: DataPortal) -> None:
        super()._first_visit_to_portal(portal)
        self._persist_initial_config_params(portal)
        with portal:
            _ = ValueAddr(self)


    def _persist_initial_config_params(self, portal:DataPortal) -> None:
        for key, value in self._auxiliary_config_params_at_init.items():
            self._set_config_setting(key, value, portal)


    @property
    def portal(self) -> DataPortal:
        return super().portal


    def _get_config_setting(self, key: SafeStrTuple, portal:DataPortal) -> Any:
        if not isinstance(key, (str,SafeStrTuple)):
            raise TypeError("key must be a SafeStrTuple or a string")

        portal_wide_value = portal._get_portal_config_setting(key)
        if portal_wide_value is not None:
            return portal_wide_value

        function_specific_value = portal._get_portal_config_setting(
            self.addr + key)

        return function_specific_value


    def _set_config_setting(self
            , key: SafeStrTuple|str
            , value: Any
            , portal:DataPortal) -> None:
        if not isinstance(key, (SafeStrTuple, str)):
            raise TypeError("key must be a SafeStrTuple or a string")
        portal._set_portal_config_setting(ValueAddr(self) + key, value)


    @property
    def addr(self) -> ValueAddr:
        if not hasattr(self, "_addr_cache"):
            with self.portal:
                self._addr_cache = ValueAddr(self)
        return self._addr_cache


    def _invalidate_cache(self):
        """Invalidate the function's attribute cache.

        If the function's attribute named ATTR is cached,
        its cached value will be stored in an attribute named _ATTR_cache
        This method should delete all such attributes.
        """
        if hasattr(self, "_addr_cache"):
            del self._addr_cache
        super()._invalidate_cache()


    def __setstate__(self, state):
        """This method is called when the object is unpickled."""
        super().__setstate__(state)
        self._auxiliary_config_params_at_init = dict()


    def __getstate__(self):
        """This method is called when the object is pickled."""
        return super().__getstate__()


class HashAddr(SafeStrTuple):
    """A globally unique hash-based address of an object.

    Two objects with exactly the same type and value will always have
    exactly the same HashAddr-es.

    Conceptually, HashAddr consists of 2 components: a descriptor,
    and a hash signature. A descriptor contains human-readable information
    about an object's type. A hash signature string contains
    the object's sha256 value, encoded in base-32.

    Under the hood, the hash signature is further split into 3 strings:
    a shard, a subshard and a hash tail.
    This is done to address limitations of some file systems
    and to optimize work sith cloud storage (e.g. S3).
    """

    def __init__(self, descriptor:str
                 , hash_signature:str):
        if not isinstance(descriptor, str) or not isinstance(hash_signature, str):
            raise TypeError("descriptor and hash_signature must be strings")
        if len(descriptor) == 0 or len(hash_signature) == 0:
            raise ValueError("descriptor and hash_signature must not be empty")
        SafeStrTuple.__init__(self,hash_signature[:3], hash_signature[3:6]
                              ,descriptor, hash_signature[6:])


    @property
    def shard(self)->str:
        return self.strings[0]

    @property
    def subshard(self)->str:
        return self.strings[1]

    @property
    def descriptor(self) -> str:
        return self.strings[2]

    @property
    def hash_tail(self)->str:
        return self.strings[3]

    @property
    def hash_signature(self) -> str:
        return self.shard+self.subshard+self.hash_tail

    @staticmethod
    def _build_descriptor(x: Any) -> str:
        """Create a short human-readable summary of an object."""

        if (hasattr(x, "__hash_addr_descriptor__")
                and callable(x.__hash_addr_descriptor__)):
            descriptor = x.__hash_addr_descriptor__()
        else:
            descriptor = x.__class__.__name__.lower()
            if (hasattr(x, "shape") and hasattr(x.shape, "__iter__")
                    and callable(x.shape.__iter__) and not callable(x.shape)):
                suffix, connector = "_shape_", "_x_"
                for n in x.shape:
                    suffix += str(n) + connector
                suffix = suffix[:-len(connector)]
            elif hasattr(x, "__len__") and callable(x.__len__):
                suffix = "_len_" + str(len(x))
            else:
                suffix = ""

            suffix = replace_unsafe_chars(suffix, replace_with="_")
            descriptor = descriptor + suffix

        return descriptor


    @staticmethod
    def _build_hash_signature(x: Any) -> str:
        """Create a URL-safe hashdigest for an object."""
        hash_signature = get_hash_signature(x)
        return hash_signature


    @classmethod
    def from_strings(cls, *
                     , descriptor:str
                     , hash_signature:str
                     , assert_readiness:bool=True
                     ) -> HashAddr:
        """(Re)construct address from str versions of a descriptor and a hash"""

        if not isinstance(descriptor, str) or not isinstance(hash_signature, str):
            raise TypeError("descriptor and hash_signature must be strings")

        if len(descriptor) == 0 or len(hash_signature) == 0:
            raise ValueError("descriptor and hash_signature must not be empty")

        address = cls.__new__(cls)
        super(cls, address).__init__(descriptor=descriptor
            , hash_signature=hash_signature)
        if assert_readiness:
            if not address.ready:
                raise ValueError("Address is not ready for retrieving data")
        return address


    @property
    @abstractmethod
    def ready(self) -> bool:
        """Check if the address points to a value that is ready to be retrieved."""
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
        """Invalidate the object's attribute cache.

        If the object's attribute named ATTR is cached,
        its cached value will be stored in an attribute named _ATTR_cache
        This method should delete all such attributes.
        """
        pass


class ValueAddr(HashAddr):
    """A globally unique address of an immutable value.

    ValueAddr is a universal global identifier of any (constant) value.

    Using only the value's hash should (theoretically) be enough to
    uniquely address all possible data objects that humanity will create
    in the foreseeable future (see, for example, ipfs.io).

    However, an address also includes a descriptor with an optional suffix.
    It makes it easier for humans to interpret an address
    and further decreases collision risk.
    """
    _containing_portals: set[str]
    _value_cache: Any

    def __init__(self, data: Any, store: bool = True):
        self._containing_portals = set()

        if hasattr(data, "get_ValueAddr"):
            data_value_addr = data.get_ValueAddr()
            descriptor = data_value_addr.descriptor
            hash_signature = data_value_addr.hash_signature
            HashAddr.__init__(self
                , descriptor=descriptor
                , hash_signature=hash_signature)
            return

        if isinstance(data, HashAddr):
            raise TypeError("get_ValueAddr is the only way to convert HashAddr into ValueAddr")

        descriptor = self._build_descriptor(data)
        hash_signature = self._build_hash_signature(data)
        HashAddr.__init__(self
            , descriptor=descriptor
            , hash_signature=hash_signature)

        self._value_cache = data

        if store:
            portal = get_current_data_portal()
            portal._value_store[self] = data
            self._containing_portals.add(portal.fingerprint)


    def _invalidate_cache(self):
        """Invalidate the object's attribute cache.

        If the object's attribute named ATTR is cached,
        its cached value will be stored in an attribute named _ATTR_cache
        This method should delete all such attributes.
        """
        if hasattr(self, "_value_cache"):
            del self._value_cache
        self._containing_portals = set()
        super()._invalidate_cache()


    def get_ValueAddr(self):
        return self


    @property
    def _ready_in_current_portal(self) -> bool:
        portal = get_current_data_portal()
        portal_id = portal.fingerprint
        if portal_id in self._containing_portals:
            return True
        result = self in portal._value_store
        if result:
            self._containing_portals.add(portal_id)
        return result


    @property
    def _ready_in_noncurrent_portals(self) -> bool:
        for portal in get_noncurrent_portals():
            if self in portal._value_store:
                value = portal._value_store[self]
                get_current_data_portal()._value_store[self] = value
                new_ids = {portal.fingerprint, get_current_portal().fingerprint}
                self._containing_portals |= new_ids
                self._value_cache = value
                return True
        return False


    @property
    def ready(self) -> bool:
        """Check if address points to a value that is ready to be retrieved."""
        if self._ready_in_current_portal:
            return True
        if self._ready_in_noncurrent_portals:
            return True
        return False


    def _get_from_current_portal(self) -> Any:
        """Retrieve value, referenced by the address, from the current portal"""

        if hasattr(self, "_value_cache"):
            if get_current_portal().fingerprint in self._containing_portals:
                return self._value_cache
            else:
                get_current_data_portal()._value_store[self] = self._value_cache
                self._containing_portals |= {get_current_portal().fingerprint}
                return self._value_cache

        value = get_current_data_portal()._value_store[self]
        self._value_cache = value
        self._containing_portals |= {get_current_portal().fingerprint}
        return value


    def _get_from_noncurrent_portals(self) -> Any:
        """Retrieve value, referenced by the address, from noncurrent portals"""

        for portal in get_noncurrent_data_portals():
            try:
                value = portal._value_store[self]
                get_current_data_portal()._value_store[self] = value
                self._value_cache = value
                new_ids = {portal.fingerprint, get_current_portal().fingerprint}
                self._containing_portals |= new_ids
                return value
            except:
                continue

        raise KeyError(f"ValueAddr {self} not found in any portal")


    def get(self
            , timeout:int|None = None
            , expected_type:Type[T]= Any
            ) -> T:
        """Retrieve value, referenced by the address from any available portal"""

        try:
            result = self._get_from_current_portal()
        except:
            result = self._get_from_noncurrent_portals()

        if not (expected_type is Any or expected_type is object):
            if not isinstance(result, expected_type):
                raise TypeError(f"Expected type {expected_type}, "
                    +f"but got {type(result)}")
        return result


    def __getstate__(self):
        """This method is called when the object is pickled."""
        state = dict(strings=self.strings)
        return state


    def __setstate__(self, state):
        """This method is called when the object is unpickled."""
        self._invalidate_cache()
        self.strings = state["strings"]
        self._containing_portals = set()


    @classmethod
    def from_strings(cls, *
                     , descriptor: str
                     , hash_signature: str
                     , assert_readiness: bool = True
                     ) -> HashAddr:
        """(Re)construct address from text representations of descriptor and hash"""

        address = super().from_strings(
            descriptor=descriptor
            , hash_signature=hash_signature
            , assert_readiness=False)
        address._containing_portals = set()
        if assert_readiness:
            if not address.ready:
                raise ValueError("Address is not ready for retrieving data")
        return address