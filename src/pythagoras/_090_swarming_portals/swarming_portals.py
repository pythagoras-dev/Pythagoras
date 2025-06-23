from __future__ import annotations

import atexit
import os
from time import sleep
import random

import pandas as pd
import parameterizable
from parameterizable import sort_dict_by_keys
from persidict import PersiDict, Joker, KEEP_CURRENT

from .. import get_number_of_known_portals, get_all_known_portals
from .._010_basic_portals import BasicPortal
from .._040_logging_code_portals.logging_portal_core_classes import build_execution_environment_summary
from .._010_basic_portals.basic_portal_core_classes import _describe_runtime_characteristic
from .._800_signatures_and_converters.random_signatures import get_random_signature
from persidict import OverlappingMultiDict
from .._080_pure_code_portals.pure_core_classes import (
    PureCodePortal, PureFnExecutionResultAddr)
from .._800_signatures_and_converters.node_signatures import get_node_signature

from multiprocessing import get_context

from .._090_swarming_portals.output_suppressor import (
    OutputSuppressor)

BACKGROUND_WORKERS_TXT = "Background workers"


class SwarmingPortal(PureCodePortal):
    _compute_nodes: OverlappingMultiDict | None
    _node_id: str | None
    _principal_runtime_id: str | None
    _principal_process_id: int | None
    _principal_runtime_id_at_init: str | None
    _principal_process_id_at_init: int | None
    _is_principal: bool

    def __init__(self
                 , root_dict: PersiDict | str | None = None
                 , p_consistency_checks:float|Joker = KEEP_CURRENT
                 , excessive_logging: bool|Joker = KEEP_CURRENT
                 , max_n_workers: int|Joker = KEEP_CURRENT
                 , principal_runtime_id: str | None = None
                 , principal_process_id: int | None = None
                 ):
        PureCodePortal.__init__(self
            , root_dict=root_dict
            , p_consistency_checks=p_consistency_checks
            , excessive_logging=excessive_logging)

        assert isinstance(max_n_workers, (int, Joker))

        self._ephemeral_config_params_at_init["max_n_workers"
            ] = max_n_workers

        compute_nodes_prototype = self._root_dict.get_subdict("compute_nodes")
        compute_nodes_shared_params = compute_nodes_prototype.get_params()
        dict_type = type(self._root_dict)
        compute_nodes = OverlappingMultiDict(
            dict_type=dict_type
            , shared_subdicts_params=compute_nodes_shared_params
            , json=dict(immutable_items=False)
            , pkl=dict(immutable_items=False)
            )
        self._compute_nodes = compute_nodes

        self._node_id = get_node_signature()

        self._principal_runtime_id_at_init = principal_runtime_id
        self._principal_process_id_at_init = principal_process_id

        if principal_runtime_id is None or principal_process_id is None:
            assert principal_runtime_id is None
            assert principal_process_id is None
            principal_runtime_id = get_random_signature()
            principal_process_id = os.getpid()
            self._principal_runtime_id = principal_runtime_id
            self._principal_process_id = principal_process_id
            self._compute_nodes.pkl[self._runtime_id_address
                ] = principal_runtime_id
            self._is_principal = True
            summary = build_execution_environment_summary()
            self._compute_nodes.json[self._execution_environment_address
                ] = summary
        else:
            self._principal_runtime_id = principal_runtime_id
            self._principal_process_id = principal_process_id
            self._is_principal = False


    def _post_init_hook(self) -> None:
        super()._post_init_hook()

        if get_number_of_known_portals() == 1:
            atexit.register(_clean_runtime_id)

        if self._is_principal:
            for n in range(self.max_n_workers):
                self._launch_background_worker()


    @property
    def _runtime_id_address(self) -> list[str]:
        """Get the address of the runtime id in the compute nodes."""
        return [self._node_id, str(self._principal_process_id), "principal_runtime_id"]


    @property
    def _execution_environment_address(self) -> list[str]:
        """Get the address of the execution environment in the compute nodes."""
        return [self._node_id, str(self._principal_process_id), "execution_environment"]


    @property
    def max_n_workers(self) -> int:
        """Get the maximum number of background workers"""
        n = self._ephemeral_config_params_at_init.get("max_n_workers")
        if n in (None, KEEP_CURRENT):
            n = 3
        return n


    def describe(self) -> pd.DataFrame:
        """Get a DataFrame describing the portal's current state"""
        all_params = [super().describe()]
        all_params.append(_describe_runtime_characteristic(
            BACKGROUND_WORKERS_TXT, self.max_n_workers))

        result = pd.concat(all_params)
        result.reset_index(drop=True, inplace=True)
        return result


    def parent_runtime_is_live(self):
        runtime_id = self._principal_runtime_id
        with self:
            try:
                if runtime_id == self._compute_nodes.pkl[self._runtime_id_address]:
                    return True
            except:
                return False


    def _launch_background_worker(self):
        """Launch one background worker process."""
        init_params = self.get_portable_params()
        init_params["max_n_workers"] = 0
        init_params["principal_runtime_id"] = self._principal_runtime_id
        init_params["principal_process_id"] = self._principal_process_id
        init_params = sort_dict_by_keys(init_params)
        ctx = get_context("spawn")
        p = ctx.Process(target=_background_worker, kwargs=init_params)
        p.start()
        return p


    def _clear(self):
        self._compute_nodes.pkl.delete_if_exists(self._runtime_id_address)
        self._compute_nodes = None
        super()._clear()


    def _randomly_delay_execution(self
            , p:float = 0.5
            , min_delay:float = 0.2 
            , max_delay:float = 1.2
            ) -> None:
        """Randomly delay execution by a given probability."""
        if self.entropy_infuser.uniform(0, 1) < p:
            delay = self.entropy_infuser.uniform(min_delay, max_delay)
            sleep(delay)

