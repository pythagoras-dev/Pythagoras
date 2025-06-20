from __future__ import annotations

from typing import Callable, Any

import pandas as pd
from persidict import PersiDict

from .._010_basic_portals import BasicPortal, PortalAwareClass
from .code_normalizer import _get_normalized_function_source_impl
from .function_processing import get_function_name_from_source
from .._820_strings_signatures_converters import get_hash_signature
from .._010_basic_portals.basic_portal_core_classes_NEW import (
    _describe_runtime_characteristic)


def get_normalized_function_source(a_func: OrdinaryFn | Callable | str) -> str:
    """Return function's source code in a 'canonical' form.

    Remove all comments, docstrings and empty lines;
    standardize code formatting based on PEP 8.

    Only ordinary functions are supported;
    methods and lambdas are not supported.
    """

    if isinstance(a_func, OrdinaryFn):
        return a_func.source_code
    else:
        return _get_normalized_function_source_impl(
            a_func, drop_pth_decorators=True)


REGISTERED_FUNCTIONS_TXT = "Registered functions"

class OrdinaryCodePortal(BasicPortal):

    def __init__(self
            , root_dict: PersiDict | str | None = None
            ):
        super().__init__(root_dict = root_dict)


    def _clear(self) -> None:
        """Clear the portal's state"""
        super()._clear()


    def linked_functions_ids(self, target_class:type|None=None) -> set[str]:
        """Get the set of known functions' IDs"""
        if target_class is None:
            target_class = OrdinaryFn
        if not issubclass(target_class, OrdinaryFn):
            raise TypeError(f"target_class must be a subclass of {OrdinaryFn.__name__}.")
        return self.linked_objects_ids(target_class=target_class)


    def linked_functions(self, target_class:type|None=None) -> list[OrdinaryFn]:
        """Get the list of known functions"""
        if target_class is None:
            target_class = OrdinaryFn
        if not issubclass(target_class, OrdinaryFn):
            raise TypeError(f"target_class must be a subclass of {OrdinaryFn.__name__}.")
        return self.linked_objects(target_class=target_class)


    def number_of_linked_functions(self, target_class:type|None=None) -> int:
        return len(self.linked_functions_ids(target_class=target_class))


    def describe(self) -> pd.DataFrame:
        """Get a DataFrame describing the portal's current state"""
        all_params = [super().describe()]

        all_params.append(_describe_runtime_characteristic(
            REGISTERED_FUNCTIONS_TXT, self.number_of_linked_functions()))

        result = pd.concat(all_params)
        result.reset_index(drop=True, inplace=True)
        return result


