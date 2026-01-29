from __future__ import annotations

from functools import cached_property
from typing import Type, Any, Final

from persidict import replace_unsafe_chars, SafeStrTuple

from .._210_basic_portals import *
from .._110_supporting_utilities import get_hash_signature, get_long_infoname

from .._210_basic_portals.basic_portal_core_classes import (
    _describe_persistent_characteristic)
from persidict import WriteOnceDict

T = TypeVar('T')

_TOTAL_VALUES_TXT: Final[str] = "Values, total"


def count_known_data_portals() -> int:
    """Get the number of known DataPortals.

    Returns:
        The total count of all known portals in the system.

    Raises:
        TypeError: If any known portal is not an instance of DataPortal.
    """
    return count_known_portals(DataPortal)


def get_all_known_data_portals() -> set[DataPortal]:
    """Get a list of all known DataPortals.

    Returns:
        A list containing all portal instances currently known to the system.

    Raises:
        TypeError: If any known portal is not an instance of DataPortal.
    """
    return get_known_portals(DataPortal)


def get_number_of_active_data_portals() -> int:
    """Get the number of unique DataPortals in the active stack.

    Returns:
        The count of unique portals currently in the active portal stack.

    Raises:
        TypeError: If any active portal is not an instance of DataPortal.
    """
    return count_active_portals(DataPortal)


def measure_depth_of_active_data_portals_stack() -> int:
    """Get the depth of the active DataPortal stack.

    Returns:
        The total depth (sum of all counters) of the active portal stack.

    Raises:
        TypeError: If any active portal is not an instance of DataPortal.
    """
    return measure_active_portals_stack(DataPortal)


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
        raise TypeError(f"The current portal is {get_long_infoname(portal)}, "
                           f"but a DataPortal was expected.")
    return portal


def get_nonactive_data_portals() -> set[DataPortal]:
    """Get a list of all DataPortals that are not in the active stack.

    Returns:
        A list of portal instances that are not currently in the active portal stack.

    Raises:
        TypeError: If any non-active portal is not an instance of DataPortal.
    """
    return get_nonactive_portals(DataPortal)


def get_noncurrent_data_portals() -> set[DataPortal]:
    """Get a list of all DataPortals that are not the current portal.

    Returns:
        A list of all known portal instances but the current one.

    Raises:
        TypeError: If any non-current portal is not an instance of DataPortal.
    """
    return get_noncurrent_portals(DataPortal)


class DataPortal(BasicPortal):
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

    Note:
        Use the portal as a context manager whenever code performs I/O with
        the portal (reading or storing values):

        with portal:
            addr = ValueAddr(data)
            value = addr.get()

    """

    _global_value_store: WriteOnceDict | None

    def __init__(self
            , root_dict: PersiDict|str|None = None
            ):
        """Initialize a DataPortal.

        Args:
            root_dict: Prototype PersiDict or a path/URI used to create
                a persistent dictionary for internal stores. If None, uses
                the parent's default.
        """
        BasicPortal.__init__(self, root_dict = root_dict)
        del root_dict

        value_store_prototype = self._root_dict.get_subdict("value_store")
        value_store_params = value_store_prototype.get_params()
        value_store_params.update(
            digest_len=0, append_only=True, serialization_format = "pkl")
        value_store = type(self._root_dict)(**value_store_params)
        value_store = WriteOnceDict(value_store, 0)
        self._global_value_store = value_store


    @property
    def global_value_store(self) -> WriteOnceDict:
        """The portal's persistent content-addressable storage.

        Returns:
            The persistent dictionary storing values by address.
        """
        return self._global_value_store


    def describe(self) -> pd.DataFrame:
        """Get a DataFrame describing the portal's current state."""
        all_params = [super().describe()]

        all_params.append(_describe_persistent_characteristic(
            _TOTAL_VALUES_TXT, len(self.global_value_store)))

        result = pd.concat(all_params)
        result.reset_index(drop=True, inplace=True)
        return result


    def _clear(self) -> None:
        """Clear the portal's state.

        The portal must not be used after this method is called.
        """
        super()._clear()
        self._global_value_store = None


class StorableObject(PortalAwareObject):
    """Minimal portal-aware base class for objects that work with DataPortal."""

    def __init__(self, portal: DataPortal | None = None):
        """Create a storable portal-aware object.

        Args:
            portal: Optional DataPortal to bind to.
        """
        super().__init__(portal=portal)

    @property
    def portal(self) -> DataPortal:
        """The DataPortal associated with this object.

        Returns:
            DataPortal: The portal used by this object's methods.
        """
        return super().portal

    @cached_property
    def addr(self) -> ValueAddr:
        """The content-derived address of this object.

        Returns:
            ValueAddr uniquely identifying this object based on its content.
        """
        if not hasattr(self, "_init_finished") or not self._init_finished:
            raise ValueError("Cannot get address of an uninitialized object")
        return ValueAddr(self)


