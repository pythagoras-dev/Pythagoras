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

from persidict import PersiDict, Joker, KEEP_CURRENT

from parameterizable import *

from .._010_basic_portals import get_all_known_portals
from .._070_protected_code_portals import (VALIDATION_SUCCESSFUL,
    get_unused_ram_mb, get_unused_cpu_cores)
from .._010_basic_portals.basic_portal_core_classes import _describe_runtime_characteristic
from persidict import OverlappingMultiDict
from .._080_pure_code_portals.pure_core_classes import (
    PureCodePortal, PureFnExecutionResultAddr, PureFnCallSignature)

from multiprocessing import get_context
from .descendant_process_info import *
from .descendant_process_info import _min_date
from .system_processes_info_getters import *


from .._090_swarming_portals.output_suppressor import OutputSuppressor


_MAX_BACKGROUND_WORKERS_TXT = "Max Background workers"
_MIN_BACKGROUND_WORKERS_TXT = "Min Background workers"
_EXACT_BACKGROUND_WORKERS_TXT = "Exact Background workers"
_ANCESTOR_PROCESS_ID_TXT = "Ancestor Process ID"
_ANCESTOR_PROCESS_START_TIME_TXT = "Ancestor Process Start Time"


class SwarmingPortal(PureCodePortal):
    """Portal for asynchronous swarming execution of pure functions.

    The SwarmingPortal distributes execution of registered pure functions
    across background worker processes (potentially on different machines)
    in a best-effort, eventually-executed manner. It manages a child process
    that maintains a pool of background workers and randomly dispatches
    execution requests. No strong guarantees are provided regarding which
    worker runs a task, how many times it runs, or when it will run; only that
    eligible requests will eventually be executed at least once.

    Notes:
    - Ancestor/child: The portal instance created by user code is the ancestor.
      It may spawn a separate child process whose responsibility is
      to keep background workers alive.

    See also: OutputSuppressor for silencing worker output, PureCodePortal for
    the base API and lifecycle management, and tests in tests/_090_swarming_portals.
    """
    _compute_nodes: OverlappingMultiDict | None
    _node_id: str | None

    _ancestor_process_id: int | None
    _ancestor_process_start_time: int | None

    _atexit_is_registered: bool = False

    def __init__(self
                 , root_dict: PersiDict | str | None = None
                 , p_consistency_checks:float|Joker = KEEP_CURRENT
                 , excessive_logging: bool|Joker = KEEP_CURRENT
                 , max_n_workers: int|Joker|None = KEEP_CURRENT
                 , min_n_workers: int|Joker|None = KEEP_CURRENT
                 , exact_n_workers: int|None = None
                 , ancestor_process_id: int | None = None
                 , ancestor_process_start_time: int | None = None
                 ):
        """Initialize a swarming portal.

        Args:
            root_dict: Persistent dictionary or path used to back the portal's
                state. If None, a default dictionary will be used.
            p_consistency_checks: Probability or Joker controlling internal
                consistency checks. Passed to PureCodePortal.
            excessive_logging: Whether to enable verbose logging. Passed to
                PureCodePortal.
            max_n_workers: Maximum number of background workers for the
                ancestor process. Descendants must pass None here.
                The effective value may be reduced based on available CPUs and
                RAM at runtime.
            min_n_workers: Minimum number of background workers for the portal.
                The effective value may be increased based on available CPUs and
                RAM at runtime.
            exact_n_workers: Exact number of background workers for the portal.
                If this is not None, min_n_workers and max_n_workers are ignored.
                If this is None, the effective number of workers is determined
                by min_n_workers and max_n_workers.
            ancestor_process_id: ID of the ancestor process when this portal is
                constructed inside a descendant process. For (root)parent
                portals, it must be None.
            ancestor_process_start_time: Start time of the ancestor process,
                used to detect PID reuse. For parent portals, it must be None.

        Notes:
            - When ancestor_process_id or ancestor_process_start_time is provided,
              both must be provided.
        """
        PureCodePortal.__init__(self
            , root_dict=root_dict
            , p_consistency_checks=p_consistency_checks
            , excessive_logging=excessive_logging)

        if not isinstance(max_n_workers, (int, Joker, type(None))):
            raise TypeError(f"max_n_workers must be int or Joker or None, "
                            f"got {type(max_n_workers).__name__}")
        if not isinstance(min_n_workers, (int, Joker, type(None))):
            raise TypeError(f"min_n_workers must be int or Joker or None, "
                            f"got {type(min_n_workers).__name__}")
        if not isinstance(exact_n_workers, (int, type(None))):
            raise TypeError(f"exact_n_workers must be int or None, "
                            f"got {type(exact_n_workers).__name__}")


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

        self._all_workers = self._local_node_store.get_subdict("all_workers")


    @property
    def auxiliary_param_names(self) -> set[str]:
        names = super().auxiliary_param_names
        names.update({"ancestor_process_id","ancestor_process_start_time"})
        return names


    def register_descendant_process(self, process_type:str, process_id:int, process_start_time:int):
        # Validate inputs
        if not isinstance(process_type, str):
            raise TypeError(f"process_type must be a string, got {type(process_type).__name__}")
        if not process_type:
            raise ValueError("process_type cannot be empty")

        if not isinstance(process_id, int):
            raise TypeError(f"process_id must be an integer, got {type(process_id).__name__}")
        if process_id <= 0:
            raise ValueError(f"process_id must be positive, got {process_id}")

        if not isinstance(process_start_time, int):
            raise TypeError(f"process_start_time must be an integer, got {type(process_start_time).__name__}")
        if process_start_time < MIN_VALID_TIMESTAMP:
            raise ValueError(f"process_start_time must be a valid Unix timestamp (>= {MIN_VALID_TIMESTAMP} / {_min_date}), got {process_start_time}")

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
        return self._ancestor_process_id


    @property
    def ancestor_process_start_time(self) -> int | None:
        return self._ancestor_process_start_time

    @property
    def max_n_workers(self) -> int:
        return self._get_portal_config_setting("max_n_workers")

    @property
    def min_n_workers(self) -> int:
        return self._get_portal_config_setting("min_n_workers")

    @property
    def exact_n_workers(self) -> int:
        return self._get_portal_config_setting("exact_n_workers")


    def get_active_descendant_process_counter(self,
            process_type: str | None = None) -> int:
        """Count alive descendant processes, clean up dead ones.

        Args:
            process_type: If provided, only workers with this process type are
                counted. When None (default), all alive workers are counted.
                Dead workers are cleaned up.

        Returns:
            int: Number of alive descendant processes matching the filter.
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
                                   f"{type(worker).__name__}")

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
        """Return portal parameters including parent process metadata.

        Returns:
            dict: Sorted dictionary of portal parameters inherited from
            PureCodePortal plus ancestor_process_id and
            ancestor_process_start_time.
        """
        params = super().get_params()
        params["ancestor_process_id"] = self.ancestor_process_id
        params["ancestor_process_start_time"] = self.ancestor_process_start_time
        sorted_params = sort_dict_by_keys(params)
        return sorted_params


    @property
    def is_ancestor(self) -> bool:
        """Whether this portal instance represents the parent process.

        Returns:
            bool: True if this process created the portal instance on the node
            (no ancestor metadata set); False if this is a descendant portal
            instantiated inside the background worker process.
        """
        if self.ancestor_process_id is None:
            return True
        else:
            return False

    @property
    def n_workers_to_target(self) -> int:
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
        """Lifecycle hook invoked after initialization.

        Registers a global atexit handler once per process to terminate any
        child processes spawned by portals. For parent portals with a positive
        max_n_workers, spawns a child process that manages the pool of
        background worker processes.
        """
        super().__post_init__()

        if not SwarmingPortal._atexit_is_registered:
            atexit.register(_terminate_all_portals_descendant_processes)
            SwarmingPortal._atexit_is_registered = True

        if self.is_ancestor:
            if self.n_workers_to_target > 0:

                portal_init_jsparams = parameterizable.dumpjs(self)
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
        """Terminate tracked descendant worker processes if they are running.

        This method also cleans up dead processes.
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
            except:
                # Best-effort: ensure we don't keep stale tracking records
                # Bare except is intentional here
                pass



    # @property
    # def _execution_environment_address(self) -> list[str]: #TODO: move to Logs
    #     """Address path for storing execution environment summary.
    #
    #     Returns:
    #         list[str]: A hierarchical key used in the compute_nodes storage of
    #         the form [node_id, parent_pid_and_start, "execution_environment"].
    #     """
    #     s = str(self._ancestor_process_id) + "_" + str(self._ancestor_process_start_time)
    #     return [self._node_id, s, "execution_environment"]




    def describe(self) -> pd.DataFrame:
        """Describe the current portal configuration and runtime.

        Returns:
            pandas.DataFrame: A table combining PureCodePortal description with
            swarming-specific characteristics such as effective number of
            background workers.
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
        """Check that the recorded parent process is still alive.

        Returns:
            bool: True if the parent PID exists and its start time matches the
            recorded start time (to avoid PID reuse issues); False otherwise.
        """
        return process_is_alive(
            process_id=self.ancestor_process_id,
            process_start_time = self.ancestor_process_start_time)


    def _clear(self):
        """Release resources and clear internal state.

        The portal must not be used after this method is called.
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
        """Introduce randomized backoff to reduce contention.

        With probability p, sleeps for a random delay uniformly drawn from
        [min_delay, max_delay]. Uses the portal's entropy_infuser to remain
        deterministic when seeded in tests.

        Args:
            p: Probability of applying the delay.
            min_delay: Minimum sleep duration in seconds.
            max_delay: Maximum sleep duration in seconds.
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


    # def _invalidate_cache(self):
    #     """Drop cached computed attributes and delegate to base class.
    #
    #     This implementation removes any attributes used as local caches by this
    #     class (currently _max_n_workers_cache) and then calls the base
    #     implementation to allow it to clear its own caches.
    #     """
    #     if hasattr(self, "_max_n_workers_cache"):
    #         del self._max_n_workers_cache
    #     super()._invalidate_cache()


