"""Core classes for working with portal/object settings in Pythagoras.

This module provides TunablePortal and TunableObject classes,
which add settings management capabilities to portals and
portal-aware objects.
"""

from __future__ import annotations

from typing import Any

from persidict import PersiDict, NonEmptySafeStrTuple
from mixinforge import sort_dict_by_keys

from .._220_data_portals import DataPortal, StorableObject
from .._110_supporting_utilities import get_node_signature


class TunablePortal(DataPortal):
    """A portal that provides tools for storing / retrieving settings.

    TunablePortal extends DataPortal with persistent storage for settings.
    It maintains two types of settings:
    - Portal-wide (global): Settings shared across all nodes in a portal
    - Node-specific (local): Settings applicable to the current compute node

    Settings Precedence:
        When retrieving settings via get_effective_setting(), global settings
        take precedence over local settings. This allows portal-wide defaults
        to be overridden by node-specific values when needed.

    Attributes:
        _global_portal_settings: Portal-wide persistent configuration store.
        _local_node_settings: Node-specific persistent configuration store.
        _local_node_value_store: Alias to _local_node_settings for convenience.
        _auxiliary_config_params_at_init: Config parameters from initialization.
    """

    _global_portal_settings: PersiDict | None
    _local_node_settings: PersiDict | None
    _local_node_value_store: PersiDict | None
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
            The persistent dictionary storing portal-wide settings.
        """
        return self._global_portal_settings


    @property
    def local_node_settings(self) -> PersiDict:
        """Node-specific persistent configuration store.

        Returns:
            The persistent dictionary storing node-specific settings.
        """
        return self._local_node_settings


    @property
    def local_node_value_store(self) -> PersiDict:
        """Local node value store (alias to local_node_settings).

        Returns:
            The persistent dictionary for local node values.
        """
        return self._local_node_value_store


    def get_effective_setting(self , key: NonEmptySafeStrTuple|str, default:Any=None) -> Any:
        """Get the effective configuration setting for a given key.

        Precedence order (highest to lowest):
            1. global_portal_settings (portal-wide, shared across all nodes)
            2. local_node_settings (node-specific)

        Args:
            key: Configuration key to retrieve.
            default: Value to return if key is not found in any settings store.

        Returns:
            The effective configuration value, or default if not found.
        """

        no_value = object()

        portal_value = self.global_portal_settings.get(key, no_value)
        if portal_value is not no_value:
            return portal_value
        node_value = self.local_node_settings.get(key, default)
        return node_value


    def _persist_initial_config_params(self) -> None:
        """Persist initialization configuration parameters to the portal's global config store.

        Writes all auxiliary configuration parameters that were provided during
        initialization to the portal-wide (global) config store. This ensures
        these settings take precedence over any node-specific settings.
        """
        for key, value in self._auxiliary_config_params_at_init.items():
            self.global_portal_settings[key] = value


    def __post_init__(self) -> None:
        """Finalize initialization after __init__ completes across the MRO.

        Ensures that auxiliary configuration parameters are persisted.
        """
        super().__post_init__()
        self._persist_initial_config_params()


    def get_params(self) -> dict:
        """Return the portal's configuration parameters.

        Returns:
            A sorted dictionary of base parameters augmented with
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
        names = set(super().auxiliary_param_names)
        names.update(self._auxiliary_config_params_at_init)
        return names


    def _invalidate_cache(self):
        """Invalidate the portal's cache."""
        super()._invalidate_cache()


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

    Settings Precedence:
        When retrieving settings via get_effective_setting(), the following
        precedence order applies (highest to lowest):
            1. Portal's global_portal_settings (portal-wide, shared across nodes)
            2. Portal's local_node_settings (portal-wide, node-specific)
            3. Object's global_portal_settings (object-scoped, shared across nodes)
            4. Object's local_node_settings (object-scoped, node-specific)

        This allows portal-wide settings to override object-specific settings,
        and global settings to override local settings at each level.
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
        """Get the object's local node settings from the specified portal.

        Args:
            portal: The TunablePortal to retrieve settings from.

        Returns:
            The local node settings dictionary scoped to this object's address.
        """
        return portal.local_node_settings.get_subdict(self.addr)

    @property
    def local_node_settings(self) -> PersiDict:
        """Get the object's local node settings from the associated portal.

        Returns:
            The local node settings dictionary scoped to this object's address.
        """
        return self._get_local_node_settings(portal=self.portal)


    def _get_global_portal_settings(self, portal: TunablePortal) -> PersiDict:
        """Get the object's global portal settings from the specified portal.

        Args:
            portal: The TunablePortal to retrieve settings from.

        Returns:
            The global portal settings dictionary scoped to this object's address.
        """
        return portal.global_portal_settings.get_subdict(self.addr)


    @property
    def global_portal_settings(self) -> PersiDict:
        """Get the object's global portal settings from the associated portal.

        Returns:
            The global portal settings dictionary scoped to this object's address.
        """
        return self._get_global_portal_settings(portal=self.portal)

    def get_effective_setting(self , key: NonEmptySafeStrTuple|str, default:Any=None) -> Any:
        """Get the effective configuration setting for a given key.

        Precedence order (highest to lowest):
            1. Portal's global_portal_settings (portal-wide, shared across all nodes)
            2. Portal's local_node_settings (portal-wide, node-specific)
            3. Object's global_portal_settings (object-scoped, shared across nodes)
            4. Object's local_node_settings (object-scoped, node-specific)

        Args:
            key: Configuration key to retrieve.
            default: Value to return if key is not found in any settings store.

        Returns:
            The effective configuration value, or default if not found.
        """
        no_value = object()
        # Check portal-wide settings first (highest priority)
        portal_wide_value = self.portal.get_effective_setting(key, no_value)
        if portal_wide_value is not no_value:
            return portal_wide_value
        # Then check object's global settings
        global_value = self.global_portal_settings.get(key, no_value)
        if global_value is not no_value:
            return global_value
        # Finally check object's local settings
        local_value = self.local_node_settings.get(key, default)
        return local_value


    def _first_visit_to_portal(self, portal: TunablePortal) -> None:
        """Handle the first visit to a portal.

        Args:
            portal: The TunablePortal being visited for the first time.
        """
        super()._first_visit_to_portal(portal)
        # self._persist_initial_config_params(portal)
        local_node_settings = self._get_local_node_settings(portal=portal)

        for key, value in self._auxiliary_config_params_at_init.items():
            local_node_settings[key] = value


    @property
    def portal(self) -> TunablePortal:
        """The TunablePortal associated with this object.

        Returns:
            The portal used by this object's methods.
        """
        return super().portal


    def __setstate__(self, state):
        """Restore object state from pickle.

        Note:
            _auxiliary_config_params_at_init is intentionally reset to an empty
            dict rather than restored from state. This asymmetry with __getstate__
            is by design: config params are persisted to the portal's settings
            on first visit (see _first_visit_to_portal), so after unpickling,
            the object retrieves its effective settings from the portal rather
            than from its internal state.
        """
        super().__setstate__(state)
        self._auxiliary_config_params_at_init = dict()


    def __getstate__(self):
        """Return object state for pickling.

        Note:
            _auxiliary_config_params_at_init is intentionally excluded from
            the serialized state. See __setstate__ for the design rationale.
        """
        return super().__getstate__()
