"""Core classes for configuration management in Pythagoras portals.

This module provides ConfigurablePortal and ConfigurableStorableClass,
which add configuration parameter management capabilities to portals and
portal-aware objects.
"""

from __future__ import annotations

from typing import Any

from persidict import PersiDict, SafeStrTuple, KEEP_CURRENT, DELETE_CURRENT, Joker
from mixinforge import sort_dict_by_keys

from .._220_data_portals import DataPortal
from .._210_basic_portals import PortalAwareObject
from .._110_supporting_utilities import get_node_signature


class TunablePortal(DataPortal):
    """A portal that manages configuration parameters.

    ConfigurablePortal extends DataPortal with persistent configuration storage
    capabilities. It maintains two types of configuration:
    - Portal-wide configuration: Settings shared across all nodes
    - Node-specific configuration: Settings specific to the current compute node

    Configuration settings are cached for performance and can include auxiliary
    parameters specified during initialization.

    Attributes:
        _portal_config_settings: Portal-wide persistent configuration store.
        _node_config_settings: Node-specific persistent configuration store.
        _local_node_store: Alias to _node_config_settings for convenience.
        _portal_config_settings_cache: In-memory cache for config values.
        _auxiliary_config_params_at_init: Config parameters from initialization.
    """

    _portal_config_settings: PersiDict | None
    _node_config_settings: PersiDict | None
    _local_node_store: PersiDict | None
    _portal_config_settings_cache: dict
    _auxiliary_config_params_at_init: dict[str, Any] | None

    def __init__(self, root_dict: PersiDict | str | None = None):
        """Initialize a ConfigurablePortal.

        Args:
            root_dict: Prototype PersiDict or a path/URI used to create
                a persistent dictionary for internal stores. If None, uses
                the parent's default.
        """
        DataPortal.__init__(self, root_dict=root_dict)
        del root_dict

        self._auxiliary_config_params_at_init = dict()
        self._portal_config_settings_cache = dict()

        # Create portal-wide configuration store
        portal_config_settings_prototype = self._root_dict.get_subdict("portal_cfg")
        portal_config_settings_params = portal_config_settings_prototype.get_params()
        portal_config_settings_params.update(
            digest_len=0, append_only=False, serialization_format="pkl")
        portal_config_settings = type(self._root_dict)(**portal_config_settings_params)
        self._portal_config_settings = portal_config_settings

        # Create node-specific configuration store
        node_config_prototype = self._root_dict.get_subdict("node_cfg")
        node_config_prototype = (
            node_config_prototype.get_subdict(get_node_signature()[:8]))
        node_config_params = node_config_prototype.get_params()
        node_config_params.update(
            digest_len=0, append_only=False, serialization_format="pkl")
        node_config_settings = type(self._root_dict)(**node_config_params)
        self._node_config_settings = node_config_settings

        # TODO: refactor
        self._local_node_store = node_config_settings


    def _persist_initial_config_params(self) -> None:
        """Persist initialization configuration parameters to the portal's config store.

        Writes all auxiliary configuration parameters that were provided during
        initialization to the persistent config store.
        """
        for key, value in self._auxiliary_config_params_at_init.items():
            self._set_portal_config_setting(key, value)


    def __post_init__(self) -> None:
        """Finalize initialization after __init__ completes across the MRO.

        Ensures that auxiliary configuration parameters are persisted.
        """
        super().__post_init__()
        self._persist_initial_config_params()


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
        """Names of all auxiliary configuration parameters for this portal.

        Returns:
            Set of parameter names including base parameters and portal-specific
            auxiliary configuration parameters.
        """
        names = super().auxiliary_param_names
        names.update(self._auxiliary_config_params_at_init)
        return names


    def _get_portal_config_setting(self, key: SafeStrTuple | str) -> Any:
        """Get a configuration setting from the portal's config store.

        Retrieves settings from cache if available, otherwise loads from persistent
        storage and caches the result.

        Args:
            key: Configuration key to retrieve.

        Returns:
            The configuration value, or None if not found.

        Raises:
            TypeError: If key is not a SafeStrTuple or string.
        """
        if not isinstance(key, (str, SafeStrTuple)):
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
        """Set a configuration setting in the portal's config store.

        Persists the setting to storage and updates the cache. Handles special
        Joker values: KEEP_CURRENT leaves existing value unchanged, DELETE_CURRENT
        removes the setting.

        Args:
            key: Configuration key to set.
            value: Value to store, or a Joker for special behavior.

        Raises:
            TypeError: If key is not a SafeStrTuple or string.
        """
        if not isinstance(key, (str, SafeStrTuple)):
            raise TypeError("key must be a SafeStrTuple or a string")

        if value is KEEP_CURRENT:
            return

        self._portal_config_settings[key] = value
        self._portal_config_settings_cache[key] = value

        if value is DELETE_CURRENT:
            del self._portal_config_settings_cache[key]


    def _invalidate_cache(self):
        """Invalidate the portal's cache."""
        super()._invalidate_cache()
        self._portal_config_settings_cache = dict()


    def _clear(self) -> None:
        """Clear the portal's state.

        The portal must not be used after this method is called.
        """
        super()._clear()
        self._auxiliary_config_params_at_init = None
        self._portal_config_settings = None
        self._node_config_settings = None
        self._local_node_store = None


