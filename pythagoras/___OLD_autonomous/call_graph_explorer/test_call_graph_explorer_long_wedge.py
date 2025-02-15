import inspect
from pythagoras.___OLD_autonomous.call_graph_explorer import *

def a(return_name:bool = False
        , return_shallow:bool=False
        , return_deep:bool=False
        , **kwargs)-> Set[str]:
    assert return_name + return_shallow + return_deep == 1
    nested_calls = []
    nested_calls = set(nested_calls)
    my_name = inspect.stack()[0].function
    result = {my_name}
    args = set(kwargs.values())
    if return_name:
        return result
    elif return_shallow:
        result |= {f.__name__ for f in nested_calls}
        return result
    else: # return_deep == True
        if my_name in args:
            return args
        else:
            for f in nested_calls:
                kwargs[my_name] = my_name
                result |= f(**kwargs, return_deep=True)
            return result

def b(return_name:bool = False
        , return_shallow:bool=False
        , return_deep:bool=False
        , **kwargs)-> Set[str]:
    assert return_name + return_shallow + return_deep == 1
    nested_calls = [a]
    nested_calls = set(nested_calls)
    my_name = inspect.stack()[0].function
    result = {my_name}
    args = set(kwargs.values())
    if return_name:
        return result
    elif return_shallow:
        result |= {f.__name__ for f in nested_calls}
        return result
    else: # return_deep == True
        if my_name in args:
            return args
        else:
            for f in nested_calls:
                kwargs[my_name] = my_name
                result |= f(**kwargs, return_deep=True)
            return result


def c(return_name:bool = False
        , return_shallow:bool=False
        , return_deep:bool=False
        , **kwargs)-> Set[str]:
    assert return_name + return_shallow + return_deep == 1
    nested_calls = [b]
    nested_calls = set(nested_calls)
    my_name = inspect.stack()[0].function
    result = {my_name}
    args = set(kwargs.values())
    if return_name:
        return result
    elif return_shallow:
        result |= {f.__name__ for f in nested_calls}
        return result
    else: # return_deep == True
        if my_name in args:
            return args
        else:
            for f in nested_calls:
                kwargs[my_name] = my_name
                result |= f(**kwargs, return_deep=True)
            return result


def d(return_name:bool = False
        , return_shallow:bool=False
        , return_deep:bool=False
        , **kwargs)-> Set[str]:
    assert return_name + return_shallow + return_deep == 1
    nested_calls = [c]
    nested_calls = set(nested_calls)
    my_name = inspect.stack()[0].function
    result = {my_name}
    args = set(kwargs.values())
    if return_name:
        return result
    elif return_shallow:
        result |= {f.__name__ for f in nested_calls}
        return result
    else: # return_deep == True
        if my_name in args:
            return args
        else:
            for f in nested_calls:
                kwargs[my_name] = my_name
                result |= f(**kwargs, return_deep=True)
            return result


def e(return_name:bool = False
        , return_shallow:bool=False
        , return_deep:bool=False
        , **kwargs)-> Set[str]:
    assert return_name + return_shallow + return_deep == 1
    nested_calls = [d]
    nested_calls = set(nested_calls)
    my_name = inspect.stack()[0].function
    result = {my_name}
    args = set(kwargs.values())
    if return_name:
        return result
    elif return_shallow:
        result |= {f.__name__ for f in nested_calls}
        return result
    else: # return_deep == True
        if my_name in args:
            return args
        else:
            for f in nested_calls:
                kwargs[my_name] = my_name
                result |= f(**kwargs, return_deep=True)
            return result


def aa(return_name:bool = False
        , return_shallow:bool=False
        , return_deep:bool=False
        , **kwargs)-> Set[str]:
    assert return_name + return_shallow + return_deep == 1
    nested_calls = []
    nested_calls = set(nested_calls)
    my_name = inspect.stack()[0].function
    result = {my_name}
    args = set(kwargs.values())
    if return_name:
        return result
    elif return_shallow:
        result |= {f.__name__ for f in nested_calls}
        return result
    else: # return_deep == True
        if my_name in args:
            return args
        else:
            for f in nested_calls:
                kwargs[my_name] = my_name
                result |= f(**kwargs, return_deep=True)
            return result

