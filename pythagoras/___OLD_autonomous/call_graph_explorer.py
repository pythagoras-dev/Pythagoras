from typing import List, Dict, Set, Union, Callable

from pythagoras._060_autonomous_code_portals.names_usage_analyzer import (
    analyze_names_in_function)

def get_referenced_names(function:Union[Callable,str])->Dict[str,Set[str]]:
    """ Discover all external names referenced from within a function.

    Parameters
    ----------
    function: Callable or str
        a function for which we are discovering dependencies

    Returns
    ----------
    referenced_names: dict[str,set[str]]
        a dictionary with only one key, containing the function's name,
        and corresponding set, containing all external names
        referenced from within the function's source code plus
        the function's name itself.
    """
    analyzer = analyze_names_in_function(function)
    analyzer = analyzer["analyzer"]
    function_name = analyzer.names.function

    referenced_names = {function_name}
    referenced_names |= analyzer.names.explicitly_global_unbound_deep
    referenced_names |= analyzer.names.explicitly_nonlocal_unbound_deep
    referenced_names |= analyzer.names.unclassified_deep

    result = {function_name: referenced_names}

    return result

def explore_call_graph_shallow(functions:List[Union[Callable,str]]) -> Dict[str, Set[str]]:
    """ Discover all direct dependencies between functions.

    Parameters
    ----------
    functions: list[Callable]
        a list of all functions

    Returns
    ----------
    dependencies: dict[str, set[str]]
        a dictionary with keys containing function names,
        and values containing sets of function names.
        Each set dependencies[some_name] contains
        names of all functions from the original all_funcs,
        that are directly referenced / called from within
        some_name's source code. Each set always contains
        at least 1 element (the some_name function itself).
    """
    all_dependencies = dict()

    for function in functions:
        all_dependencies.update(get_referenced_names(function))
    all_function_names = set(all_dependencies)
    for function_name in all_function_names:
        all_dependencies[function_name] &= all_function_names

    return all_dependencies

def explore_call_graph_deep(all_funcs:List[Union[Callable,str]]) -> Dict[str, Set[str]]:
    """ Discover all direct and indirect dependencies between functions.

    Parameters
    ----------
    all_funcs: list[Callable]
        a list of all functions

    Returns
    ----------
    dependencies: dict[str, set[str]]
        a dictionary with keys containing function names,
        and values containing sets of function names.
        Each set dependencies[some_name] contains
        names of all functions from the original all_funcs,
        that are directly or indirectly referenced / called from within
        some_name's source code. Each set always contains
        at least 1 element (the some_name function itself).
    """
    all_dependencies = explore_call_graph_shallow(all_funcs)

    all_function_names = set(all_dependencies)

    for function_name in all_function_names:
        dependencies_old = all_dependencies[function_name]
        while True:
            dependencies_new = set(dependencies_old)
            for referenced_name in dependencies_old:
                dependencies_new |= all_dependencies[referenced_name]
            if len(dependencies_new) == len(dependencies_old):
                break
            dependencies_old = set(dependencies_new)
        all_dependencies[function_name] = dependencies_new

    return all_dependencies