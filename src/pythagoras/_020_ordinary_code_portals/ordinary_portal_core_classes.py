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
from .._800_signatures_and_converters import get_hash_signature
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

    def __init__(self
            , root_dict: PersiDict | str | None = None
            ):
        """Initialize the portal.

        Args:
            root_dict: Optional persistence root (PersiDict or path-like string)
                used by the underlying BasicPortal to store state.
        """
        super().__init__(root_dict = root_dict)


    def _get_linked_functions_ids(self, target_class: type | None=None) -> set[str]:
        """Return the set of IDs for functions linked to this portal.

        Args:
            target_class: Optional subclass of OrdinaryFn to filter the results.
                If None, OrdinaryFn is used.

        Returns:
            A set of string IDs corresponding to linked OrdinaryFn instances.

        Raises:
            TypeError: If target_class is not a subclass of OrdinaryFn.
        """
        if target_class is None:
            target_class = OrdinaryFn
        if isinstance(target_class, OrdinaryFn):
            target_class = target_class.__class__
        if not issubclass(target_class, OrdinaryFn):
            raise TypeError(f"target_class must be a subclass of {OrdinaryFn.__name__}.")
        return self._get_linked_objects_ids(target_class=target_class)


    def get_linked_functions(self, target_class: type | None=None) -> list[OrdinaryFn]:
        """Return linked OrdinaryFn instances managed by this portal.

        Args:
            target_class: Optional subclass of OrdinaryFn to filter the results.
                If None, OrdinaryFn is used.

        Returns:
            A list of linked OrdinaryFn instances.

        Raises:
            TypeError: If target_class is not a subclass of OrdinaryFn.
        """
        if target_class is None:
            target_class = OrdinaryFn
        if not issubclass(target_class, OrdinaryFn):
            raise TypeError(f"target_class must be a subclass of {OrdinaryFn.__name__}.")
        return self.get_linked_objects(target_class=target_class)


    def get_number_of_linked_functions(self, target_class: type | None=None) -> int:
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
    def _virtual_file_name(self):
        """Return a synthetic filename used when compiling the function.

        Returns:
            str: A stable file name derived from the function name and hash
            signature, ending with ".py".
        """
        return self.name + "_" + self.hash_signature + ".py"


    @cached_property
    def _kwargs_var_name(self):
        """Return the internal name used to store call kwargs during exec.

        Returns:
            str: A stable variable name unique to this function instance.
        """
        var_name = "kwargs_" + self.name
        var_name += "_" + self.hash_signature
        return var_name


    @cached_property
    def _result_var_name(self):
        """Return the internal name used to store the call result.

        Returns:
            str: A stable variable name unique to this function instance.
        """
        var_name = "result_" + self.name
        var_name += "_" + self.hash_signature
        return var_name


    @cached_property
    def _tmp_fn_name(self):
        """Return the internal temporary function name used during exec.

        Returns:
            str: A stable function name unique to this function instance.
        """
        fn_name = "func_" + self.name
        fn_name += "_" + self.hash_signature
        return fn_name


    @cached_property
    def _compiled_code(self):
        """Return a code object that executes the wrapped function call.
        """
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
    def _compile(cls,*args, **kwargs) -> Any:
        """Compile Python source code.

        Args:
            *args: Positional arguments passed to compile().
            **kwargs: Keyword arguments passed to compile().

        Returns:
            Any: The code object returned by compile().
        """
        return compile(*args, **kwargs)


    def __call__(self,* args, **kwargs) -> Any:
        """Invoke the wrapped function using only keyword arguments.

        Args:
            *args: Positional arguments are not allowed and will raise.
            **kwargs: Keyword arguments to pass to the function.

        Returns:
            Any: The result of executing the function.

        Raises:
            TypeError: If positional arguments are supplied.
        """
        if len(args) != 0:
            raise FunctionError(f"Function {self.name} can't be called"
            f" with positional arguments, only keyword arguments are allowed."
            f" Got {len(args)} positional args.")
        return self.execute(**kwargs)


    def _available_names(self):
        """Return names injected into the function's execution context.

        Returns:
            dict: A mapping of name to object made available during execution,
            including globals(), the OrdinaryFn itself under its function name
            and under "self", and the pythagoras package as "pth".
        """
        # import pythagoras as pth
        # names= dict(globals())
        # names[self.name] = self
        # names["self"] = self
        # names["pth"] = pth
        # return names
        import builtins
        import pythagoras as pth

        return {
            "__builtins__": builtins,
            self.name: self,  # original symbol
            "self": self,  # common alias
            "pth": pth,  # project root module
        }


    def execute(self,**kwargs):
        """Execute the underlying function with the provided keyword args.

        The call is executed inside the portal context, with an execution
        namespace populated by _available_names().

        Args:
            **kwargs: Keyword-only arguments for the function call.

        Returns:
            Any: The value returned by the function.
        """
        with self.portal:
            names_dict = self._available_names()
            names_dict[self._kwargs_var_name] = kwargs
            exec(self._compiled_code, names_dict)
            result = names_dict[self._result_var_name]
            return result


    def __getstate__(self):
        """Return the picklable state for this instance.

        Returns:
            dict: A mapping that contains the normalized source code under the
            "source_code" key. Runtime caches and portal references are omitted.
        """
        state = dict(source_code=self._source_code)
        return state


    def __setstate__(self, state):
        """Restore instance state from pickled data.

        Args:
            state (dict): The state mapping previously produced by __getstate__,
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