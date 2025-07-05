from __future__ import annotations

from copy import deepcopy
from typing import Callable, Any

import pandas as pd
from persidict import PersiDict

from .._010_basic_portals import BasicPortal, PortalAwareClass
from .code_normalizer import _get_normalized_function_source_impl
from .function_processing import get_function_name_from_source
from .._800_signatures_and_converters import get_hash_signature
from .._010_basic_portals.basic_portal_core_classes import (
    _describe_runtime_characteristic)


def get_normalized_function_source(a_func: OrdinaryFn | Callable | str) -> str:
    """Return a function's source code in a 'canonical' form.

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


    def _get_linked_functions_ids(self, target_class: type | None=None) -> set[str]:
        """Get the set of known functions' IDs"""
        if target_class is None:
            target_class = OrdinaryFn
        if not issubclass(target_class, OrdinaryFn):
            raise TypeError(f"target_class must be a subclass of {OrdinaryFn.__name__}.")
        return self._get_linked_objects_ids(target_class=target_class)


    def get_linked_functions(self, target_class: type | None=None) -> list[OrdinaryFn]:
        """Get the list of known functions"""
        if target_class is None:
            target_class = OrdinaryFn
        if not issubclass(target_class, OrdinaryFn):
            raise TypeError(f"target_class must be a subclass of {OrdinaryFn.__name__}.")
        return self.get_linked_objects(target_class=target_class)


    def get_number_of_linked_functions(self, target_class: type | None=None) -> int:
        return len(self._get_linked_functions_ids(target_class=target_class))


    def describe(self) -> pd.DataFrame:
        """Get a DataFrame describing the portal's current state"""
        all_params = [super().describe()]

        all_params.append(_describe_runtime_characteristic(
            REGISTERED_FUNCTIONS_TXT, self.get_number_of_linked_functions()))

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
            self.__setstate__(deepcopy(fn.__getstate__()))
            if self._linked_portal_at_init is None:
                self._linked_portal_at_init = fn._linked_portal_at_init
            #TODO: check this logic
        else:
            if not (callable(fn) or isinstance(fn, str)):
                raise TypeError("fn must be a callable or a string "
                                "with the function's source code.")
            self._source_code = get_normalized_function_source(fn)


    @property
    def portal(self) -> OrdinaryCodePortal:
        """Get the portal which the function's methods will be using.

        It's either the function's linked portal or
        (if the linked portal is None) the currently active portal.
        """
        return super().portal


    @property
    def source_code(self) -> str:
        """Get the source code of the function."""
        return self._source_code


    @property
    def name(self) -> str:
        """Get the name of the function."""
        if not hasattr(self, "_name_cache") or self._name_cache is None:
            self._name_cache = get_function_name_from_source(self.source_code)
        return self._name_cache


    @property
    def hash_signature(self):
        """Get the hash signature of the function."""
        if not hasattr(self, "_hash_signature_cache"):
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
        """Invalidate the function's attribute cache.

        If the function's attribute named ATTR is cached,
        its cached value will be stored in an attribute named _ATTR_cache
        This method should delete all such attributes.
        """
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
        import pythagoras as pth
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
        """This method is called when the object is pickled."""
        state = dict(source_code=self._source_code)
        return state


    def __setstate__(self, state):
        """This method is called when the object is unpickled."""
        super().__setstate__(state)
        self._source_code = state["source_code"]


    def __hash_signature_descriptor__(self) -> str:
        descriptor = self.name
        descriptor += "_" + self.__class__.__name__
        descriptor = descriptor.lower()
        return descriptor