class HashAddr(SafeStrTuple, CacheablePropertiesMixin):
    """A globally unique hash-based address of an object.

    HashAddr provides content-addressable identification where two objects
    with identical type and value always produce identical addresses. This
    enables reliable deduplication and content-based retrieval.

    Structure:
        - descriptor: Human-readable type/shape information
        - hash_signature: SHA-256 hash encoded in base-32
          - shard: First 3 characters (for filesystem/storage optimization)
          - subshard: Next 3 characters (for further partitioning)
          - hash_tail: Remaining characters

    The three-part hash split addresses filesystem limitations (max files
    per directory) and optimizes cloud storage access patterns (S3 prefix
    distribution).
    """

    def __init__(self, descriptor:str
                 , hash_signature:str):
        """Initialize a HashAddr.

        Args:
            descriptor: Human-readable type/shape information.
            hash_signature: Base-32 encoded hash, minimum 10 characters.

        Raises:
            TypeError: If descriptor or hash_signature are not strings.
            ValueError: If either is empty or hash_signature is too short.
        """
        if not isinstance(descriptor, str) or not isinstance(hash_signature, str):
            raise TypeError("descriptor and hash_signature must be strings")
        if len(descriptor) == 0 or len(hash_signature) == 0:
            raise ValueError("descriptor and hash_signature must not be empty")
        if len(hash_signature) < 10:
            raise ValueError(f"hash_signature must be at least 10 characters, "
                             f"got {len(hash_signature)} characters instead.")
        SafeStrTuple.__init__(self,hash_signature[:3], hash_signature[3:6]
                              ,descriptor, hash_signature[6:])


    @cached_property
    def shard(self)->str:
        """First 3 characters of hash, used for top-level partitioning."""
        return self.strings[0]

    @cached_property
    def subshard(self)->str:
        """Characters 4-6 of hash, used for second-level partitioning."""
        return self.strings[1]

    @cached_property
    def descriptor(self) -> str:
        """Human-readable type/shape information."""
        return self.strings[2]

    @cached_property
    def hash_tail(self)->str:
        """Remaining characters of hash after shard and subshard."""
        return self.strings[3]

    @cached_property
    def hash_signature(self) -> str:
        """Complete hash signature (shard + subshard + tail)."""
        return self.shard+self.subshard+self.hash_tail

    @staticmethod
    def _build_descriptor(x: Any) -> str:
        """Create a short human-readable summary of an object.

        Generates a descriptor by examining the object's type and structure.
        For objects with a __hash_addr_descriptor__ method, uses that; otherwise
        constructs from class name and shape/length information.

        Args:
            x: Object to create a descriptor for.

        Returns:
            URL-safe string descriptor.
        """

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
        """Create a URL-safe hash signature for an object.

        Args:
            x: Object to hash.

        Returns:
            Base-32 encoded hash signature.
        """
        hash_signature = get_hash_signature(x)
        return hash_signature


    @classmethod
    def from_strings(cls, *
                     , descriptor:str
                     , hash_signature:str
                     , assert_readiness:bool=True
                     ) -> HashAddr:
        """Reconstruct address from string components.

        Args:
            descriptor: Human-readable type/shape information.
            hash_signature: Base-32 encoded hash.
            assert_readiness: Whether to validate address readiness (subclass-specific).

        Returns:
            Reconstructed HashAddr instance.

        Raises:
            TypeError: If descriptor or hash_signature are not strings.
            ValueError: If either is empty.
        """

        if not isinstance(descriptor, str) or not isinstance(hash_signature, str):
            raise TypeError("descriptor and hash_signature must be strings")

        if len(descriptor) == 0 or len(hash_signature) == 0:
            raise ValueError("descriptor and hash_signature must not be empty")

        address = cls.__new__(cls)
        HashAddr.__init__(address, descriptor = descriptor, hash_signature=hash_signature)
        return address


    @property
    @abstractmethod
    def ready(self) -> bool:
        """Check if the address points to a value that is ready to be retrieved."""
        # TODO: decide whether we need .ready() at the base class
        raise NotImplementedError


    @abstractmethod
    def get(self, timeout: int | None = None, expected_type:Type[T]= Any) -> T:
        """Retrieve the value referenced by this address.

        Args:
            timeout: Maximum wait time in seconds, or None for no timeout.
            expected_type: Expected type of the retrieved value for validation.

        Returns:
            The value stored at this address.

        Raises:
            NotImplementedError: Must be implemented by subclasses.
        """
        raise NotImplementedError


    def __eq__(self, other) -> bool:
        """Return self==other. """
        return type(self) is type(other) and self.strings == other.strings


    def __ne__(self, other) -> bool:
        """Return self!=other. """
        return not (self == other)


    def __hash__(self) -> int:
        """Return hash(self), consistent with __eq__."""
        return hash((type(self), self.strings))


