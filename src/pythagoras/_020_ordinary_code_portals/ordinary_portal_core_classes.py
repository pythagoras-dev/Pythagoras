"""Core classes for ordinary function portals and wrappers.

This module defines `OrdinaryFn` (a wrapper around ordinary functions) and
`OrdinaryCodePortal` (a portal for managing ordinary functions).
"""

from __future__ import annotations

import ast
from copy import deepcopy
from functools import cached_property
from typing import Callable, Any

import pandas as pd
from persidict import PersiDict

from .function_error_exception import FunctionError
from .._010_basic_portals import BasicPortal, PortalAwareClass
from .code_normalizer import _get_normalized_function_source_impl
from .function_processing import get_function_name_from_source
from .._800_foundational_utilities import get_hash_signature
from .._010_basic_portals.basic_portal_core_classes import (
    _describe_runtime_characteristic)


def get_normalized_function_source(a_func: OrdinaryFn | Callable | str) -> str:
    """Get the normalized source code for a function or OrdinaryFn.

    This is a convenience wrapper around the internal normalizer that:
    - Accepts either an OrdinaryFn instance, a regular callable, or a string of
      source code containing a single function definition.
    - Returns a normalized string representing the function's source code, with
      comments, docstrings, type annotations, and empty lines removed and the
      result formatted per PEP 8.

    Args:
        a_func: An OrdinaryFn instance, a Python callable, or a string with the
            function's source code.

    Returns:
        The normalized source code string.

    Raises:
        FunctionError: If the function is not compliant with Pythagoras'
            ordinarity rules or multiple decorators are present.
        TypeError | ValueError: If input type is invalid or integrity checks fail.
        SyntaxError: If the provided source cannot be parsed.
    """

    if isinstance(a_func, OrdinaryFn):
        return a_func.source_code
    else:
        return _get_normalized_function_source_impl(
            a_func, drop_pth_decorators=True)


_REGISTERED_FUNCTIONS_TXT = "Registered functions"

class OrdinaryCodePortal(BasicPortal):
    """Portal that manages OrdinaryFn instances and their runtime context.

    The portal is responsible for tracking linked OrdinaryFn objects and
    providing a context manager used during execution. It extends BasicPortal
    with convenience methods specific to ordinary functions.
    """

    def __init__(self, root_dict: PersiDict | str | None = None):
        """Initialize the portal.

        Args:
            root_dict: Optional persistence root (PersiDict or path-like string)
                used by the underlying BasicPortal to store state.
        """
        super().__init__(root_dict=root_dict)

    def _get_linked_functions_ids(self, target_class: type | None = None) -> set[str]:
        """Return the set of IDs for functions linked to this portal.

        Args:
            target_class: Optional subclass of OrdinaryFn to filter the results.
                If None, OrdinaryFn is used.

        Returns:
            A set of string IDs corresponding to linked OrdinaryFn instances.

        Raises:
            TypeError: If required_portal_type is not a subclass of OrdinaryFn.
        """
        if target_class is None:
            target_class = OrdinaryFn
        if isinstance(target_class, OrdinaryFn):
            # in case an instance is passed by mistake
            target_class = target_class.__class__
        if not issubclass(target_class, OrdinaryFn):
            raise TypeError(f"required_portal_type must be a subclass of {OrdinaryFn.__name__}.")
        return self._get_linked_objects_ids(target_class=target_class)

    def get_linked_functions(self, target_class: type | None = None) -> list[OrdinaryFn]:
        """Return linked OrdinaryFn instances managed by this portal.

        Args:
            target_class: Optional subclass of OrdinaryFn to filter the results.
                If None, OrdinaryFn is used.

        Returns:
            A list of linked OrdinaryFn instances.

        Raises:
            TypeError: If required_portal_type is not a subclass of OrdinaryFn.
        """
        if target_class is None:
            target_class = OrdinaryFn
        if not issubclass(target_class, OrdinaryFn):
            raise TypeError(f"required_portal_type must be a subclass of {OrdinaryFn.__name__}.")
        return self.get_linked_objects(target_class=target_class)

    def get_number_of_linked_functions(self, target_class: type | None = None) -> int:
        """Return the number of OrdinaryFn objects linked to this portal.

        Args:
            target_class: Optional subclass of OrdinaryFn to filter the results.
                If None, OrdinaryFn is used.

        Returns:
            The number of linked functions matching the filter.
        """
        return len(self._get_linked_functions_ids(target_class=target_class))


    def describe(self) -> pd.DataFrame:
        """Describe the portal's current state.

        Returns:
            A pandas DataFrame with runtime characteristics of the portal,
            including the number of registered functions, combined with the
            base portal description.
        """
        all_params = [super().describe()]

        all_params.append(_describe_runtime_characteristic(
            _REGISTERED_FUNCTIONS_TXT, self.get_number_of_linked_functions()))

        result = pd.concat(all_params)
        result.reset_index(drop=True, inplace=True)
        return result


