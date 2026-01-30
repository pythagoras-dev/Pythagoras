"""Core classes for ordinary function portals and wrappers.

This module defines OrdinaryFn (a wrapper around ordinary functions) and
OrdinaryCodePortal (a portal for managing ordinary function execution context).
"""

from __future__ import annotations

import ast
from copy import deepcopy
from functools import cached_property
from typing import Callable, Any, TypeVar, Final

import pandas as pd
from persidict import PersiDict, SafeStrTuple

from .function_error_exception import FunctionError
from .reuse_flag import ReuseFlag, USE_FROM_OTHER
from .._230_tunable_portals import TunablePortal, TunableObject
from .code_normalizer import _get_normalized_fn_source_code_str_impl
from .function_processing import get_function_name_from_source
from .._110_supporting_utilities import get_hash_signature
from .._210_basic_portals.basic_portal_core_classes import (
    _describe_runtime_characteristic)


def get_normalized_fn_source_code_str(
        a_func: OrdinaryFn | Callable | str,
        skip_ordinarity_check: bool = False
        ) -> str:
    """Get normalized source code for a function.

    Normalizes function source by removing comments, docstrings, type
    annotations, and empty lines, then applying PEP 8 formatting. This creates
    a canonical representation for reliable comparison and hashing.

    Args:
        a_func: OrdinaryFn instance, callable, or source code string.
        skip_ordinarity_check: If True, skip ordinarity validation for callables.

    Returns:
        Normalized source code string.

    Raises:
        FunctionError: If the function violates ordinarity rules
            (unless skip_ordinarity_check is True).
        TypeError | ValueError: If input type is invalid or integrity checks fail.
        SyntaxError: If source cannot be parsed.
    """

    if isinstance(a_func, OrdinaryFn):
        return a_func.source_code
    else:
        return _get_normalized_fn_source_code_str_impl(
            a_func, drop_pth_decorators=True,
            skip_ordinarity_check=skip_ordinarity_check)


_REGISTERED_FUNCTIONS_TXT: Final[str] = "Registered functions"

OrdinaryFnType = TypeVar("OrdinaryFnType", bound="OrdinaryFn")


class OrdinaryCodePortal(TunablePortal):
    """Portal that manages OrdinaryFn instances and their runtime context.

    The portal is responsible for tracking linked OrdinaryFn objects and
    providing a context manager used during execution. It extends DataPortal
    with convenience methods specific to ordinary functions.
    """

    def __init__(self, root_dict: PersiDict | str | None = None):
        """Initialize the portal.

        Args:
            root_dict: Optional persistence root (PersiDict or path-like string)
                used by the underlying BasicPortal to store state.
        """
        super().__init__(root_dict=root_dict)

    def get_linked_functions(self
            , target_class: type[OrdinaryFnType] = None
            ) -> set[OrdinaryFnType]:
        """Return linked OrdinaryFn instances managed by this portal.

        Args:
            target_class: Optional OrdinaryFn subclass filter; defaults to
                OrdinaryFn.

        Returns:
            Set of linked OrdinaryFn instances.

        Raises:
            TypeError: If target_class is not an OrdinaryFn subclass.
        """
        if target_class is None:
            target_class = OrdinaryFn
        if isinstance(target_class, OrdinaryFn):
            # in case an instance is passed by mistake
            target_class = target_class.__class__
        if not issubclass(target_class, OrdinaryFn):
            raise TypeError(f"target_class must be a subclass of {OrdinaryFn.__name__}.")
        return self.get_linked_objects(target_class=target_class)

    def get_number_of_linked_functions(self, target_class: type | None = None) -> int:
        """Return the number of OrdinaryFn objects linked to this portal.

        Args:
            target_class: Optional OrdinaryFn subclass filter; defaults to
                OrdinaryFn.

        Returns:
            Number of linked functions matching the filter.
        """
        return len(self.get_linked_functions(target_class=target_class))


    def describe(self) -> pd.DataFrame:
        """Describe the portal's current state.

        Returns:
            DataFrame with portal runtime characteristics including the number
            of registered functions.
        """
        all_params = [super().describe()]

        all_params.append(_describe_runtime_characteristic(
            _REGISTERED_FUNCTIONS_TXT, self.get_number_of_linked_functions()))

        result = pd.concat(all_params)
        result.reset_index(drop=True, inplace=True)
        return result

