# from pythagoras._07_mission_control.global_state_management import (
#   is_fully_unitialized, is_correctly_initialized)
import pythagoras as pth
import pandas as pd

from pythagoras._05_events_and_exceptions.current_date_gmt_str import \
    current_date_gmt_string


def persistent(param, val) -> pd.DataFrame:
  d = dict(
      type="persistent"
      ,parameter = [param]
      ,value = [val])
  return pd.DataFrame(d)


def runtime(param, val) -> pd.DataFrame:
  d = dict(
      type = "runtime"
      ,parameter = [param]
      ,value = [val])
  return pd.DataFrame(d)

def summary(include_current_session:bool = True, print_result:bool = False):
    """ Get summary of Pythagoras' current state ."""

    # if is_fully_unitialized():
    #     return "Pythagoras is not initialized."
    # if not is_correctly_initialized():
    #     return "Pythagoras is not correctly initialized."

    all_params = []

    all_params.append(persistent(
        "Base directory", pth.base_dir))
    all_params.append(persistent(
        "Total # of values stored", len(pth.value_store)))
    all_params.append(persistent(
        "Total # of function execution results cached"
        ,len(pth.execution_results)))
    all_params.append(persistent(
        "Total # of exceptions recorded", len(pth.crash_history)))
    all_params.append(persistent(
        "    # of exceptions recorded today"
        , len(pth.crash_history.get_subdict(current_date_gmt_string()))))
    all_params.append(persistent(
        "Total # of events recorded", len(pth.event_log)))
    all_params.append(persistent(
        "    # of events recorded today"
        , len(pth.event_log.get_subdict(current_date_gmt_string()))))
    all_params.append(persistent(
        "Execution queue size", len(pth.execution_requests)))
    all_params.append(persistent(
        "# of currently active nodes", len(pth.compute_nodes.pkl)))

    all_params.append(runtime(
        "# of background workers on the current node"
        , pth.n_background_workers))
    all_params.append(runtime(
        "Total # of available islands"
        , len(pth.all_autonomous_functions)))
    all_params.append(runtime(
        "Default island name", pth.default_island_name))
    all_params.append(runtime(
        "All available islands"
        , ", ".join(list(pth.all_autonomous_functions))))
    for island_name, island in pth.all_autonomous_functions.items():
        all_params.append(runtime(
            f"# of functions in island '{island_name}'"
            , len(island)))
        all_params.append(runtime(
            f"Names of functions in island '{island_name}'"
            , ", ".join(list(island))))


    result = pd.concat(all_params)
    result.reset_index(drop=True, inplace=True)
    # result.style.hide(axis="index")


    #
    # if include_current_session:
    #
    #     result += 21*"~" +  " CURRENT SESSION: " + 21*"~" + "\n"
    #     result += f"{len(pth.all_autonomous_functions)=} \n"
    #     result += f"{[island for island in pth.all_autonomous_functions]=} \n"
    #     result += f"{pth.default_island_name=} \n"
    #     default_island = pth.all_autonomous_functions[pth.default_island_name]
    #     result += f"{len(default_island)=} \n"
    #     result += f"{[func for func in default_island]=} \n"
    #
    # result += 60*"~" + "\n\n"

    if print_result:
        print(result)

    return result