class OrdinaryFn(PortalAwareClass):
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

    Ordinary functions must be:
    - Regular Python functions (not methods, lambdas, closures, or async)
    - Callable with keyword arguments only
    - Free of default parameter values
    - Free of *args

    These constraints enable Pythagoras to reliably hash, compare, cache,
    and execute functions in isolated contexts where all dependencies are
    explicit and traceable.

    Attributes:
        _source_code: Normalized source representation of the function.
    """
    _source_code:str

    def __init__(self
                 , fn: Callable | str
                 , portal: OrdinaryCodePortal | None = None
                 ):
        """Create a new OrdinaryFn wrapper.

        Args:
            fn: Either a regular callable, a string with the function's source,
                or another OrdinaryFn instance to clone.
            portal: Optional OrdinaryCodePortal to link to this instance.

        Raises:
            TypeError: If fn is neither callable, a string, nor an OrdinaryFn.
            FunctionError: If the provided function source is not
                compliant with Pythagoras ordinarity rules.
            SyntaxError: If the provided source cannot be parsed.
        """
        PortalAwareClass.__init__(self, portal=portal)
        if isinstance(fn, OrdinaryFn):
            self.__setstate__(deepcopy(fn.__getstate__()))
            self._init_finished = False
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
        """Return the portal used by this function.

        It's either the function's linked portal or, if that is None, the
        currently active portal from the ambient context.

        Returns:
            OrdinaryCodePortal: The portal to be used by this object.
        """
        return super().portal


    @property
    def source_code(self) -> str:
        """Get the normalized source code of the function.

        Returns:
            str: The function source after normalization (no comments,
            docstrings, annotations; PEP 8 formatting).
        """
        return self._source_code


    @cached_property
    def name(self) -> str:
        """Get the name of the function.

        Returns:
            str: The function identifier parsed from the source code.
        """
        return get_function_name_from_source(self.source_code)


    @cached_property
    def hash_signature(self) -> str:
        """Get the hash signature of the function.

        Returns:
            str: A stable, content-derived signature used to uniquely identify
            the function's normalized source and selected metadata.
        """
        if not self._init_finished:
            raise RuntimeError("Function is not fully initialized yet, "
                               "hash_signature is not available.")
        return get_hash_signature(self)


    @cached_property
    def _virtual_file_name(self) -> str:
        """Return a synthetic filename used when compiling the function.

        The virtual filename appears in tracebacks and enables debuggers to
        identify the source of dynamically compiled code. Including the hash
        signature ensures each function version has a unique traceback identity.

        Returns:
            A stable file name derived from the function name and hash
            signature, ending with ".py".
        """
        return self.name + "_" + self.hash_signature + ".py"


    @cached_property
    def _kwargs_var_name(self) -> str:
        """Return the internal name used to store call kwargs during exec.

        Each function instance needs a unique variable name in the execution
        namespace to avoid collisions when multiple OrdinaryFn instances
        execute in the same or nested contexts.

        Returns:
            A stable variable name unique to this function instance.
        """
        var_name = "kwargs_" + self.name
        var_name += "_" + self.hash_signature
        return var_name


    @cached_property
    def _result_var_name(self) -> str:
        """Return the internal name used to store the call result.

        After execution, the result is retrieved from the namespace using
        this unique variable name. The hash-based naming prevents collisions
        between different function instances executing concurrently or nested.

        Returns:
            A stable variable name unique to this function instance.
        """
        var_name = "result_" + self.name
        var_name += "_" + self.hash_signature
        return var_name


    @cached_property
    def _tmp_fn_name(self) -> str:
        """Return the internal temporary function name used during exec.

        The original function is renamed to this unique identifier before
        compilation to prevent namespace collisions.

        Returns:
            A stable function name unique to this function instance.
        """
        fn_name = "func_" + self.name
        fn_name += "_" + self.hash_signature
        return fn_name


    @cached_property
    def _compiled_code(self) -> Any:
        """Return a code object that executes the wrapped function call."""
        # 1. Parse the stored source
        tree = ast.parse(self.source_code,
            filename=self._virtual_file_name,
            mode="exec")

        # 2. Rename the target function
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == self.name:
                node.name = self._tmp_fn_name
                break
        else:  # defensive: should not happen
            raise RuntimeError(
                f"Function definition {self.name!r} not found "
                "while building _compiled_code.")

        # 3. Append the call-and-store trailer
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
        """Invoke the wrapped function using only keyword arguments.

        Args:
            *args: Positional arguments are not allowed and will raise.
            **kwargs: Keyword arguments to pass to the function.

        Returns:
            The result of executing the function.

        Raises:
            TypeError: If positional arguments are supplied.
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
        """Execute the underlying function with the provided keyword args.

        The call is executed inside the portal context, with an execution
        namespace populated by _available_names().

        Args:
            **kwargs: Keyword-only arguments for the function call.

        Returns:
            The value returned by the function.
        """
        with self.portal:
            names_dict = self._available_names()
            names_dict[self._kwargs_var_name] = kwargs
            exec(self._compiled_code, names_dict)
            result = names_dict[self._result_var_name]
            return result


    def __getstate__(self) -> dict[str, Any]:
        """Return the picklable state for this instance.

        Returns:
            dict: A mapping that contains the normalized source code under the
            "source_code" key. Runtime caches and portal references are omitted.
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
            str: Lowercased string combining the function name and class name.
        """
        descriptor = self.name
        descriptor += "_" + self.__class__.__name__
        descriptor = descriptor.lower()
        return descriptor