class OrdinaryFn(TunableObject):
    """A wrapper around an ordinary function that enables controlled execution.

    OrdinaryFn provides a normalized, introspectable representation of regular
    Python functions. It stores function source in canonical form (no comments,
    docstrings, or type hints) enabling reliable comparison and hashing for
    caching and memoization.

    The execution model:
    1. Normalized source is compiled to a code object (cached)
    2. Function is renamed to avoid namespace collisions
    3. Execution happens in a controlled namespace with explicit dependencies
    4. All calls use keyword arguments only for maximum clarity

    Ordinary functions must:
    - Be regular functions (not methods, lambdas, closures, or async)
    - Accept keyword arguments only
    - Have no default parameter values
    - Have no *args parameters

    These constraints enable Pythagoras to reliably hash, compare, cache,
    and execute functions in isolated contexts where all dependencies are
    explicit and traceable.

    Attributes:
        _source_code: Normalized source representation of the function.
    """
    _source_code:str

    def __init__(self
                 , fn: Callable | str
                 , portal: OrdinaryCodePortal | ReuseFlag | None = None
                 ):
        """Create a new OrdinaryFn wrapper.

        Args:
            fn: Function, source code string, or OrdinaryFn to clone.
            portal: Portal to link to this instance. Can be:

                - An OrdinaryCodePortal instance to link directly
                - USE_FROM_OTHER to inherit the portal from ``fn`` when ``fn``
                  is an existing OrdinaryFn (enables sharing portals across
                  related function wrappers)
                - None to infer a suitable portal when the function is executed

        Raises:
            TypeError: If fn is not callable, string, or OrdinaryFn.
            FunctionError: If the function violates ordinarity rules.
            SyntaxError: If source cannot be parsed.
            ValueError: If portal is USE_FROM_OTHER but fn is not an OrdinaryFn.
        """
        if portal is USE_FROM_OTHER:
            if isinstance(fn, OrdinaryFn):
                portal = fn._linked_portal
            else:
                raise ValueError("portal can't be USE_FROM_OTHER "
                                 "when fn is not an OrdinaryFn.")

        TunableObject.__init__(self, portal=portal)
        if isinstance(fn, OrdinaryFn):
            self.__setstate__(deepcopy(fn.__getstate__()))
            self._init_finished = False
        else:
            if not (callable(fn) or isinstance(fn, str)):
                raise TypeError("fn must be a callable or a string "
                                "with the function's source code.")
            self._source_code = get_normalized_fn_source_code_str(fn)

        self._linked_portal = portal


    @property
    def portal(self) -> OrdinaryCodePortal:
        """Return the portal used by this function.

        Returns the function's linked portal or the active portal from context.

        Returns:
            The portal used by this function.
        """
        return super().portal


    @cached_property
    def source_code(self) -> str:
        """Get the normalized source code of the function.

        Returns:
            Normalized source (no comments, docstrings, or annotations).
        """
        return self._source_code


    @cached_property
    def name(self) -> str:
        """Get the name of the function.

        Returns:
            Function name parsed from source code.
        """
        return get_function_name_from_source(self.source_code)


    @cached_property
    def hash_signature(self) -> str:
        """Get the hash signature of the function.

        Returns:
            Stable, content-derived signature identifying the function's
            normalized source and metadata.
        """
        if not self._init_finished:
            raise RuntimeError("Function is not fully initialized yet, "
                               "hash_signature is not available.")
        return get_hash_signature(self)


    @cached_property
    def _virtual_file_name(self) -> str:
        """Return synthetic filename for compilation and tracebacks.

        The virtual filename appears in tracebacks and enables debuggers to
        identify dynamically compiled code. Each function version gets a unique
        filename via hash signature inclusion.

        Returns:
            Stable filename derived from function name and hash signature.
        """
        return self.name + "_" + self.hash_signature + ".py"


    @cached_property
    def _kwargs_var_name(self) -> str:
        """Return internal name for storing kwargs during execution.

        Unique variable names prevent collisions.

        Returns:
            Stable variable name unique to this function instance.
        """
        var_name = "kwargs_" + self.name
        var_name += "_" + self.hash_signature
        return var_name


    @cached_property
    def _result_var_name(self) -> str:
        """Return internal name for storing execution results.

        Hash-based naming prevents collisions.

        Returns:
            Stable variable name unique to this function instance.
        """
        var_name = "result_" + self.name
        var_name += "_" + self.hash_signature
        return var_name


    @cached_property
    def _tmp_fn_name(self) -> str:
        """Return internal temporary function name for execution.

        Functions are renamed before compilation to prevent namespace collisions.

        Returns:
            Stable function name unique to this instance.
        """
        fn_name = "func_" + self.name
        fn_name += "_" + self.hash_signature
        return fn_name


    @cached_property
    def _compiled_code(self) -> Any:
        """Compile the wrapped function's source into an executable code object.

        Parses the normalized source, renames the function to avoid namespace
        collisions, appends a call-and-store trailer, and compiles the result.
        The compiled code expects kwargs in _kwargs_var_name and stores the
        result in _result_var_name.

        Returns:
            Compiled code object ready for exec().
        """
        # Parse the stored source
        tree = ast.parse(self.source_code,
            filename=self._virtual_file_name,
            mode="exec")

        # Rename the target function
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == self.name:
                node.name = self._tmp_fn_name
                break
        else:  # defensive: should not happen
            raise RuntimeError(
                f"Function definition {self.name!r} not found "
                "while building _compiled_code.")

        # Append the call-and-store trailer
        trailer_src = (
            f"{self._result_var_name} = "
            f"{self._tmp_fn_name}(**{self._kwargs_var_name})")
        trailer_ast = ast.parse(trailer_src,
            filename=self._virtual_file_name,
            mode="exec",)
        tree.body.extend(trailer_ast.body)

        # Fix locations after AST edits, compile the code
        ast.fix_missing_locations(tree)
        source_to_execute = ast.unparse(tree)
        return self._compile(
            source_to_execute, self._virtual_file_name, "exec")


    @classmethod
    def _compile(cls, *args, **kwargs) -> Any:
        """Compile Python source code.

        Args:
            *args: Positional arguments passed to compile().
            **kwargs: Keyword arguments passed to compile().

        Returns:
            The code object returned by compile().
        """
        return compile(*args, **kwargs)


    def __call__(self, *args, **kwargs) -> Any:
        """Invoke the wrapped function using keyword arguments only.

        Args:
            *args: Not allowed; will raise FunctionError.
            **kwargs: Keyword arguments for the function.

        Returns:
            Function execution result.

        Raises:
            FunctionError: If positional arguments are supplied.
        """
        if len(args) != 0:
            raise FunctionError(f"Function {self.name} can't be called"
            f" with positional arguments, only keyword arguments are allowed."
            f" Got {len(args)} positional args.")
        return self.execute(**kwargs)


    def _available_names(self) -> dict[str, Any]:
        """Return names injected into the function's execution context.

        Provides a controlled namespace for function execution with only
        explicitly allowed symbols. This ensures:
        - Standard builtins are available (print, len, etc.)
        - Functions can reference themselves (for recursion or introspection)
        - Access to the Pythagoras package for framework operations
        - No implicit access to the caller's namespace (enforces isolation)

        Returns:
            A mapping of name to object made available during execution:
            - "__builtins__": The builtins module for standard Python functions.
            - self.name: The OrdinaryFn itself, allowing recursive calls.
            - "self": Alias for the OrdinaryFn (enables self-reference).
            - "pth": The pythagoras package for framework-level operations.
        """
        import builtins
        import pythagoras as pth

        return {"__builtins__": builtins,
            self.name: self,
            "self": self,
            "pth": pth,}


    def execute(self, **kwargs: Any) -> Any:
        """Execute the underlying function with keyword arguments.

        Executes inside the portal context with a controlled namespace populated
        by _available_names().

        Args:
            **kwargs: Keyword arguments for the function.

        Returns:
            Function return value.
        """
        with self.portal:
            names_dict = self._available_names()
            names_dict[self._kwargs_var_name] = kwargs
            exec(self._compiled_code, names_dict)
            result = names_dict[self._result_var_name]
            return result


    def __getstate__(self) -> dict[str, Any]:
        """Return picklable state for this instance.

        Returns:
            Dictionary with normalized source code.
        """
        state = dict(source_code=self._source_code)
        return state


    def __setstate__(self, state: dict[str, Any]) -> None:
        """Restore instance state from pickled data.

        Args:
            state: The state mapping previously produced by __getstate__,
                expected to contain the "source_code" key.
        """
        super().__setstate__(state)
        self._source_code = state["source_code"]


    def __hash_addr_descriptor__(self) -> str:
        """Return a short descriptor string used in hashing.

        Returns:
            Lowercased string combining the function name and class name.
        """
        descriptor = self.name
        descriptor += "_" + self.__class__.__name__
        descriptor = descriptor.lower()
        return descriptor


    def _first_visit_to_portal(self, portal: TunablePortal) -> None:
        """Register this function in a new portal and ensure addr is created."""
        super()._first_visit_to_portal(portal)
        with portal:
            _ = self.addr