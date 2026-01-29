"""Classes and functions enabling asynchronous swarming execution.

Pythagoras enables distributed execution of pure functions across multiple
processes and machines using an asynchronous model called 'swarming'. The
swarming model provides eventual execution guarantees without deterministic
timing, worker assignment, or execution count. Functions are guaranteed to
execute at least once, but may execute multiple times across different workers.

This module implements SwarmingPortal, which manages background worker pools
and coordinates distributed execution through a best-effort dispatching
mechanism.
"""

from __future__ import annotations

import atexit
from time import sleep
from typing import Final

import pandas as pd
import mixinforge

from persidict import PersiDict, Joker, KEEP_CURRENT

from mixinforge import *

from .._210_basic_portals import get_known_portals
from .._350_protected_code_portals import (VALIDATION_SUCCESSFUL,
                                           get_unused_ram_mb, get_unused_cpu_cores)
from .._210_basic_portals.basic_portal_core_classes import _describe_runtime_characteristic
from persidict import OverlappingMultiDict
from .._360_pure_code_portals.pure_core_classes import (
    PureCodePortal, PureFnExecutionResultAddr, PureFnCallSignature)

from multiprocessing import get_context
from .descendant_process_info import *
from .system_processes_info_getters import *


from .._110_supporting_utilities import get_long_infoname


_MAX_BACKGROUND_WORKERS_TXT: Final[str] = "Max Background workers"
_MIN_BACKGROUND_WORKERS_TXT: Final[str] = "Min Background workers"
_EXACT_BACKGROUND_WORKERS_TXT: Final[str] = "Exact Background workers"
_ANCESTOR_PROCESS_ID_TXT: Final[str] = "Ancestor Process ID"
_ANCESTOR_PROCESS_START_TIME_TXT: Final[str] = "Ancestor Process Start Time"


