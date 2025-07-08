""" Classes and functions that enable swarming algorithm.

Pythagoras provides infrastructure for remote execution of
pure functions in distributed environments. Pythagoras employs
an asynchronous execution model called 'swarming':
you do not know when your function will be executed,
what machine will execute it, and how many times it will be executed.
Pythagoras ensures that the function will be eventually executed
at least once but does not offer any further guarantees.
"""

from __future__ import annotations

import atexit
from time import sleep

import pandas as pd
import parameterizable
from parameterizable import sort_dict_by_keys
from persidict import PersiDict, Joker, KEEP_CURRENT

from .._010_basic_portals import get_all_known_portals
from .._070_protected_code_portals.system_utils import get_unused_ram_mb, get_unused_cpu_cores, process_is_active, \
    get_process_start_time, get_current_process_id, get_current_process_start_time
from .._040_logging_code_portals.logging_portal_core_classes import build_execution_environment_summary
from .._010_basic_portals.basic_portal_core_classes import _describe_runtime_characteristic
from persidict import OverlappingMultiDict
from .._080_pure_code_portals.pure_core_classes import (
    PureCodePortal, PureFnExecutionResultAddr)
from .._800_signatures_and_converters.node_signature import get_node_signature

from multiprocessing import get_context

from .._090_swarming_portals.output_suppressor import (
    OutputSuppressor)

BACKGROUND_WORKERS_TXT = "Background workers"


class SwarmingPortal(PureCodePortal):
    _compute_nodes: OverlappingMultiDict | None
    _node_id: str | None

    _parent_process_id: int | None
    _parent_process_start_time: float | None
    _is_parent: bool | None

    _atexit_is_registered: bool = False

    def __init__(self
                 , root_dict: PersiDict | str | None = None
                 , p_consistency_checks:float|Joker = KEEP_CURRENT
                 , excessive_logging: bool|Joker = KEEP_CURRENT
                 , max_n_workers: int|Joker = KEEP_CURRENT
                 , parent_process_id: int | None = None
                 , parent_process_start_time: float | None = None
                 ):
        PureCodePortal.__init__(self
            , root_dict=root_dict
            , p_consistency_checks=p_consistency_checks
            , excessive_logging=excessive_logging)

        assert isinstance(max_n_workers, (int, Joker))

        if parent_process_id is None or parent_process_start_time is None:
            assert parent_process_id is None
            assert parent_process_start_time is None
            self._ephemeral_config_params_at_init["max_n_workers"
                ] = max_n_workers
        else:
            assert max_n_workers == 0

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
        self._parent_process_id = parent_process_id
        self._parent_process_start_time = parent_process_start_time
        self._child_process = None


    @property
    def is_parent(self) -> bool:
        """Check if this portal is the parent process."""
        if self._parent_process_id is None:
            return True
        return False


    def _post_init_hook(self) -> None:
        super()._post_init_hook()

        if not SwarmingPortal._atexit_is_registered:
            atexit.register(_terminate_all_portals_child_processes)
            SwarmingPortal._atexit_is_registered = True

        if self.is_parent:
            if self.max_n_workers > 0:

                portal_init_params = self.get_portable_params()
                portal_init_params["max_n_workers"] = self.max_n_workers
                portal_init_params = sort_dict_by_keys(portal_init_params)

                ctx = get_context("spawn")
                self._child_process = ctx.Process(
                    target=_launch_many_background_workers
                    , kwargs=portal_init_params)
                self._child_process.start()


    def _terminate_child_process(self):
        """Terminate the child process if it is running."""
        if self._child_process is not None:
            if self._child_process.is_alive():
                self._child_process.terminate()
                self._child_process.join(3)
                if self._child_process.is_alive():
                    self._child_process.kill()
                    self._child_process.join()
        self._child_process = None


    @property
    def _execution_environment_address(self) -> list[str]: #TODO: move to Logs
        """Get the address of the execution environment in the compute nodes."""
        s = str(self._parent_process_id) + "_" + str(self._parent_process_start_time)
        return [self._node_id, s, "execution_environment"]


    @property
    def max_n_workers(self) -> int:
        """Get the maximum number of background workers"""
        if not hasattr(self, "_max_n_workers_cache"):
            n = self._get_config_setting("max_n_workers")
            if n in (None, KEEP_CURRENT):
                n = 10
            n = min(n, get_unused_cpu_cores() + 2)
            n = min(n, get_unused_ram_mb() / 500)
            n = int(n)
            self._max_n_workers_cache = n

        return self._max_n_workers_cache


    def describe(self) -> pd.DataFrame:
        """Get a DataFrame describing the portal's current state"""
        all_params = [super().describe()]
        all_params.append(_describe_runtime_characteristic(
            BACKGROUND_WORKERS_TXT, self.max_n_workers))

        result = pd.concat(all_params)
        result.reset_index(drop=True, inplace=True)
        return result


    def parent_runtime_is_live(self):
        if not process_is_active(self._parent_process_id):
            return False
        if get_process_start_time(self._parent_process_id) != self._parent_process_start_time:
            return False
        return True


    def _clear(self):
        self._compute_nodes = None
        self._terminate_child_process()
        super()._clear()


    def _randomly_delay_execution(self
            , p:float = 0.5
            , min_delay:float = 0.02
            , max_delay:float = 0.22
            ) -> None:
        """Randomly delay execution by a given probability."""
        if self.entropy_infuser.uniform(0, 1) < p:
            delay = self.entropy_infuser.uniform(min_delay, max_delay)
            sleep(delay)


    def _invalidate_cache(self):
        """Invalidate the object's attribute cache.

        If the object's attribute named ATTR is cached,
        its cached value will be stored in an attribute named _ATTR_cache
        This method should delete all such attributes.
        """
        if hasattr(self, "_max_n_workers_cache"):
            del self._max_n_workers_cache
        super()._invalidate_cache()