def _launch_many_background_workers(portal_init_jsparams:JsonSerializedObject) -> None:
    """Spawn and maintain a pool of background worker processes.

    This function is executed inside a dedicated child process created by the
    parent portal. It spawns up to max_n_workers worker processes, restarts
    any that exit unexpectedly, and records an execution environment summary
    under the portal's compute_nodes.

    Args:
        portal_init_jsparams: Serialized initialization parameters for
            reconstructing a SwarmingPortal. The parameters are adjusted to
            indicate this is a child context (max_n_workers=0) and to record
            the parent process metadata.
    """

    #
    # n_workers_to_launch = access_jsparams(portal_init_jsparams
    #     , "exact_n_workers")["exact_n_workers"]

    portal = parameterizable.loadjs(portal_init_jsparams)
    if not isinstance(portal, SwarmingPortal):
        raise TypeError(f"Expected SwarmingPortal, got {type(portal).__name__}")
    # summary = build_execution_environment_summary()
    # portal._compute_nodes.json[portal._execution_environment_address] = summary

    with portal:
        while True:
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
                except:
                    # Bare except is intentional here
                    pass
            portal._randomly_delay_execution(p=1)


def _background_worker(portal_init_jsparams:JsonSerializedObject) -> None:
    """Worker loop that processes random execution requests serially.

    Runs indefinitely until the parent process is detected as dead.
    Within the loop, each individual request is handled in a subprocess to
    isolate failures and to reduce the risk of state leakage.

    Args:
        portal_init_jsparams: Serialized initialization parameters for
            reconstructing a SwarmingPortal in child context.
    """
    portal_init_jsparams = update_jsparams(
        portal_init_jsparams
        , exact_n_workers=0
        , max_n_workers=KEEP_CURRENT
        , min_n_workers=KEEP_CURRENT
    )
    portal = parameterizable.loadjs(portal_init_jsparams)
    if not isinstance(portal, SwarmingPortal):
        raise TypeError(f"Expected SwarmingPortal, got {type(portal).__name__}")
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
    """Process a single pending execution request, if any.

    The function reconstructs a child-context portal, selects a random pending
    execution request (if available), and validates readiness. If validation
    yields a PureFnCallSignature, it continues with it; otherwise, it executes
    the request when validation returns VALIDATION_SUCCESSFUL. Output during
    execution is suppressed by the caller to keep workers quiet.

    Args:
        portal_init_jsparams: Serialized initialization parameters for
            reconstructing a SwarmingPortal in child context.
    """
    portal_init_jsparams = update_jsparams(
        portal_init_jsparams
        , exact_n_workers=0
        , max_n_workers=KEEP_CURRENT
        , min_n_workers=KEEP_CURRENT
    )
    portal = parameterizable.loadjs(portal_init_jsparams)
    if not isinstance(portal, SwarmingPortal):
        raise TypeError(f"Expected SwarmingPortal, got {type(portal).__name__}")
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
                elif not pre_validation_result is VALIDATION_SUCCESSFUL:
                    continue
                with OutputSuppressor():
                    new_address.execute()
                return


def _terminate_all_portals_descendant_processes():
    """Terminate descendant processes for all known portals.

    Registered with atexit the first time a SwarmingPortal is initialized.
    Ensures that any descendant processes are terminated to avoid orphaned workers.
    """
    for portal in get_all_known_portals():
        try:
            portal._terminate_descendant_processes()
        except Exception:
            # Best-effort cleanup; ignore errors during shutdown.
            pass