class SwarmingPortal(PureCodePortal):
    """Portal for asynchronous swarming execution of pure functions.

    Distributes execution of registered pure functions across background worker
    processes with eventual consistency guarantees. The portal spawns a child
    process that maintains a worker pool and randomly dispatches execution
    requests. Workers run independently and may execute tasks multiple times,
    but every eligible request will eventually execute at least once.

    The portal distinguishes between ancestor and descendant processes:
    the ancestor is the original portal instance created by user code,
    while descendants are worker processes spawned to execute tasks.

    Attributes:
        max_n_workers: Maximum number of background workers to spawn.
        min_n_workers: Minimum number of background workers to maintain.
        exact_n_workers: Fixed number of workers, overriding min/max when set.
        ancestor_process_id: PID of the ancestor process for descendant tracking.
        ancestor_process_start_time: Start time of ancestor for PID reuse detection.

    Note:
        Worker output is suppressed to prevent noise. Use OutputSuppressor
        directly for custom control.
    """
    _compute_nodes: OverlappingMultiDict | None
    _node_id: str | None

    _ancestor_process_id: int | None
    _ancestor_process_start_time: int | None

    _atexit_is_registered: bool = False

    def __init__(self
                 , root_dict: PersiDict | str | None = None
                 , excessive_logging: bool|Joker = KEEP_CURRENT
                 , max_n_workers: int|Joker|None = KEEP_CURRENT
                 , min_n_workers: int|Joker|None = KEEP_CURRENT
                 , exact_n_workers: int|None = None
                 , ancestor_process_id: int | None = None
                 , ancestor_process_start_time: int | None = None
                 ):
        """Initialize a swarming portal.

        Args:
            root_dict: Persistent storage backing portal state, or None for default.
            excessive_logging: Whether to enable verbose diagnostic logging.
            max_n_workers: Upper bound on background workers. Actual count may be
                lower based on available CPUs and RAM.
            min_n_workers: Lower bound on background workers. Actual count may be
                higher based on resource availability.
            exact_n_workers: Fixed worker count, overriding min and max when set.
                When None, worker count is dynamically determined.
            ancestor_process_id: PID of the ancestor process. Must be None for
                ancestor portals, required for descendants.
            ancestor_process_start_time: Unix timestamp of ancestor start time,
                preventing PID reuse issues. Must match ancestor_process_id.

        Raises:
            TypeError: If worker count parameters have incorrect types.
            ValueError: If worker counts are negative or exact_n_workers conflicts
                with min/max settings.
            RuntimeError: If ancestor_process_id and ancestor_process_start_time
                are inconsistently set.
        """
        PureCodePortal.__init__(self
            , root_dict=root_dict
            , excessive_logging=excessive_logging)

        if not isinstance(max_n_workers, (int, Joker, type(None))):
            raise TypeError(f"max_n_workers must be int or Joker or None, "
                            f"got {get_long_infoname(max_n_workers)}")
        if not isinstance(min_n_workers, (int, Joker, type(None))):
            raise TypeError(f"min_n_workers must be int or Joker or None, "
                            f"got {get_long_infoname(min_n_workers)}")
        if not isinstance(exact_n_workers, (int, type(None))):
            raise TypeError(f"exact_n_workers must be int or None, "
                            f"got {get_long_infoname(exact_n_workers)}")


        if max_n_workers not in (None, KEEP_CURRENT) and max_n_workers < 0:
            raise ValueError("max_n_workers cannot be negative")
        if min_n_workers not in (None, KEEP_CURRENT) and min_n_workers < 0:
            raise ValueError("min_n_workers cannot be negative")
        if exact_n_workers not in (None, 0) and exact_n_workers < 0:
            raise ValueError("exact_n_workers cannot be negative")


        if ancestor_process_id is not None:
            # the portal is being created in a descendant process
            # insise _launch_many_background_workers
            # or _background_worker or _process_random_execution_request
            if ancestor_process_start_time is None:
                raise RuntimeError(
                    f"ancestor_process_id and ancestor_process_start_time must "
                    f"both be None or both set; got id={ancestor_process_id}, "
                    f"start_time={ancestor_process_start_time}")
        else:
            if ancestor_process_start_time is not None:
                raise RuntimeError(
                    f"ancestor_process_id and ancestor_process_start_time must "
                    f"both be None or both set; got id={ancestor_process_id}, "
                    f"start_time={ancestor_process_start_time}")
            if exact_n_workers not in (None, 0):
                if max_n_workers is not None and max_n_workers is not KEEP_CURRENT:
                    raise ValueError("If exact_n_workers is set, max_n_workers must be None")
                if min_n_workers is not None and min_n_workers is not KEEP_CURRENT:
                    raise ValueError("If exact_n_workers is set, min_n_workers must be None")

        self._auxiliary_config_params_at_init["max_n_workers"] = max_n_workers
        self._auxiliary_config_params_at_init["min_n_workers"] = min_n_workers
        self._auxiliary_config_params_at_init["exact_n_workers"] = exact_n_workers

        self._ancestor_process_id = ancestor_process_id
        self._ancestor_process_start_time = ancestor_process_start_time

        self._all_workers = self.local_node_value_store.get_subdict("all_workers")


    @property
    def auxiliary_param_names(self) -> set[str]:
        """Parameter names excluded from hash-based identity comparison.

        Returns:
            Set of parameter names including ancestor process identifiers.
        """
        names = super().auxiliary_param_names
        names.update({"ancestor_process_id","ancestor_process_start_time"})
        return names


    def register_descendant_process(self, process_type:str, process_id:int, process_start_time:int):
        """Register a descendant worker process for tracking and cleanup.

        Args:
            process_type: Descriptive label for the process role.
            process_id: PID of the descendant process.
            process_start_time: Unix timestamp when the process started.

        Raises:
            TypeError: If parameters have incorrect types.
            ValueError: If process_type is empty, process_id is non-positive,
                or process_start_time is invalid.
        """
        # Validate inputs
        if not isinstance(process_type, str):
            raise TypeError(f"process_type must be a string, got {get_long_infoname(process_type)}")
        if not process_type:
            raise ValueError("process_type cannot be empty")

        if not isinstance(process_id, int):
            raise TypeError(f"process_id must be an integer, got {get_long_infoname(process_id)}")
        if process_id <= 0:
            raise ValueError(f"process_id must be positive, got {process_id}")

        if not isinstance(process_start_time, int):
            raise TypeError(f"process_start_time must be an integer, got {get_long_infoname(process_start_time)}")
        validate_process_start_time(process_start_time, "process_start_time")

        # Use self.ancestor_process_id if available (for descendant portals),
        # otherwise use current process ID (for ancestor portals)
        if self.ancestor_process_id is not None:
            ancestor_process_id = self.ancestor_process_id
            ancestor_process_start_time = self.ancestor_process_start_time
        else:
            ancestor_process_id = get_current_process_id()
            ancestor_process_start_time = get_current_process_start_time()

        process_info = DescendantProcessInfo(
            process_id=process_id,
            process_start_time=process_start_time,
            ancestor_process_id=ancestor_process_id,
            ancestor_process_start_time=ancestor_process_start_time,
            process_type=process_type)
        address = (str(process_info.process_id),
                   str(process_info.process_start_time))
        self._all_workers[address] = process_info


    @property
    def ancestor_process_id(self) -> int | None:
        """PID of the ancestor process, or None if this is the ancestor."""
        return self._ancestor_process_id


    @property
    def ancestor_process_start_time(self) -> int | None:
        """Start time of the ancestor process, or None if this is the ancestor."""
        return self._ancestor_process_start_time

    @property
    def max_n_workers(self) -> int:
        """Maximum number of background workers to spawn."""
        return self.get_effective_setting("max_n_workers")

    @property
    def min_n_workers(self) -> int:
        """Minimum number of background workers to maintain."""
        return self.get_effective_setting("min_n_workers")

    @property
    def exact_n_workers(self) -> int:
        """Fixed number of workers when set, overriding min/max bounds."""
        return self.get_effective_setting("exact_n_workers")


    def get_active_descendant_process_counter(self,
            process_type: str | None = None) -> int:
        """Count alive descendant processes and remove dead ones.

        Iterates through tracked descendant processes, verifies they are still
        running, and removes stale entries. Only counts descendants belonging to
        the current ancestor lineage.

        Args:
            process_type: Filter by process role. When None, counts all alive workers.

        Returns:
            Number of alive descendant processes matching the filter.

        Raises:
            TypeError: If process_type is not a string or None.
            ValueError: If process_type is an empty string.
        """

        if process_type is not None and not isinstance(process_type, str):
            raise TypeError("process_type must be a string or None")
        if process_type == "":
            raise ValueError("process_type cannot be an empty string")

        ancestor_process_id = self.ancestor_process_id
        ancestor_process_start_time = self.ancestor_process_start_time
        if ancestor_process_id is None:
            ancestor_process_id = get_current_process_id()
            ancestor_process_start_time = get_current_process_start_time()

        counter = 0
        dead_addresses = []

        for worker_address, worker in self._all_workers.items():
            if len(worker_address) != 2:
                raise RuntimeError("Unexpected worker address format: "
                                   f"{worker_address}")
            if not isinstance(worker, DescendantProcessInfo):
                raise RuntimeError(f"Unexpected worker type: "
                                   f"{get_long_infoname(worker)}")

            if not worker.is_alive():
                dead_addresses.append(worker_address)
            elif process_type is None or worker.process_type == process_type:
                if worker.ancestor_process_id == ancestor_process_id:
                    if worker.ancestor_process_start_time == ancestor_process_start_time:
                        counter += 1

        for addr in dead_addresses:
            self._all_workers.discard(addr)

        return counter


    def get_params(self) -> dict:
        """Return portal configuration parameters.

        Returns:
            Sorted dictionary of portal parameters.
        """
        params = super().get_params()
        params["ancestor_process_id"] = self.ancestor_process_id
        params["ancestor_process_start_time"] = self.ancestor_process_start_time
        sorted_params = sort_dict_by_keys(params)
        return sorted_params


    @property
    def is_ancestor(self) -> bool:
        """True if this is the original portal instance, False if a worker descendant."""
        if self.ancestor_process_id is None:
            return True
        else:
            return False

    @property
    def n_workers_to_target(self) -> int:
        """Compute target worker count based on configuration and system resources.

        Uses exact_n_workers if set; otherwise dynamically calculates based on
        available CPU cores and RAM, bounded by min_n_workers and max_n_workers.

        Returns:
            Target number of workers to maintain, at least 0.
        """
        if self.exact_n_workers is not None:
            result =  self.exact_n_workers
        else:
            n = self.max_n_workers
            if n in (None, KEEP_CURRENT):
                n = 10
            n = min(n, int(get_unused_cpu_cores()) + 2)
            n = min(n, int(get_unused_ram_mb() / 500))
            n = int(n)

            min_n_workers = self.min_n_workers
            if min_n_workers in (None, KEEP_CURRENT):
                min_n_workers = 0

            if n < min_n_workers:
                n = min_n_workers

            result= max(0, n)

        return result


    def __post_init__(self) -> None:
        """Complete portal initialization and spawn worker management process.

        Registers a global atexit handler for process cleanup. Ancestor portals
        with positive target worker counts spawn a child process that maintains
        the background worker pool.
        """
        super().__post_init__()

        if not SwarmingPortal._atexit_is_registered:
            atexit.register(_terminate_all_portals_descendant_processes)
            SwarmingPortal._atexit_is_registered = True

        if self.is_ancestor:
            if self.n_workers_to_target > 0:

                portal_init_jsparams = mixinforge.dumpjs(self)
                portal_init_jsparams = update_jsparams(
                    portal_init_jsparams,
                    exact_n_workers = self.n_workers_to_target,
                    max_n_workers = KEEP_CURRENT,
                    min_n_workers = KEEP_CURRENT,
                    ancestor_process_id = get_current_process_id(),
                    ancestor_process_start_time = get_current_process_start_time())

                ctx = get_context("spawn")
                workers_launcher = ctx.Process(
                    target=_launch_many_background_workers
                    , args=(portal_init_jsparams,))
                workers_launcher.start()

                # Register the workers_launcher process from outside
                launcher_pid = workers_launcher.pid
                launcher_start_time = get_process_start_time_with_retry(launcher_pid)
                self.register_descendant_process(
                    "_launch_many_background_workers",
                    launcher_pid,
                    launcher_start_time)


    def _terminate_descendant_processes(self):
        """Terminate descendant workers belonging to this ancestor and clean up dead processes.

        Raises:
            RuntimeError: If called from a descendant process.
        """
        if not self.is_ancestor:
            raise RuntimeError("This method should only be called "
                               "from the ancestor process")

        workers_to_terminate, adresses_to_discard = list(),list()
        current_process_id = get_current_process_id()
        current_process_start_time = get_current_process_start_time()

        for address, worker in self._all_workers.items():
            if not worker.is_alive():
                adresses_to_discard.append(address)
            elif worker.ancestor_process_id == current_process_id:
                if worker.ancestor_process_start_time == current_process_start_time:
                    workers_to_terminate.append(worker)

        for address in adresses_to_discard:
            self._all_workers.discard(address)
        for worker in workers_to_terminate:
            try:
                address = (str(worker.process_id), str(worker.process_start_time))
                worker.terminate()
                self._all_workers.discard(address)
            except Exception:
                # Best-effort: ensure we don't keep stale tracking records
                pass


    def describe(self) -> pd.DataFrame:
        """Return portal configuration and runtime characteristics as a table.

        Returns:
            DataFrame with portal settings including worker counts and ancestor metadata.
        """
        all_params = [super().describe()]
        all_params.append(_describe_runtime_characteristic(
            _MAX_BACKGROUND_WORKERS_TXT, self.max_n_workers))
        all_params.append(_describe_runtime_characteristic(
            _MIN_BACKGROUND_WORKERS_TXT, self.min_n_workers))
        all_params.append(_describe_runtime_characteristic(
            _EXACT_BACKGROUND_WORKERS_TXT, self.exact_n_workers))
        all_params.append(_describe_runtime_characteristic(
            _ANCESTOR_PROCESS_ID_TXT, self.ancestor_process_id))
        all_params.append(_describe_runtime_characteristic(
            _ANCESTOR_PROCESS_START_TIME_TXT, self.ancestor_process_start_time))


        result = pd.concat(all_params)
        result.reset_index(drop=True, inplace=True)
        return result


    def ancestor_runtime_is_live(self):
        """Check whether the ancestor process is still running.

        Verifies both PID existence and start time to prevent PID reuse false positives.

        Returns:
            True if the ancestor process is alive; False otherwise.
        """
        return process_is_alive(
            process_id=self.ancestor_process_id,
            process_start_time = self.ancestor_process_start_time)


    def _clear(self):
        """Release resources and terminate descendant processes.

        Ancestor portals terminate their workers before cleanup. The portal must
        not be used after calling this method.
        """
        # self._compute_nodes = None
        if self.is_ancestor:
            self._terminate_descendant_processes()
        super()._clear()


    def _randomly_delay_execution(self
            , p:float = 0.5
            , min_delay:float = 0.02
            , max_delay:float = 0.22
            ) -> None:
        """Introduce random delay to reduce worker contention.

        Sleeps with probability p for a uniform random duration between min_delay
        and max_delay. Uses portal entropy_infuser for deterministic behavior in tests.

        Args:
            p: Probability of delaying, between 0 and 1.
            min_delay: Minimum delay duration in seconds.
            max_delay: Maximum delay duration in seconds.

        Raises:
            ValueError: If p is outside [0,1] or max_delay < min_delay or min_delay < 0.
        """
        if not 0 <= p <= 1:
            raise ValueError("p must be between 0 and 1")
        if min_delay < 0:
            raise ValueError("min_delay cannot be negative")
        if max_delay < min_delay:
            raise ValueError("max_delay must be >= min_delay")

        if self.entropy_infuser.uniform(0, 1) < p:
            delay = self.entropy_infuser.uniform(min_delay, max_delay)
            sleep(delay)