parameterizable.register_parameterizable_class(SwarmingPortal)


def _launch_many_background_workers(**portal_init_params) -> None:
    """Launch many background worker processes."""
    n_workers_to_launch = portal_init_params["max_n_workers"]
    n_workers_to_launch = int(n_workers_to_launch)

    portal_init_params["max_n_workers"] = 0
    current_process_id = get_current_process_id()
    portal_init_params["parent_process_id"] = current_process_id
    portal_init_params["parent_process_start_time"
        ] = get_current_process_start_time()
    portal_init_params = sort_dict_by_keys(portal_init_params)
    portal = parameterizable.get_object_from_portable_params(
        portal_init_params)
    assert isinstance(portal, SwarmingPortal)

    summary = build_execution_environment_summary()
    portal._compute_nodes.json[portal._execution_environment_address] = summary

    list_of_all_workers = []

    with portal:
        for i in range(n_workers_to_launch):
            portal._randomly_delay_execution(p=1)
            ctx = get_context("spawn")
            try:
                p = ctx.Process(target=_background_worker, kwargs=portal_init_params)
                p.start()
                list_of_all_workers.append(p)
            except Exception as e:
                break

    with portal:
        while True:
            portal._randomly_delay_execution(p=1)
            new_list_of_all_workers = []
            for worker in list_of_all_workers:
                if  worker.is_alive():
                    new_list_of_all_workers.append(worker)
                else:
                    portal._randomly_delay_execution(p=1)
                    ctx = get_context("spawn")
                    try:
                        p = ctx.Process(target=_background_worker, kwargs=portal_init_params)
                        p.start()
                        new_list_of_all_workers.append(p)
                    except Exception as e:
                        break
            list_of_all_workers = new_list_of_all_workers


def _background_worker(**portal_init_params) -> None:
    """Background worker that keeps processing random execution requests."""
    portal = parameterizable.get_object_from_portable_params(
        portal_init_params)
    assert isinstance(portal, SwarmingPortal)
    with portal:
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
    portal = parameterizable.get_object_from_portable_params(
        portal_init_params)
    assert isinstance(portal, SwarmingPortal)
    with portal:

        while True:
            addr = portal._execution_requests.random_key()
            if addr is None:
                portal._randomly_delay_execution()
                continue
            new_address = PureFnExecutionResultAddr.from_strings(
                descriptor=addr[2], hash_signature=addr[0]+addr[1]+addr[3]
                ,assert_readiness=False)
            if not new_address.needs_execution:
                continue
            if not new_address.can_be_executed:
                continue
            with OutputSuppressor():
                new_address.execute()
            return

        # max_addresses_to_consider = random.randint(200, 5000)
        # # TODO: are 200 and 5000 good values for max_addresses_to_consider?
        # with OutputSuppressor():
        #     candidate_addresses = []
        #     while len(candidate_addresses) == 0:
        #         if not portal.parent_runtime_is_live():
        #             return
        #         for addr in portal._execution_requests:
        #             new_address = PureFnExecutionResultAddr.from_strings(
        #                 prefix=addr[0], hash_signature=addr[1]
        #                 ,assert_readiness=False) # How does it handle portals?
        #             if not new_address.needs_execution:
        #                 continue
        #             if not new_address.can_be_executed:
        #                 continue
        #             candidate_addresses.append(new_address)
        #             if len(candidate_addresses) > max_addresses_to_consider:
        #                 break
        #         if len(candidate_addresses) == 0:
        #             portal._randomly_delay_execution(p=1)
        #     random_address = portal.entropy_infuser.choice(candidate_addresses)
        #     random_address.execute()


def _terminate_all_portals_child_processes():
    """ Clean runtime id.

    This function is called at the end of the program execution.
    It deletes the principal_runtime_id record from all portals.
    """
    for portal in get_all_known_portals():
        try:
            portal._terminate_child_process()
        except:
            pass