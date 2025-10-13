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
import json
from time import sleep

import pandas as pd
import parameterizable
from parameterizable import (
    sort_dict_by_keys,
    update_jsparams,
    access_jsparams)
from persidict import PersiDict, Joker, KEEP_CURRENT

from parameterizable import *

from .. import VALIDATION_SUCCESSFUL
from .._010_basic_portals import get_all_known_portals
from .._070_protected_code_portals.system_utils import get_unused_ram_mb, get_unused_cpu_cores, process_is_active, \
    get_process_start_time, get_current_process_id, get_current_process_start_time
from .._040_logging_code_portals.logging_portal_core_classes import build_execution_environment_summary
from .._010_basic_portals.basic_portal_core_classes import _describe_runtime_characteristic
from persidict import OverlappingMultiDict
from .._080_pure_code_portals.pure_core_classes import (
    PureCodePortal, PureFnExecutionResultAddr, PureFnCallSignature)
from .._800_signatures_and_converters.node_signature import get_node_signature

from multiprocessing import get_context

from .._090_swarming_portals.output_suppressor import (
    OutputSuppressor)

_BACKGROUND_WORKERS_TXT = "Background workers"


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
    - Parent/child: The portal instance created by user code is the parent.
      It may spawn a separate child process whose responsibility is to keep
      background workers alive. Child processes created by the portal do not
      spawn further workers (max_n_workers is forced to 0 in children).
    - Resources: The effective number of workers is automatically bounded by
      currently available CPU cores and RAM at runtime.
    - Environment logging: Runtime environment summary is stored under compute_nodes
      for debugging purposes to help describe where the parent process is running.

    See also: OutputSuppressor for silencing worker output, PureCodePortal for
    the base API and lifecycle management, and tests in tests/_090_swarming_portals.
    """
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
        """Initialize a swarming portal.

        Args:
            root_dict: Persistent dictionary or path used to back the portal's
                state. If None, a default dictionary will be used.
            p_consistency_checks: Probability or Joker controlling internal
                consistency checks. Passed to PureCodePortal.
            excessive_logging: Whether to enable verbose logging. Passed to
                PureCodePortal.
            max_n_workers: Desired maximum number of background workers for the
                parent process. Children must pass 0 here.
                The effective value may be reduced based on available CPUs and
                RAM at runtime.
            parent_process_id: ID of the parent process when this portal is
                constructed inside a child process. For parent portals, it
                must be None.
            parent_process_start_time: Start time of the parent process, used to
                detect PID reuse. For parents, it must be None.

        Notes:
            - When parent_process_id or parent_process_start_time is provided,
              both must be provided and max_n_workers must be 0.
            - Initializes compute_nodes storage and captures a unique
              node signature for this runtime.
        """
        PureCodePortal.__init__(self
            , root_dict=root_dict
            , p_consistency_checks=p_consistency_checks
            , excessive_logging=excessive_logging)

        if not isinstance(max_n_workers, (int, Joker)):
            raise TypeError(f"max_n_workers must be int or Joker, got {type(max_n_workers).__name__}")

        if (parent_process_id is None) != (parent_process_start_time is None):
            raise RuntimeError(
                f"parent_process_id and parent_process_start_time must both be None or both set; got id={parent_process_id}, start_time={parent_process_start_time}")
        if parent_process_id is None:
            self._auxiliary_config_params_at_init["max_n_workers"] = max_n_workers
        else:
            if max_n_workers != 0:
                raise ValueError(f"In child context, max_n_workers must be 0, got {max_n_workers}")

        compute_nodes_prototype = self._root_dict.get_subdict("compute_nodes")
        compute_nodes_shared_params = compute_nodes_prototype.get_params()
        dict_type = type(self._root_dict)
        compute_nodes = OverlappingMultiDict(
            dict_type=dict_type
            , shared_subdicts_params=compute_nodes_shared_params
            , json=dict(append_only=False)
            , pkl=dict(append_only=False)
            )
        self._compute_nodes = compute_nodes

        self._node_id = get_node_signature()
        self._parent_process_id = parent_process_id
        self._parent_process_start_time = parent_process_start_time
        self._child_process = None


    def get_params(self) -> dict:
        """Return portal parameters including parent process metadata.

        Returns:
            dict: Sorted dictionary of portal parameters inherited from
            PureCodePortal plus parent_process_id and
            parent_process_start_time.
        """
        params = super().get_params()
        params["parent_process_id"] = self._parent_process_id
        params["parent_process_start_time"] = self._parent_process_start_time
        sorted_params = sort_dict_by_keys(params)
        return sorted_params


    @property
    def is_parent(self) -> bool:
        """Whether this portal instance represents the parent process.

        Returns:
            bool: True if this process created the portal instance on the node
            (no parent metadata set); False if this is a child portal
            instantiated inside the background worker process.
        """
        if self._parent_process_id is None:
            return True
        return False


    def _post_init_hook(self) -> None:
        """Lifecycle hook invoked after initialization.

        Registers a global atexit handler once per process to terminate any
        child processes spawned by portals. For parent portals with a positive
        max_n_workers, spawns a child process that manages the pool of
        background worker processes.
        """
        super()._post_init_hook()

        if not SwarmingPortal._atexit_is_registered:
            atexit.register(_terminate_all_portals_child_processes)
            SwarmingPortal._atexit_is_registered = True

        if self.is_parent:
            if self.max_n_workers > 0:

                portal_init_jsparams = parameterizable.dumpjs(self)
                portal_init_jsparams = update_jsparams(portal_init_jsparams,
                    max_n_workers = self.max_n_workers)

                ctx = get_context("spawn")
                self._child_process = ctx.Process(
                    target=_launch_many_background_workers
                    , args=(portal_init_jsparams,))
                self._child_process.start()


    def _terminate_child_process(self):
        """Terminate the child process if it is running.

        This method is idempotent and safe to call from atexit handlers.
        It attempts a graceful termination, then escalates to kill if the
        child does not stop within a short grace period.
        """
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
        """Address path for storing execution environment summary.

        Returns:
            list[str]: A hierarchical key used in the compute_nodes storage of
            the form [node_id, parent_pid_and_start, "execution_environment"].
        """
        s = str(self._parent_process_id) + "_" + str(self._parent_process_start_time)
        return [self._node_id, s, "execution_environment"]


    @property
    def max_n_workers(self) -> int:
        """Effective cap on background worker processes.

        The configured max_n_workers value is adjusted down by runtime
        resource availability: currently unused CPU cores and available RAM.
        The result is cached in RAM for the life of the portal process
        until the cache is invalidated.

        Returns:
            int: Effective maximum number of worker processes to use.
        """
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
        """Describe the current portal configuration and runtime.

        Returns:
            pandas.DataFrame: A table combining PureCodePortal description with
            swarming-specific characteristics such as effective number of
            background workers.
        """
        all_params = [super().describe()]
        all_params.append(_describe_runtime_characteristic(
            _BACKGROUND_WORKERS_TXT, self.max_n_workers))

        result = pd.concat(all_params)
        result.reset_index(drop=True, inplace=True)
        return result


    def parent_runtime_is_live(self):
        """Check that the recorded parent process is still alive.

        Returns:
            bool: True if the parent PID exists and its start time matches the
            recorded start time (to avoid PID reuse issues); False otherwise.
        """
        if not process_is_active(self._parent_process_id):
            return False
        if get_process_start_time(self._parent_process_id) != self._parent_process_start_time:
            return False
        return True


    def _clear(self):
        """Release resources and clear internal state.

        Side Effects:
            Terminates the child process if present and clears references to
            compute node metadata before delegating to the base implementation.
        """
        self._compute_nodes = None
        self._terminate_child_process()
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
        if self.entropy_infuser.uniform(0, 1) < p:
            delay = self.entropy_infuser.uniform(min_delay, max_delay)
            sleep(delay)


    def _invalidate_cache(self):
        """Drop cached computed attributes and delegate to base class.

        This implementation removes any attributes used as local caches by this
        class (currently _max_n_workers_cache) and then calls the base
        implementation to allow it to clear its own caches.
        """
        if hasattr(self, "_max_n_workers_cache"):
            del self._max_n_workers_cache
        super()._invalidate_cache()


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


    n_workers_to_launch = access_jsparams(portal_init_jsparams
        , "max_n_workers")["max_n_workers"]
    n_workers_to_launch = int(n_workers_to_launch)

    portal_init_jsparams = update_jsparams(portal_init_jsparams,
        max_n_workers=0, parent_process_id = get_current_process_id(),
        parent_process_start_time = get_current_process_start_time())

    portal = parameterizable.loadjs(portal_init_jsparams)
    if not isinstance(portal, SwarmingPortal):
        raise TypeError(f"Expected SwarmingPortal, got {type(portal).__name__}")
    summary = build_execution_environment_summary()
    portal._compute_nodes.json[portal._execution_environment_address] = summary

    list_of_all_workers = []

    with portal:
        for i in range(n_workers_to_launch):
            portal._randomly_delay_execution(p=1)
            ctx = get_context("spawn")
            try:
                p = ctx.Process(target=_background_worker, args=(portal_init_jsparams,))
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
                        p = ctx.Process(target=_background_worker, args=(portal_init_jsparams,))
                        p.start()
                        new_list_of_all_workers.append(p)
                    except Exception as e:
                        break
            list_of_all_workers = new_list_of_all_workers


def _background_worker(portal_init_jsparams:JsonSerializedObject) -> None:
    """Worker loop that processes random execution requests serially.

    Runs indefinitely until the parent process is detected as dead.
    Within the loop, each individual request is handled in a subprocess to
    isolate failures and to reduce the risk of state leakage.

    Args:
        portal_init_jsparams: Serialized initialization parameters for
            reconstructing a SwarmingPortal in child context.
    """
    portal = parameterizable.loadjs(portal_init_jsparams)
    if not isinstance(portal, SwarmingPortal):
        raise TypeError(f"Expected SwarmingPortal, got {type(portal).__name__}")
    with portal:
        ctx = get_context("spawn")
        with OutputSuppressor():
            while True:
                if not portal.parent_runtime_is_live():
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
        portal_init_jsparams, max_n_workers=0)
    portal = parameterizable.loadjs(portal_init_jsparams)
    if not isinstance(portal, SwarmingPortal):
        raise TypeError(f"Expected SwarmingPortal, got {type(portal).__name__}")
    with portal:
        call_signature:PureFnCallSignature|None = None
        while True:
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


def _terminate_all_portals_child_processes():
    """Terminate child processes for all known portals.

    Registered with atexit the first time a SwarmingPortal is initialized.
    Ensures that any child processes are terminated to avoid orphaned workers.
    """
    for portal in get_all_known_portals():
        try:
            portal._terminate_child_process()
        except Exception:
            # Best-effort cleanup; ignore errors during shutdown.
            pass