class ValueAddr(HashAddr):
    """A globally unique address of an immutable value.

    ValueAddr provides content-addressable storage and retrieval for arbitrary
    Python objects. Each value is uniquely identified by its content hash
    (SHA-256), making ValueAddr suitable for distributed systems and deduplication.

    The address includes both a cryptographic hash (providing theoretical uniqueness
    comparable to systems like IPFS) and a human-readable descriptor (improving
    interpretability and further reducing collision risk).

    Behavior:
        - Creating a ValueAddr automatically stores the value in the current DataPortal
        - Values can be retrieved from any DataPortal that contains them
        - If a value is retrieved from a non-current portal, it's automatically replicated to the current one
        - The .ready property checks value availability across all known portals
        - The .get() method retrieves value from any known portal that contains it
    """
    _containing_portals: set[DataPortal]

    def __init__(self, data: Any, store: bool = True):
        """Create a ValueAddr for an object.

        Args:
            data: The object to address. Can be any picklable Python object,
                or another ValueAddr/object with get_ValueAddr() method.
            store: If True, automatically store the value in the current DataPortal.
                Set to False to create an address without storage (useful for lookups).

        Raises:
            ValueError: If data is an uninitialized object (has _init_finished=False).
            TypeError: If data is a HashAddr (must use get_ValueAddr() instead).
        """
        self._containing_portals = set()

        if hasattr(data, "get_ValueAddr"):
            data_value_addr = data.get_ValueAddr()
            descriptor = data_value_addr.descriptor
            hash_signature = data_value_addr.hash_signature
            HashAddr.__init__(self
                , descriptor=descriptor
                , hash_signature=hash_signature)
            return

        if hasattr(data, "_init_finished") and not data._init_finished:
            raise ValueError("Cannot create ValueAddr for an uninitialized object")

        if isinstance(data, HashAddr):
            raise TypeError("get_ValueAddr is the only way to convert HashAddr into ValueAddr")

        descriptor = self._build_descriptor(data)
        hash_signature = self._build_hash_signature(data)
        HashAddr.__init__(self
            , descriptor=descriptor
            , hash_signature=hash_signature)

        if store:
            portal = get_current_data_portal()
            portal.global_value_store[self] = data
            self._containing_portals.add(portal)

        self._set_cached_properties(value=data)


    @cached_property
    def value(self) -> Any:
        """The value referenced by this address.

        Retrieves and caches the value from any available portal. Equivalent
        to calling .get() but cached for efficiency.

        Returns:
            The object referenced by this address.

        Raises:
            KeyError: If the value cannot be found in any known portal.
        """
        return self.get()


    def _invalidate_cache(self):
        """Invalidate the object's attribute cache."""
        self._containing_portals = set()
        super()._invalidate_cache()


    def get_ValueAddr(self):
        """Return self, enabling ValueAddr to be used where addresses are expected.

        Returns:
            This ValueAddr instance.
        """
        return self



    @property
    def _noncontaining_portals(self) -> set[DataPortal]:
        """Portals not yet known to contain this value.

        Returns:
            Set of portals that haven't been checked or confirmed
            not to contain this value.
        """
        all_portals = set(get_all_known_data_portals())
        return all_portals - self._containing_portals



    def _get_from_current_portal(self) -> tuple[Any, bool]:
        """Try to retrieve value from the current portal.

        Uses cached portals for fast-path lookup when available,
        falls back to direct store lookup otherwise. Updates cache on success.

        Returns:
            Tuple of (data, success) where success is True if value was found
            and retrieved.
        """
        current_portal = get_current_data_portal()

        # Fast path: check if we already know it's in current portal
        if current_portal in self._containing_portals:
            data = current_portal.global_value_store[self]
            self._set_cached_properties(value=data)
            return data, True

        # Slow path: check the store directly
        if self in current_portal.global_value_store:
            self._containing_portals.add(current_portal)
            data = current_portal.global_value_store[self]
            self._set_cached_properties(value=data)
            return data, True

        return None, False


    @property
    def ready(self) -> bool:
        """Check if the value is available in any known portal.

        Searches through all retrieval strategies (cache, current portal, known
        containing portals, and other portals) to determine availability. If found
        in a non-current portal, automatically replicates the value to the current portal.

        Returns:
            True if the value is available in the current portal or has been successfully replicated,
            False if not found in any portal.
        """
        # Try to retrieve using the same strategies as get(), just return boolean
        if get_current_data_portal() in self._containing_portals:
            return True

        _, success = self._get_from_cache()
        if success:
            return True

        _, success = self._get_from_current_portal()
        if success:
            return True

        _, success = self._get_from_known_containing_portal()
        if success:
            return True

        _, success = self._get_from_noncontaining_portals()
        return success


    def _get_from_cache(self) -> tuple[Any, bool]:
        """Try to retrieve value from the cached property.

        If the value property is cached, retrieves it and ensures it's stored
        in the current portal (replicating if necessary).

        Returns:
            Tuple of (data, success) where success is True if a cached value
            was available.
        """
        if not self._get_cached_property_status("value"):
            return None, False

        data = self._get_cached_property("value")
        current_portal = get_current_data_portal()

        if current_portal not in self._containing_portals:
            current_portal.global_value_store[self] = data
            self._containing_portals.add(current_portal)

        return data, True


    def _get_from_known_containing_portal(self) -> tuple[Any, bool]:
        """Try to retrieve value from a known containing portal (not current).

        Retrieves from any cached containing portal, then replicates
        to the current portal.

        Returns:
            Tuple of (data, success) where success is True if data was retrieved.
        """
        if len(self._containing_portals) < 1:
            return None, False

        containing_portal = next(iter(self._containing_portals))
        data = containing_portal.global_value_store[self]

        current_portal = get_current_data_portal()
        current_portal.global_value_store[self] = data
        self._containing_portals.add(current_portal)
        self._set_cached_properties(value=data)

        return data, True


    def _get_from_noncontaining_portals(self) -> tuple[Any, bool]:
        """Search all portals we haven't checked yet for the value.

        Iterates through all portals not known to contain this value and tries
        to retrieve it. If found, replicates to the current portal.

        Returns:
            Tuple of (data, success) where success is True if value was found,
            retrieved and replicated.
        """
        current_portal = get_current_data_portal()

        for other_portal in self._noncontaining_portals:
            try:
                data = other_portal.global_value_store[self]
                self._containing_portals.add(other_portal)
                current_portal.global_value_store[self] = data
                self._containing_portals.add(current_portal)
                self._set_cached_properties(value=data)
                return data, True
            except Exception:
                pass

        return None, False


    def _validate_type(self, data: Any, expected_type: Type[T]) -> None:
        """Validate that retrieved data matches the expected type.

        Args:
            data: The retrieved data to validate.
            expected_type: The expected type.

        Raises:
            TypeError: If data doesn't match expected_type.
        """
        if expected_type is Any or expected_type is object:
            return

        if not isinstance(data, expected_type):
            raise TypeError(f"Expected type {expected_type}, "
                +f"but got {type(data)}")


    def get(self
            , timeout:int|None = None
            , expected_type:Type[T]= Any
            ) -> T:
        """Retrieve the value referenced by this address from any available portal.

        Searches through cache, current portal, known containing portals, and
        other portals in order. If found in a non-current portal, the value is
        automatically replicated to the current portal.

        Args:
            timeout: Unused.
            expected_type: Expected type of the retrieved value for validation.

        Returns:
            The value stored at this address.

        Raises:
            KeyError: If the value cannot be found in any known portal.
            TypeError: If the retrieved value doesn't match expected_type.
        """
        # Try to retrieve data through various strategies
        data, success = self._get_from_cache()
        if not success:
            data, success = self._get_from_current_portal()
        if not success:
            data, success = self._get_from_known_containing_portal()
        if not success:
            data, success = self._get_from_noncontaining_portals()

        if not success:
            raise KeyError(f"Could not retrieve value for address {self} "
                           f"from any available portal")

        self._validate_type(data, expected_type)
        return data


    def __getstate__(self):
        """Prepare address for pickling.

        Returns:
            State dictionary containing only the address components (strings).
            Cached values and portal fingerprints are not serialized.
        """
        state = dict(strings=self.strings)
        return state


    def __setstate__(self, state):
        """Restore address from unpickling.

        Reconstructs the address from serialized strings and resets runtime state
        (cached values and portal fingerprints).

        Args:
            state: State dictionary from __getstate__.
        """
        self._invalidate_cache()
        self.strings = state["strings"]
        self._containing_portals = set()


    @classmethod
    def from_strings(cls, *
                     , descriptor: str
                     , hash_signature: str
                     , assert_readiness: bool = True
                     ) -> Self:
        """Reconstruct a ValueAddr from its string components.

        Args:
            descriptor: Human-readable type/shape information.
            hash_signature: Base-32 encoded hash.
            assert_readiness: If True, verify the value is retrievable.

        Returns:
            Reconstructed ValueAddr instance.

        Raises:
            TypeError: If descriptor or hash_signature are not strings.
            ValueError: If either is empty, or if assert_readiness is True
                and the value cannot be found in any known portal.
        """
        address = super().from_strings(
            descriptor=descriptor
            , hash_signature=hash_signature
            , assert_readiness=False)
        address._containing_portals = set()
        if assert_readiness:
            if not address.ready:
                raise ValueError("Address is not ready for retrieving data")
        return address