class TunableObject(PortalAwareObject):
    """A portal-aware class with config management capabilities.

    TunableObject provides configuration management for any portal-aware object.
    It stores auxiliary configuration parameters and provides methods to get/set
    config settings in the portal. This class does NOT provide content-addressable
    storage (.addr) - that functionality is added by subclasses that have
    sufficient structure to be hashed (like OrdinaryFn).
    """

    _auxiliary_config_params_at_init: dict[str, Any] | None

    def __init__(self, portal: TunablePortal | None = None):
        """Create a configurable storable portal-aware object.

        Args:
            portal: Optional ConfigurablePortal to bind to.
        """
        PortalAwareObject.__init__(self, portal=portal)
        self._auxiliary_config_params_at_init = dict()


    def _first_visit_to_portal(self, portal: TunablePortal) -> None:
        """Handle first visit to a portal by persisting config params.

        Args:
            portal: The ConfigurablePortal being visited for the first time.
        """
        super()._first_visit_to_portal(portal)
        self._persist_initial_config_params(portal)


    def _persist_initial_config_params(self, portal: TunablePortal) -> None:
        """Persist configuration parameters to a portal.

        Args:
            portal: The ConfigurablePortal to store configuration settings in.
        """
        for key, value in self._auxiliary_config_params_at_init.items():
            self._set_config_setting(key, value, portal)


    @property
    def portal(self) -> TunablePortal:
        """The ConfigurablePortal associated with this object.

        Returns:
            TunablePortal: The portal used by this object's methods.
        """
        return super().portal


    def _get_config_setting(self, key: SafeStrTuple | str, portal: TunablePortal) -> Any:
        """Retrieve a configuration setting from a portal.

        Checks portal-wide settings first, then falls back to object-specific
        settings if available.

        Args:
            key: Configuration key to retrieve.
            portal: The ConfigurablePortal to query.

        Returns:
            The configuration value, or None if not found.

        Raises:
            TypeError: If key is not a SafeStrTuple or string.
        """
        if not isinstance(key, (str, SafeStrTuple)):
            raise TypeError("key must be a SafeStrTuple or a string")

        portal_wide_value = portal._get_portal_config_setting(key)
        if portal_wide_value is not None:
            return portal_wide_value

        # For object-specific settings, we just use the key directly
        # Subclasses with .addr can override this to use addr-based keys
        object_specific_value = portal._get_portal_config_setting(key)

        return object_specific_value


    def _set_config_setting(self
                            , key: SafeStrTuple | str
                            , value: Any
                            , portal: TunablePortal) -> None:
        """Set a configuration setting in a portal.

        Args:
            key: Configuration key to set.
            value: Value to store.
            portal: The ConfigurablePortal to store the setting in.

        Raises:
            TypeError: If key is not a SafeStrTuple or string.
        """
        if not isinstance(key, (SafeStrTuple, str)):
            raise TypeError("key must be a SafeStrTuple or a string")
        portal._set_portal_config_setting(key, value)


    def __setstate__(self, state):
        """This method is called when the object is unpickled."""
        super().__setstate__(state)
        self._auxiliary_config_params_at_init = dict()


    def __getstate__(self):
        """This method is called when the object is pickled."""
        return super().__getstate__()
