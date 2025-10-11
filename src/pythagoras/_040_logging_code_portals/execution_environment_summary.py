import psutil
import os
import platform
import socket
from typing import Dict
from getpass import getuser
from datetime import datetime
from .notebook_checker import is_executed_in_notebook
from .._010_basic_portals import BasicPortal


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
    """Return a unique name based on the suggestion and a set of existing names.

    If the suggested name already exists, appends a random numeric
    suffix until a unique candidate is found.

    Args:
        suggested_name: Preferred base name.
        existing_names: A collection supporting membership check (e.g., dict,
            set, list) used to determine collisions.

    Returns:
        str: A name guaranteed to not be present in existing_names at the
        time of checking.
    """
    candidate = suggested_name
    entropy_infuser = BasicPortal._entropy_infuser
    while candidate in existing_names:
        candidate = suggested_name + "_"
        random_number = entropy_infuser.randint(1, 10_000_000_000)
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