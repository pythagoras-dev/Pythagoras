"""Execution environment snapshot utilities for diagnostic context.

This module provides functions to capture detailed system, process, and runtime
metadata at the moment of logging. This contextual information is invaluable
for diagnosing issues in distributed systems, long-running applications, or
when reproducing bugs across different environments.

The captured snapshot includes hostname, user, process ID, platform details,
Python version, CPU/memory statistics, working directory, timezone, and
whether execution is inside a Jupyter notebook.
"""

import random

import psutil
import os
import platform
import socket
from typing import Dict
from getpass import getuser
from datetime import datetime
from mixinforge import is_executed_in_notebook


def build_execution_environment_summary() -> Dict:
    """Build a snapshot of the current execution environment.

    Gathers system, process, and Python runtime metadata useful for diagnosing
    issues, particularly in distributed or long-running applications.

    Returns:
        Dict: A dictionary containing environment details such as hostname,
        user, process ID, OS/platform, Python version, CPU/memory stats,
        working directory, local timezone, and whether execution is inside a
        Jupyter notebook.
    """
    cwd = os.getcwd()

    execution_environment_summary = dict(
        hostname=socket.gethostname(),
        user=getuser(),
        pid=os.getpid(),
        platform=platform.platform(),
        python_implementation=platform.python_implementation(),
        python_version=platform.python_version(),
        processor=platform.processor(),
        cpu_count=psutil.cpu_count(),
        cpu_load_avg=psutil.getloadavg(),
        # cuda_gpu_count=torch.cuda.device_count(),
        disk_usage=psutil.disk_usage(cwd),
        virtual_memory=psutil.virtual_memory(),
        working_directory=cwd,
        local_timezone=datetime.now().astimezone().tzname(),
        is_in_notebook=is_executed_in_notebook(),
    )

    return execution_environment_summary

def make_unique_name(suggested_name: str, existing_names) -> str:
    """Generate a unique name by appending random suffixes on collision.

    Uses a simple collision-avoidance strategy: if the suggested name already
    exists in the collection, appends an underscore and a random number
    (1 to 10 billion) until finding an unused name. This approach ensures
    uniqueness while maintaining readability of the base name.

    Args:
        suggested_name: Preferred base name.
        existing_names: A collection supporting membership check (e.g., dict,
            set, list) used to determine collisions.

    Returns:
        A name guaranteed to not be present in existing_names at the
        time of checking.
    """
    candidate = suggested_name
    while candidate in existing_names:
        candidate = suggested_name + "_"
        random_number = random.randint(1, 10_000_000_000)
        candidate += str(random_number)
    return candidate

def add_execution_environment_summary(*args, **kwargs):
    """Augment keyword arguments with an execution environment summary.

    Optionally also adds positional messages under a unique `message_list` key
    when args are provided. This is primarily used to enrich logged events with
    contextual runtime information.

    Args:
        *args: Optional messages or payloads to attach under `message_list`.
        **kwargs: The keyword arguments dictionary to be augmented. Mutated in
            place by adding a unique key for the environment summary.

    Returns:
        dict: The same kwargs dict, with additional keys:
            - execution_environment_summary*: A unique key containing the env
              summary built by build_execution_environment_summary().
            - message_list*: A unique key containing the provided args (if any).
              Asterisks denote keys may be suffixed to ensure uniqueness.
    """
    context_param_name = "execution_environment_summary"
    context_param_name = make_unique_name(
        suggested_name=context_param_name, existing_names=kwargs)
    kwargs[context_param_name] = build_execution_environment_summary()
    if len(args):
        message_param_name = "message_list"
        message_param_name = make_unique_name(
            suggested_name=message_param_name, existing_names=kwargs)
        kwargs[message_param_name] = args
    return kwargs