parameterizable.register_parameterizable_class(SwarmingPortal)

def _background_worker(**portal_init_params):
    """Background worker that keeps processing random execution requests."""
    portal = parameterizable.get_object_from_portable_params(
        portal_init_params)
    assert isinstance(portal, SwarmingPortal)
    with portal:
        portal._randomly_delay_execution(p=1)
        ctx = get_context("spawn")
        with OutputSuppressor():
            while True:
                if not portal.parent_runtime_is_live():
                    return
                p = ctx.Process(
                    target=_process_random_execution_request
                    , kwargs=portal_init_params)
                p.start()
                p.join()
                portal._randomly_delay_execution()


def _process_random_execution_request(**portal_init_params):
    """Process one random execution request."""
    portal_init_params["max_n_workers"] = 0
    portal = parameterizable.get_object_from_portable_params(
        portal_init_params)
    assert isinstance(portal, SwarmingPortal)
    with portal:
        max_addresses_to_consider = random.randint(200, 5000)
        # TODO: are 200 and 5000 good values for max_addresses_to_consider?
        with OutputSuppressor():
            candidate_addresses = []
            while len(candidate_addresses) == 0:
                if not portal.parent_runtime_is_live():
                    return
                for addr in portal._execution_requests:
                    new_address = PureFnExecutionResultAddr.from_strings(
                        prefix=addr[0], hash_signature=addr[1]
                        ,assert_readiness=False) # How does it handle portals?
                    if not new_address.needs_execution:
                        continue
                    if not new_address.can_be_executed:
                        continue
                    candidate_addresses.append(new_address)
                    if len(candidate_addresses) > max_addresses_to_consider:
                        break
                if len(candidate_addresses) == 0:
                    portal._randomly_delay_execution(p=1)
            random_address = portal.entropy_infuser.choice(candidate_addresses)
            random_address.execute()


def _clean_runtime_id():
    """ Clean runtime id.

    This function is called at the end of the program execution.
    It deletes the principal_runtime_id record from all portals.
    """
    for portal in get_all_known_portals():
        try:
            if portal._is_principal:
                portal._compute_nodes.pkl.delete_if_exists(
                    portal._runtime_id_address)
        except:
            pass