class OrdinaryFn(PortalAwareClass):
    """A wrapper around an ordinary function that allows calling it.

    An ordinary function is just a regular function. Async functions,
    class/object method, closures, and lambda functions
    are not considered ordinary.

    An ordinary function can only be called with keyword arguments.
    It can't be called with positional arguments.

    An OrdinaryFn object stores the source code of the function
    in a normalized form: without comments, docstrings, type annotations,
    and empty lines. The source code is formatted according to PEP 8.
    This way, Pythagoras can later compare the source
    code of two functions to check if they are equivalent.
    """
    _source_code:str

    _name_cache: str
    _compiled_code_cache:Any
    _hash_signature_cache:str
    _virtual_file_name_cache:str
    _kwargs_var_name_cache:str
    _result_var_name_cache:str
    _tmp_fn_name_cache:str

    def __init__(self
                 , fn: Callable | str
                 , portal: OrdinaryCodePortal | None = None
                 ):
        PortalAwareClass.__init__(self, portal=portal)
        if isinstance(fn, OrdinaryFn):
            self.__setstate__(fn.__getstate__())
            self._linked_portal = fn._linked_portal
            #TODO: check this logic
        else:
            if not (callable(fn) or isinstance(fn, str)):
                raise TypeError("fn must be a callable or a string "
                                "with the function's source code.")
            self._source_code = get_normalized_function_source(fn)


    @property
    def portal(self) -> OrdinaryCodePortal:
        return PortalAwareClass.portal.__get__(self)


    @portal.setter
    def portal(self, new_portal: OrdinaryCodePortal) -> None:
        if not isinstance(new_portal, OrdinaryCodePortal):
            raise TypeError("portal must be a OrdinaryCodePortal instance")
        PortalAwareClass.portal.__set__(self, new_portal)

    @property
    def source_code(self) -> str:
        return self._source_code


    @property
    def name(self) -> str:
        if not hasattr(self, "_name_cache") or self._name_cache is None:
            self._name_cache = get_function_name_from_source(self.source_code)
        return self._name_cache


    @property
    def hash_signature(self):
        if not hasattr(self, "_hash_signature_cache") or self._hash_signature_cache is None:
            self._hash_signature_cache = get_hash_signature(self)
        return self._hash_signature_cache


    @property
    def _virtual_file_name(self):
        if not hasattr(self, "_virtual_file_name_cache") or self._virtual_file_name_cache is None:
            self._virtual_file_name_cache = self.name + "_" + self.hash_signature + ".py"
        return self._virtual_file_name_cache


    @property
    def _kwargs_var_name(self):
        if not hasattr(self, "_kwargs_var_name_cache") or self._kwargs_var_name_cache is None:
            self._kwargs_var_name_cache = "kwargs_" + self.name
            self._kwargs_var_name_cache += "_" + self.hash_signature
        return self._kwargs_var_name_cache


    @property
    def _result_var_name(self):
        if not hasattr(self, "_result_var_name_cache") or self._result_var_name_cache is None:
            self._result_var_name_cache = "result_" + self.name
            self._result_var_name_cache += "_" + self.hash_signature
        return self._result_var_name_cache


    @property
    def _tmp_fn_name(self):
        if not hasattr(self, "_tmp_fn_name_cache") or self._tmp_fn_name_cache is None:
            self._tmp_fn_name_cache = "func_" + self.name
            self._tmp_fn_name_cache += "_" + self.hash_signature
        return self._tmp_fn_name_cache


    @property
    def _compiled_code(self):
        if not hasattr(self, "_compiled_code_cache") or (
                self._compiled_code_cache is None):
            source_to_execute = self.source_code
            source_to_execute = source_to_execute.replace(
                " " + self.name + "(", " " + self._tmp_fn_name + "(", 1)
            source_to_execute += f"\n\n{self._result_var_name} = "
            source_to_execute += f"{self._tmp_fn_name}(**{self._kwargs_var_name})"
            self._compiled_code_cache = self._compile(
                source_to_execute, self._virtual_file_name, "exec")
        return self._compiled_code_cache


    def _invalidate_cache(self):
        if hasattr(self, "_compiled_code_cache"):
            del self._compiled_code_cache
        if hasattr(self, "_tmp_fn_name_cache"):
            del self._tmp_fn_name_cache
        if hasattr(self, "_result_var_name_cache"):
            del self._result_var_name_cache
        if hasattr(self, "_kwargs_var_name_cache"):
            del self._kwargs_var_name_cache
        if hasattr(self, "_virtual_file_name_cache"):
            del self._virtual_file_name_cache
        if hasattr(self, "_hash_signature_cache"):
            del self._hash_signature_cache
        if hasattr(self, "_name_cache"):
            del self._name_cache
        super()._invalidate_cache()


    def _register_in_portal(self):
        PortalAwareClass._register_in_portal(self)
        if not isinstance(self._linked_portal, OrdinaryCodePortal):
            raise TypeError("To register an OrdinaryFn in a portal, "
                "the portal must be an OrdinaryCodePortal.")


    @classmethod
    def _compile(cls,*args, **kwargs) -> Any:
        return compile(*args, **kwargs)


    def __call__(self,* args, **kwargs) -> Any:
        assert len(args) == 0, (f"Function {self.name} can't"
            + " be called with positional arguments,"
            + " only keyword arguments are allowed.")
        return self.execute(**kwargs)


    def _available_names(self):
        """Returns a dictionary with the names, available inside the function."""
        from ... import pythagoras as pth
        names= dict(globals())
        names[self.name] = self
        names["self"] = self
        names["pth"] = pth
        return names


    def execute(self,**kwargs):
        with self.portal:
            names_dict = self._available_names()
            names_dict[self._kwargs_var_name] = kwargs
            exec(self._compiled_code, names_dict, names_dict)
            result = names_dict[self._result_var_name]
            return result


    def __getstate__(self):
        state = dict(_source_code=self._source_code)
        return state


    def __setstate__(self, state):
        PortalAwareClass.__setstate__(self, state)
        self._source_code = state["_source_code"]


    def __hash_signature_prefix__(self) -> str:
        prefix = self.name
        prefix += "_" + self.__class__.__name__
        prefix = prefix.lower()
        return prefix