def bb(return_name:bool = False
        , return_shallow:bool=False
        , return_deep:bool=False
        , **kwargs)-> Set[str]:
    assert return_name + return_shallow + return_deep == 1
    nested_calls = [aa]
    nested_calls = set(nested_calls)
    my_name = inspect.stack()[0].function
    result = {my_name}
    args = set(kwargs.values())
    if return_name:
        return result
    elif return_shallow:
        result |= {f.__name__ for f in nested_calls}
        return result
    else: # return_deep == True
        if my_name in args:
            return args
        else:
            for f in nested_calls:
                kwargs[my_name] = my_name
                result |= f(**kwargs, return_deep=True)
            return result


def cc(return_name:bool = False
        , return_shallow:bool=False
        , return_deep:bool=False
        , **kwargs)-> Set[str]:
    assert return_name + return_shallow + return_deep == 1
    nested_calls = [bb]
    nested_calls = set(nested_calls)
    my_name = inspect.stack()[0].function
    result = {my_name}
    args = set(kwargs.values())
    if return_name:
        return result
    elif return_shallow:
        result |= {f.__name__ for f in nested_calls}
        return result
    else: # return_deep == True
        if my_name in args:
            return args
        else:
            for f in nested_calls:
                kwargs[my_name] = my_name
                result |= f(**kwargs, return_deep=True)
            return result


def dd(return_name:bool = False
        , return_shallow:bool=False
        , return_deep:bool=False
        , **kwargs)-> Set[str]:
    assert return_name + return_shallow + return_deep == 1
    nested_calls = [cc]
    nested_calls = set(nested_calls)
    my_name = inspect.stack()[0].function
    result = {my_name}
    args = set(kwargs.values())
    if return_name:
        return result
    elif return_shallow:
        result |= {f.__name__ for f in nested_calls}
        return result
    else: # return_deep == True
        if my_name in args:
            return args
        else:
            for f in nested_calls:
                kwargs[my_name] = my_name
                result |= f(**kwargs, return_deep=True)
            return result


def ee(return_name:bool = False
        , return_shallow:bool=False
        , return_deep:bool=False
        , **kwargs)-> Set[str]:
    assert return_name + return_shallow + return_deep == 1
    nested_calls = [dd]
    nested_calls = set(nested_calls)
    my_name = inspect.stack()[0].function
    result = {my_name}
    args = set(kwargs.values())
    if return_name:
        return result
    elif return_shallow:
        result |= {f.__name__ for f in nested_calls}
        return result
    else: # return_deep == True
        if my_name in args:
            return args
        else:
            for f in nested_calls:
                kwargs[my_name] = my_name
                result |= f(**kwargs, return_deep=True)
            return result

def all_together(return_name:bool = False
        , return_shallow:bool=False
        , return_deep:bool=False
        , **kwargs)-> Set[str]:
    assert return_name + return_shallow + return_deep == 1
    nested_calls = [e,ee]
    nested_calls = set(nested_calls)
    my_name = inspect.stack()[0].function
    result = {my_name}
    args = set(kwargs.values())
    if return_name:
        return result
    elif return_shallow:
        result |= {f.__name__ for f in nested_calls}
        return result
    else:  # return_deep == True
        if my_name in args:
            return args
        else:
            for f in nested_calls:
                kwargs[my_name] = my_name
                result |= f(**kwargs, return_deep=True)
            return result


def test_long_chain():
    all_funcs = [a,b,c,d,e,aa,bb,cc,dd,ee,all_together]

    shallow_exploration_result = explore_call_graph_shallow(all_funcs)
    assert (shallow_exploration_result ==
            {f.__name__: f(return_shallow=True) for f in all_funcs})

    deep_exploration_result = explore_call_graph_deep(all_funcs)
    assert (deep_exploration_result ==
            {f.__name__: f(return_deep=True) for f in all_funcs})