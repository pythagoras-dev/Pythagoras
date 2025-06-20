# from __future__ import annotations
#
# from typing import Callable, Any
#
# import pandas as pd
# from persidict import PersiDict
#
# from .._010_basic_portals import BasicPortal, PortalAwareClass
# from .code_normalizer import _get_normalized_function_source_impl
# from .function_processing import get_function_name_from_source
# from .._820_strings_signatures_converters import get_hash_signature
# from .._010_basic_portals.basic_portal_class_OLD import _describe_runtime_characteristic
#
#
# def get_normalized_function_source(a_func: OrdinaryFn | Callable | str) -> str:
#     """Return function's source code in a 'canonical' form.
#
#     Remove all comments, docstrings and empty lines;
#     standardize code formatting based on PEP 8.
#
#     Only ordinary functions are supported;
#     methods and lambdas are not supported.
#     """
#
#     if isinstance(a_func, OrdinaryFn):
#         return a_func.source_code
#     else:
#         return _get_normalized_function_source_impl(
#             a_func, drop_pth_decorators=True)
#
#
# REGISTERED_FUNCTIONS_TXT = "Registered functions"
#
# class OrdinaryCodePortal(BasicPortal):
#
#     known_functions_ids: set[Any]
#     known_functions: dict[str, OrdinaryFn]
#
#     def __init__(self
#             , root_dict: PersiDict | str | None = None
#             ):
#         super().__init__(root_dict = root_dict)
#         self.known_functions_ids = set()
#         self.known_functions = dict()
#
#     def _clear(self) -> None:
#         """Clear the portal's state"""
#         self.known_functions_ids = set()
#         self.known_functions = dict()
#         super()._clear()
#
#     def describe(self) -> pd.DataFrame:
#         """Get a DataFrame describing the portal's current state"""
#         all_params = [super().describe()]
#
#         all_params.append(_describe_runtime_characteristic(
#             REGISTERED_FUNCTIONS_TXT, len(self.known_functions)))
#
#         result = pd.concat(all_params)
#         result.reset_index(drop=True, inplace=True)
#         return result
#
#
# class OrdinaryFn(PortalAwareClass):
#     """A wrapper around an ordinary function that allows calling it.
#
#     An ordinary function is just a regular function. Async functions,
#     class/object method, closures, and lambda functions
#     are not considered ordinary.
#
#     An ordinary function can only be called with keyword arguments.
#     It can't be called with positional arguments.
#
#     An OrdinaryFn object stores the source code of the function
#     in a normalized form: without comments, docstrings, type annotations,
#     and empty lines. The source code is formatted according to PEP 8.
#     This way, Pythagoras can later compare the source
#     code of two functions to check if they are equivalent.
#     """
#     _source_code:str
#
#     _name_cache: str
#     _compiled_code_cache:Any
#     _hash_signature_cache:str
#     _virtual_file_name_cache:str
#     _kwargs_var_name_cache:str
#     _result_var_name_cache:str
#     _tmp_fn_name_cache:str
#
#     def __init__(self
#                  , fn: Callable | str
#                  , portal: OrdinaryCodePortal | None = None
#                  ):
#         PortalAwareClass.__init__(self, portal=portal)
#         if isinstance(fn, OrdinaryFn):
#             #TODO: check this logic
#             self.__setstate__(fn.__getstate__())
#         else:
#             assert callable(fn) or isinstance(fn, str)
#             self._source_code = get_normalized_function_source(fn)
#
#
#     @property
#     def source_code(self) -> str:
#         return self._source_code
#
#
#     @property
#     def name(self) -> str:
#         if not hasattr(self, "_name_cache") or self._name_cache is None:
#             self._name_cache = get_function_name_from_source(self.source_code)
#         return self._name_cache
#
#
#     @property
#     def hash_signature(self):
#         if not hasattr(self, "_hash_signature_cache") or self._hash_signature_cache is None:
#             self._hash_signature_cache = get_hash_signature(self)
#         return self._hash_signature_cache
#
#
#     @property
#     def _virtual_file_name(self):
#         if not hasattr(self, "_virtual_file_name_cache") or self._virtual_file_name_cache is None:
#             self._virtual_file_name_cache = self.name + "_" + self.hash_signature + ".py"
#         return self._virtual_file_name_cache
#
#
#     @property
#     def _kwargs_var_name(self):
#         if not hasattr(self, "_kwargs_var_name_cache") or self._kwargs_var_name_cache is None:
#             self._kwargs_var_name_cache = "kwargs_" + self.name
#             self._kwargs_var_name_cache += "_" + self.hash_signature
#         return self._kwargs_var_name_cache
#
#
#     @property
#     def _result_var_name(self):
#         if not hasattr(self, "_result_var_name_cache") or self._result_var_name_cache is None:
#             self._result_var_name_cache = "result_" + self.name
#             self._result_var_name_cache += "_" + self.hash_signature
#         return self._result_var_name_cache
#
#
#     @property
#     def _tmp_fn_name(self):
#         if not hasattr(self, "_tmp_fn_name_cache") or self._tmp_fn_name_cache is None:
#             self._tmp_fn_name_cache = "func_" + self.name
#             self._tmp_fn_name_cache += "_" + self.hash_signature
#         return self._tmp_fn_name_cache
#
#
#     @property
#     def _compiled_code(self):
#         if not hasattr(self, "_compiled_code_cache") or (
#                 self._compiled_code_cache is None):
#             source_to_execute = self.source_code
#             source_to_execute = source_to_execute.replace(
#                 " " + self.name + "(", " " + self._tmp_fn_name + "(", 1)
#             source_to_execute += f"\n\n{self._result_var_name} = "
#             source_to_execute += f"{self._tmp_fn_name}(**{self._kwargs_var_name})"
#             self._compiled_code_cache = self._compile(
#                 source_to_execute, self._virtual_file_name, "exec")
#         return self._compiled_code_cache
#
#
#     def _invalidate_cache(self):
#         if hasattr(self, "_compiled_code_cache"):
#             del self._compiled_code_cache
#         if hasattr(self, "_tmp_fn_name_cache"):
#             del self._tmp_fn_name_cache
#         if hasattr(self, "_result_var_name_cache"):
#             del self._result_var_name_cache
#         if hasattr(self, "_kwargs_var_name_cache"):
#             del self._kwargs_var_name_cache
#         if hasattr(self, "_virtual_file_name_cache"):
#             del self._virtual_file_name_cache
#         if hasattr(self, "_hash_signature_cache"):
#             del self._hash_signature_cache
#         if hasattr(self, "_name_cache"):
#             del self._name_cache
#         super()._invalidate_cache()
#
#
#     def register_in_portal(self):
#         if self._portal is None:
#             return
#         portal = self._portal
#         assert isinstance(portal, OrdinaryCodePortal)
#         if id(self) in portal.known_functions_ids:
#             return
#         portal.known_functions_ids.add(id(self))
#         portal.known_functions[self.hash_signature] = self
#
#
#     @classmethod
#     def _compile(cls,*args, **kwargs) -> Any:
#         return compile(*args, **kwargs)
#
#
#     def __call__(self,* args, **kwargs) -> Any:
#         assert len(args) == 0, (f"Function {self.name} can't"
#             + " be called with positional arguments,"
#             + " only keyword arguments are allowed.")
#         return self.execute(**kwargs)
#
#
#     def _available_names(self):
#         """Returns a dictionary with the names, available inside the function."""
#         from ... import pythagoras as pth
#         names= dict(globals())
#         names[self.name] = self
#         names["self"] = self
#         names["pth"] = pth
#         return names
#
#
#     def execute(self,**kwargs):
#         with self.finally_bound_portal:
#             names_dict = self._available_names()
#             names_dict[self._kwargs_var_name] = kwargs
#             exec(self._compiled_code, names_dict, names_dict)
#             result = names_dict[self._result_var_name]
#             return result
#
#
#     def __getstate__(self):
#         state = dict(_source_code=self._source_code)
#         return state
#
#
#     def __setstate__(self, state):
#         self._invalidate_cache()
#         self._source_code = state["_source_code"]
#
#
#     def __hash_signature_prefix__(self) -> str:
#         prefix = self.name
#         prefix += "_" + self.__class__.__name__
#         prefix = prefix.lower()
#         return prefix