"""Core classes for work sith portal/object settings in Pythagoras .

This module provides TunablePortal and TunableObject classes    ,
which add settings management capabilities to portals and
portal-aware objects.
"""

from __future__ import annotations

from typing import Any

from persidict import PersiDict, NonEmptySafeStrTuple
from mixinforge import sort_dict_by_keys

from .._220_data_portals import DataPortal, StorableObject
from .._210_basic_portals import PortalAwareObject
from .._110_supporting_utilities import get_node_signature


class TunablePortal(DataPortal):
    """A portal that provides tools for storing / retrieving settings.

    TunablePortal extends DataPortal with persistent storage for settings.
    It maintains two types of settings:
    - Portal-wide: Settings shared across all nodes in a portal
    - Node-specific: Settings known / applicable to the current compute node

    Attributes:
        _global_portal_settings: Portal-wide persistent configuration store.
        _local_node_settings: Node-specific persistent configuration store.
        _local_node_value_store: Alias to _local_node_settings for convenience.
        _global_portal_settings_cache: In-memory cache for config values.
        _auxiliary_config_params_at_init: Config parameters from initialization.
    """

    _global_portal_settings: PersiDict | None
    _local_node_settings: PersiDict | None
    _local_node_value_store: PersiDict | None
    _global_portal_settings_cache: dict
    _auxiliary_config_params_at_init: dict[str, Any] | None

    def __init__(self, root_dict: PersiDict | str | None = None):
        """Initialize a TunablePortal.

        Args:
            root_dict: Prototype PersiDict or a path/URI used to create
                a persistent dictionary for internal stores. If None, uses
                the parent's default.
        """
        DataPortal.__init__(self, root_dict=root_dict)
        del root_dict

        self._auxiliary_config_params_at_init = dict()
        # self._global_portal_settings_cache = dict()

        # Create portal-wide configuration store
        portal_config_settings_prototype = self._root_dict.get_subdict("portal_cfg")
        portal_config_settings_params = portal_config_settings_prototype.get_params()
        portal_config_settings_params.update(
            digest_len=0, append_only=False, serialization_format="pkl")
        portal_config_settings = type(self._root_dict)(**portal_config_settings_params)
        self._global_portal_settings = portal_config_settings

        # Create node-specific configuration store
        node_config_prototype = self._root_dict.get_subdict("node_cfg")
        node_config_prototype = node_config_prototype.get_subdict(
            get_node_signature()[:8])
        node_config_params = node_config_prototype.get_params()
        node_config_params.update(
            digest_len=0, append_only=False, serialization_format="pkl")
        node_config_settings = type(self._root_dict)(**node_config_params)
        self._local_node_settings = node_config_settings

        # TODO: refactor
        self._local_node_value_store = node_config_settings


    @property
    def global_portal_settings(self) -> PersiDict:
        """Portal-wide persistent configuration store.

        Returns:
            PersiDict: The persistent dictionary storing portal-wide settings.
        """
        return self._global_portal_settings


    @property
    def local_node_settings(self) -> PersiDict:
        """Node-specific persistent configuration store.

        Returns:
            PersiDict: The persistent dictionary storing node-specific settings.
        """
        return self._local_node_settings


    @property
    def local_node_value_store(self) -> PersiDict:
        """Local node value store (alias to local_node_settings).

        Returns:
            PersiDict: The persistent dictionary for local node values.
        """
        return self._local_node_value_store


    def get_effective_setting(self , key: NonEmptySafeStrTuple|str, default:Any=None) -> Any:
        """Get the effective configuration setting for a given key.

        Checks node-specific settings first, then falls back to portal-wide
        settings if not found.

        Args:
            key: Configuration key to retrieve.

        Returns:
            The effective configuration value, or None if not found.
        """

        no_value = object()

        node_value = self.local_node_settings.get(key, no_value)
        if node_value is not no_value:
            return node_value
        portal_value = self.global_portal_settings.get(key, default)
        return portal_value


    def _persist_initial_config_params(self) -> None:
        """Persist initialization configuration parameters to the portal's config store.

        Writes all auxiliary configuration parameters that were provided during
        initialization to the persistent config store.
        """
        for key, value in self._auxiliary_config_params_at_init.items():
            self.local_node_settings[key] = value


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


    # def _get_portal_config_setting(self, key: SafeStrTuple | str) -> Any:
    #     """Get a configuration setting from the portal's config store.
    #
    #     Retrieves settings from cache if available, otherwise loads from persistent
    #     storage and caches the result.
    #
    #     Args:
    #         key: Configuration key to retrieve.
    #
    #     Returns:
    #         The configuration value, or None if not found.
    #
    #     Raises:
    #         TypeError: If key is not a SafeStrTuple or string.
    #     """
    #     if not isinstance(key, (str, SafeStrTuple)):
    #         raise TypeError("key must be a SafeStrTuple or a string")
    #
    #     if key in self._global_portal_settings_cache:
    #         value = self._global_portal_settings_cache[key]
    #     elif key in self.global_portal_settings:
    #         value = self.global_portal_settings[key]
    #         self._global_portal_settings_cache[key] = value
    #     else:
    #         value = None
    #         self._global_portal_settings_cache[key] = None
    #     return value


    # def _set_portal_config_setting(self, key: SafeStrTuple | str, value: Any) -> None:
    #     """Set a configuration setting in the portal's config store.
    #
    #     Persists the setting to storage and updates the cache. Handles special
    #     Joker values: KEEP_CURRENT leaves existing value unchanged, DELETE_CURRENT
    #     removes the setting.
    #
    #     Args:
    #         key: Configuration key to set.
    #         value: Value to store, or a Joker for special behavior.
    #
    #     Raises:
    #         TypeError: If key is not a SafeStrTuple or string.
    #     """
    #     if not isinstance(key, (str, SafeStrTuple)):
    #         raise TypeError("key must be a SafeStrTuple or a string")
    #
    #     if value is KEEP_CURRENT:
    #         return
    #
    #     self.global_portal_settings[key] = value
    #     self._global_portal_settings_cache[key] = value
    #
    #     if value is DELETE_CURRENT:
    #         del self._global_portal_settings_cache[key]


    def _invalidate_cache(self):
        """Invalidate the portal's cache."""
        super()._invalidate_cache()
        # self._global_portal_settings_cache = dict()


    def _clear(self) -> None:
        """Clear the portal's state.

        The portal must not be used after this method is called.
        """
        super()._clear()
        self._auxiliary_config_params_at_init = None
        self._global_portal_settings = None
        self._local_node_settings = None
        self._local_node_value_store = None