def _launch_many_background_workers(portal_init_jsparams:JsonSerializedObject) -> None:
    """Maintain target worker pool by spawning workers as needed.

    Runs indefinitely in a dedicated child process, monitoring active workers
    and spawning new ones when the count falls below the target. Restarts workers
    that exit unexpectedly.

    Args:
        portal_init_jsparams: Serialized portal configuration with ancestor metadata.
    """

    portal = mixinforge.loadjs(portal_init_jsparams)
    if not isinstance(portal, SwarmingPortal):
        raise TypeError(f"Expected SwarmingPortal, got {get_long_infoname(portal)}")
    # summary = build_execution_environment_summary()
    # portal._compute_nodes.json[portal._execution_environment_address] = summary

    with portal:
        while True:
            if not portal.ancestor_runtime_is_live():
                return
            current_n_workers = portal.get_active_descendant_process_counter("_background_worker")
            n_workers_to_launch = max(0, portal.n_workers_to_target - current_n_workers)
            if n_workers_to_launch > 0:
                try:
                    ctx = get_context("spawn")
                    p = ctx.Process(target=_background_worker, args=(portal_init_jsparams,))
                    p.start()

                    # Register the background worker process from outside
                    worker_pid = p.pid
                    worker_start_time = get_process_start_time_with_retry(worker_pid)
                    portal.register_descendant_process(
                        "_background_worker",
                        worker_pid,
                        worker_start_time)
                except Exception:
                    pass
            portal._randomly_delay_execution(p=1)


