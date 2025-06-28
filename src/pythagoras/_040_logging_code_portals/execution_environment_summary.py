import psutil
import os
import platform
import socket
from typing import Dict
from getpass import getuser
from datetime import datetime
from .notebook_checker import is_executed_in_notebook
from .._010_basic_portals import BasicPortal


def build_execution_environment_summary()-> Dict:
    """Capture core information about execution environment.

    The function is intended to be used to log environment information
    to help debug (distributed) applications.
    """
    cwd = os.getcwd()

    execution_environment_summary = dict(
        hostname = socket.gethostname()
        ,user = getuser()
        ,pid = os.getpid()
        ,platform = platform.platform()
        ,python_implementation = platform.python_implementation()
        ,python_version = platform.python_version()
        ,processor = platform.processor()
        ,cpu_count = psutil.cpu_count()
        ,cpu_load_avg = psutil.getloadavg()
        # ,cuda_gpu_count=torch.cuda.device_count()
        ,disk_usage = psutil.disk_usage(cwd)
        ,virtual_memory = psutil.virtual_memory()
        ,working_directory = cwd
        ,local_timezone = datetime.now().astimezone().tzname()
        ,is_in_notebook = is_executed_in_notebook()
        )

    return execution_environment_summary

def make_unique_name(suggested_name:str, existing_names) -> str:
    """Make a name unique by adding a random suffix to it."""
    candidate = suggested_name
    entropy_infuser = BasicPortal._entropy_infuser
    while candidate in existing_names:
        candidate = suggested_name + "_"
        random_number = entropy_infuser.randint(1,10_000_000_000)
        candidate += str(random_number)
    return candidate

def add_execution_environment_summary(*args, **kwargs):
    """Add execution environment summary to kwargs. """
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