class TunableObject(StorableObject):
    """A portal-aware class with config management capabilities.

    TunableObject provides configuration management for any portal-aware object.
    It stores auxiliary configuration parameters and provides methods to get/set
    config settings in the portal.
    """

    _auxiliary_config_params_at_init: dict[str, Any] | None

    def __init__(self, portal: TunablePortal | None = None):
        """Create a configurable storable portal-aware object.

        Args:
            portal: Optional TunablePortal to bind to.
        """
        StorableObject.__init__(self, portal=portal)
        self._auxiliary_config_params_at_init = dict()


    def _get_local_node_settings(self, portal: TunablePortal) -> PersiDict:
        """Get the local node settings from the specified portal.

        Args:
            portal: The TunablePortal to retrieve settings from.
        Returns:
            PersiDict: The local node settings dictionary.
        """
        return portal.local_node_settings.get_subdict(self.addr)

    @property
    def local_node_settings(self) -> PersiDict:
        """Get the local node settings from the associated portal.

        Returns:
            PersiDict: The local node settings dictionary.
        """
        return self._get_local_node_settings(portal=self.portal)


    def _get_global_portal_settings(self, portal: TunablePortal) -> PersiDict:
        """Get the global portal settings from the specified portal.

        Args:
            portal: The TunablePortal to retrieve settings from.
        Returns:
            PersiDict: The global portal settings dictionary.
        """
        return portal.global_portal_settings.get_subdict(self.addr)


    @property
    def global_portal_settings(self) -> PersiDict:
        """Get the global portal settings from the associated portal.

        Returns:
            PersiDict: The global portal settings dictionary.
        """
        return self._get_global_portal_settings(portal=self.portal)

    def get_effective_setting(self , key: NonEmptySafeStrTuple|str, default:Any=None) -> Any:
        """Get the effective configuration setting for a given key.

        Checks local node settings first, then falls back to global portal
        settings if not found.

        Args:
            key: Configuration key to retrieve.

        Returns:
            The effective configuration value, or None if not found.
        """
        no_value = object()
        node_value = self.local_node_settings.get(key, no_value)
        if node_value is not no_value:
            return node_value
        portal_value = self.global_portal_settings.get(key, default)
        return portal_value


    def _first_visit_to_portal(self, portal: TunablePortal) -> None:
        """Handle first visit to a portal.

        Args:
            portal: The TunablePortal being visited for the first time.
        """
        super()._first_visit_to_portal(portal)
        # self._persist_initial_config_params(portal)
        local_node_settings = self._get_local_node_settings(portal=portal)

        for key, value in self._auxiliary_config_params_at_init.items():
            local_node_settings[key] = value

    # def _persist_initial_config_params(self, portal: TunablePortal) -> None:
    #     """Persist configuration parameters to a portal.
    #
    #     Args:
    #         portal: The TunablePortal to store configuration settings in.
    #     """
    #     for key, value in self._auxiliary_config_params_at_init.items():
    #         portal.local_node_settings[self,key] = value


    @property
    def portal(self) -> TunablePortal:
        """The TunablePortal associated with this object.

        Returns:
            TunablePortal: The portal used by this object's methods.
        """
        return super().portal


    # def _get_config_setting(self, key: SafeStrTuple | str, portal: TunablePortal) -> Any:
    #     """Retrieve a configuration setting from a portal.
    #
    #     Checks portal-wide settings first, then falls back to object-specific
    #     settings if available.
    #
    #     Args:
    #         key: Configuration key to retrieve.
    #         portal: The TunablePortal to query.
    #
    #     Returns:
    #         The configuration value, or None if not found.
    #
    #     Raises:
    #         TypeError: If key is not a SafeStrTuple or string.
    #     """
    #     if not isinstance(key, (str, SafeStrTuple)):
    #         raise TypeError("key must be a SafeStrTuple or a string")
    #
    #     portal_wide_value = portal._get_portal_config_setting(key)
    #     if portal_wide_value is not None:
    #         return portal_wide_value
    #
    #     # For object-specific settings, we just use the key directly
    #     # Subclasses with .addr can override this to use addr-based keys
    #     object_specific_value = portal._get_portal_config_setting(key)
    #
    #     return object_specific_value


    # def _set_config_setting(self
    #                         , key: SafeStrTuple | str
    #                         , value: Any
    #                         , portal: TunablePortal) -> None:
    #     """Set a configuration setting in a portal.
    #
    #     Args:
    #         key: Configuration key to set.
    #         value: Value to store.
    #         portal: The TunablePortal to store the setting in.
    #
    #     Raises:
    #         TypeError: If key is not a SafeStrTuple or string.
    #     """
    #     if not isinstance(key, (SafeStrTuple, str)):
    #         raise TypeError("key must be a SafeStrTuple or a string")
    #     portal._set_portal_config_setting(key, value)


    def __setstate__(self, state):
        """This method is called when the object is unpickled."""
        super().__setstate__(state)
        self._auxiliary_config_params_at_init = dict()


    def __getstate__(self):
        """This method is called when the object is pickled."""
        return super().__getstate__()