def _background_worker(portal_init_jsparams:JsonSerializedObject) -> None:
    """Process execution requests in an infinite loop until ancestor dies.

    Each request is handled in a subprocess for isolation. Worker output is
    suppressed to avoid noise.

    Args:
        portal_init_jsparams: Serialized portal configuration for reconstruction.
    """
    portal = mixinforge.loadjs(portal_init_jsparams)
    if not isinstance(portal, SwarmingPortal):
        raise TypeError(f"Expected SwarmingPortal, got {get_long_infoname(portal)}")
    with portal:
        ctx = get_context("spawn")
        with OutputSuppressor():
            while True:
                if not portal.ancestor_runtime_is_live():
                    return
                p = ctx.Process(
                    target=_process_random_execution_request
                    , args=(portal_init_jsparams,))
                p.start()
                p.join()
                portal._randomly_delay_execution()


def _process_random_execution_request(portal_init_jsparams:JsonSerializedObject):
    """Select and execute a random pending request if ancestor is alive.

    Continuously validates request readiness, following dependency chains when
    validation returns PureFnCallSignature. Executes when validation succeeds.
    Returns immediately if the ancestor process dies.

    Args:
        portal_init_jsparams: Serialized portal configuration for reconstruction.
    """
    portal = mixinforge.loadjs(portal_init_jsparams)
    if not isinstance(portal, SwarmingPortal):
        raise TypeError(f"Expected SwarmingPortal, got {get_long_infoname(portal)}")
    with portal:
        call_signature:PureFnCallSignature|None = None
        while True:
            if not portal.ancestor_runtime_is_live():
                return
            if call_signature is not None:
                pre_validation_result = call_signature.fn.can_be_executed(
                    call_signature.packed_kwargs)
                if isinstance(pre_validation_result, PureFnCallSignature):
                    call_signature = pre_validation_result
                    continue
                elif pre_validation_result is VALIDATION_SUCCESSFUL:
                    call_signature.fn.execute(**call_signature.packed_kwargs)
                    return
                else:
                    call_signature = None
                    continue
            else:
                addr = portal._execution_requests.random_key()
                if addr is None:
                    portal._randomly_delay_execution()
                    continue
                new_address = PureFnExecutionResultAddr.from_strings(
                    descriptor=addr[2], hash_signature=addr[0]+addr[1]+addr[3]
                    ,assert_readiness=False)
                if not new_address.needs_execution:
                    continue
                pre_validation_result =  new_address.can_be_executed
                if isinstance(pre_validation_result, PureFnCallSignature):
                    call_signature = pre_validation_result
                    continue
                elif pre_validation_result is not VALIDATION_SUCCESSFUL:
                    continue
                with OutputSuppressor():
                    new_address.execute()
                return


def _terminate_all_portals_descendant_processes():
    """Clean up descendant processes for all portals at program exit.

    Registered via atexit during first SwarmingPortal initialization. Prevents
    orphaned worker processes.
    """
    for portal in get_known_portals():
        try:
            portal._terminate_descendant_processes()
        except Exception:
            # Best-effort cleanup; ignore errors during shutdown.
            pass
