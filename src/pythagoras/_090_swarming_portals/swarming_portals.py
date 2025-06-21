from __future__ import annotations

import atexit
from time import sleep
import random

import pandas as pd
import parameterizable
from persidict import PersiDict, Joker, KEEP_CURRENT

from .._010_basic_portals.basic_portal_class_OLD import BasicPortal
from .._040_logging_code_portals.logging_portal_core_classes import build_execution_environment_summary
from .._010_basic_portals.basic_portal_class_OLD import _describe_runtime_characteristic
from .._820_strings_signatures_converters.random_signatures import get_random_signature
from .._800_persidict_extensions.overlapping_multi_dict import (
    OverlappingMultiDict)
from .._080_pure_code_portals.pure_core_classes import (
    PureCodePortal, PureFnExecutionResultAddr)
# from pythagoras._090_swarming_portals.clean_runtime_id import clean_runtime_id
from .._820_strings_signatures_converters.node_signatures import get_node_signature

from multiprocessing import get_context

from .._810_output_manipulators.output_suppressor import (
    OutputSuppressor)

BACKGROUND_WORKERS_TXT = "Background workers"


class SwarmingPortal(PureCodePortal):
    compute_nodes: OverlappingMultiDict | None

    def __init__(self
                 , root_dict: PersiDict | str | None = None
                 , p_consistency_checks:float|Joker = KEEP_CURRENT
                 , excessive_logging: bool|Joker = KEEP_CURRENT
                 , n_background_workers:int|None = 3
                 , runtime_id:str|None = None
                 ):
        PureCodePortal.__init__(self
            , root_dict=root_dict
            , p_consistency_checks=p_consistency_checks
            , excessive_logging=excessive_logging)
        n_background_workers = int(n_background_workers)
        assert n_background_workers >= 0
        self.n_background_workers = n_background_workers

        compute_nodes_prototype = self._root_dict.get_subdict("compute_nodes")
        compute_nodes_shared_params = compute_nodes_prototype.get_params()
        dict_type = type(self._root_dict)
        compute_nodes = OverlappingMultiDict(
            dict_type=dict_type
            , shared_subdicts_params=compute_nodes_shared_params
            , json=dict(immutable_items=False)
            , pkl=dict(immutable_items=False)
            )
        self.compute_nodes = compute_nodes

        self.node_id = get_node_signature()

        if runtime_id is None:
            runtime_id = get_random_signature()
            self.runtime_id = runtime_id
            address = [self.node_id, "runtime_id"]
            self.compute_nodes.pkl[address] = runtime_id
            # for portal in self.get_noncurrent_portals():
            #     portal.compute_nodes.pkl[address] = runtime_id

            if len(BasicPortal._all_portals) == 1:
                atexit.register(_clean_runtime_id)

            summary = build_execution_environment_summary()
            address = [self.node_id, "execution_environment"]
            self.compute_nodes.json[address] = summary
            # for portal in self.get_noncurrent_portals():
            #     portal.compute_nodes.json[address] = summary
        else:
            self.runtime_id = runtime_id

        for n in range(n_background_workers):
            self._launch_background_worker()


    def get_params(self) -> dict:
        """Get the portal's configuration parameters"""
        params = super().get_params()
        params["n_background_workers"]=self.n_background_workers
        params["runtime_id"]=self.runtime_id
        return params

    def describe(self) -> pd.DataFrame:
        """Get a DataFrame describing the portal's current state"""
        all_params = [super().describe()]
        all_params.append(_describe_runtime_characteristic(
            BACKGROUND_WORKERS_TXT, self.n_background_workers))

        result = pd.concat(all_params)
        result.reset_index(drop=True, inplace=True)
        return result


    def parent_runtime_is_live(self):
        node_id = get_node_signature()
        address = [node_id, "runtime_id"]
        runtime_id = self.runtime_id
        with self:
            try:
                if runtime_id == self.compute_nodes.pkl[address]:
                    return True
            except:
                pass
        # for portal in BasicPortal._all_known_portals.values():
        #     try:
        #         with portal:
        #             if runtime_id == portal.compute_nodes.pkl[address]:
        #                 return True
        #     except:
        #         pass
        return False


    def _launch_background_worker(self):
        """Launch one background worker process."""
        init_params = self.get_portable_params()
        init_params["n_background_workers"] = 0
        ctx = get_context("spawn")
        p = ctx.Process(target=_background_worker, kwargs=init_params)
        p.start()
        return p


    def _clear(self):
        address = [self.node_id, "runtime_id"]
        self.compute_nodes.pkl.delete_if_exists(address)
        self.compute_nodes = None
        super()._clear()


    @classmethod
    def _clear_all(cls):
        super()._clear_all()


    # @classmethod
    # def get_best_portal_to_use(cls, suggested_portal: PureCodePortal | None = None
    #                            ) -> SwarmingPortal:
    #     return BasicPortal.get_best_portal_to_use(suggested_portal)
    #
    #
    # @classmethod
    # def get_most_recently_entered_portal(cls) -> SwarmingPortal | None:
    #     """Get the current portal object"""
    #     return BasicPortal._most_recently_entered_portal(expected_type=cls)
    #
    #
    # @classmethod
    # def get_noncurrent_portals(cls) -> list[SwarmingPortal]:
    #     """Get all portals except the most recently entered one"""
    #     return BasicPortal._noncurrent_portals(expected_type=cls)
    #
    #
    # @classmethod
    # def get_entered_portals(cls) -> list[SwarmingPortal]:
    #     return BasicPortal._entered_portals(expected_type=cls)

    def _randomly_delay_execution(self
            , p:float = 0.5
            , min_delay:float = 0.2 
            , max_delay:float = 1.2
            ) -> None:
        """Randomly delay execution by a given probability."""
        if self.entropy_infuser.uniform(0, 1) < p:
            delay = self.entropy_infuser.uniform(min_delay, max_delay)
            sleep(delay)

parameterizable.register_parameterizable_class(SwarmingPortal) #TODO: is it needed?

def _background_worker(**portal_init_params):
    """Background worker that keeps processing random execution requests."""
    portal_init_params["n_background_workers"] = 0
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
    portal_init_params["n_background_workers"] = 0
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
                        ,assert_readiness=False
                        ,portal = portal) # How does it handle portals?
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
    It deletes the runtime_id record from all portals.
    """
    node_id = get_node_signature()
    address = [node_id, "runtime_id"]
    for portal_id in BasicPortal._all_portals:
        try:
            portal = BasicPortal._all_portals[portal_id]
            with portal:
                portal.compute_nodes.pkl.delete_if_exists(address)
        except:
            pass