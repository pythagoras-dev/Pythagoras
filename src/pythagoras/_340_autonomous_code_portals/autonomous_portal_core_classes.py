from __future__ import annotations

import builtins

from .._220_data_portals.kw_args import _visit_portal
from .._310_ordinary_code_portals import FunctionError


from .._340_autonomous_code_portals.names_usage_analyzer import (
    _analyze_names_in_function)

from .._330_safe_code_portals.safe_portal_core_classes import *
from .._110_supporting_utilities import get_long_infoname

class AutonomousCodePortal(SafeCodePortal):
    """Portal for managing and executing autonomous functions with self-containment enforcement.

    An AutonomousCodePortal extends SafeCodePortal to provide specialized support for
    autonomous functions - self-contained functions that depend only on built-ins and
    names imported within their own body. This portal ensures that all functions
    registered through it satisfy autonomy constraints at both static analysis time
    (decoration) and runtime (execution).

    The portal manages the full lifecycle of AutonomousFn instances, including:
    - Static validation of function source code via AST analysis
    - Partial application support through fixed keyword arguments
    - Content-addressable storage of autonomous functions and their dependencies
    - Logging for all autonomous function operations

    Autonomy Rules Enforced:
        - No external name references (except built-ins)
        - All imports must be inside the function body
        - No yield or yield from statements
        - No nonlocal variable references
        - No relative imports (from . or from ..)

    This portal type is the foundation for distributed execution patterns where
    functions must be serializable and executable in isolation without relying
    on ambient state or module-level definitions.
    """
    def __init__(self
            , root_dict: PersiDict | str | None = None
            , excessive_logging: bool|Joker = KEEP_CURRENT
            ):
        """Create an autonomous code portal.

        Args:
            root_dict: Persistence root backing the portal state. Can be a
                PersiDict instance, a path string, or None for defaults.
            excessive_logging: Whether to enable verbose logging. KEEP_CURRENT
                preserves the existing portal setting.
        """
        SafeCodePortal.__init__(self
            , root_dict=root_dict
            , excessive_logging=excessive_logging)


class AutonomousFnCallSignature(SafeFnCallSignature):
    """Unique identifier for a specific autonomous function invocation.

    AutonomousFnCallSignature combines an AutonomousFn reference with a specific
    set of arguments to create a unique identifier for that particular function call.
    This signature is used for:
    - Logging and tracking execution history
    - Content-addressable result caching
    - Replay and reproducibility features

    The signature ensures type safety by restricting the function reference to
    AutonomousFn instances, preventing accidental mixing with non-autonomous functions.
    """

    def __init__(self, fn: AutonomousFn, arguments: dict):
        """Create a call signature for an autonomous function.

        Args:
            fn: The autonomous function being called.
            arguments: The call-time arguments mapping (already validated).
        """
        if not isinstance(fn, AutonomousFn):
            raise TypeError(f"fn must be AutonomousFn, got {get_long_infoname(fn)}")
        if not isinstance(arguments, dict):
            raise TypeError(f"arguments must be dict, got {get_long_infoname(arguments)}")
        super().__init__(fn, arguments)

    @cached_property
    def fn(self) -> AutonomousFn:
        """Return the function object referenced by the signature."""
        return super().fn


class AutonomousFn(SafeFn):
    """Self-contained function wrapper with strict autonomy enforcement and partial application support.

    AutonomousFn wraps regular Python functions to create fully autonomous, self-contained
    units of execution. These functions are guaranteed to depend only on:
    - Python built-in objects (functions, types, constants)
    - Names explicitly imported inside the function body
    - Arguments passed at call time (including fixed kwargs)

    Autonomy Validation:
        Static Analysis (at construction):
            - Parses function source code into an AST
            - Identifies all name references and their scopes
            - Verifies no external dependencies (global/nonlocal unbound names)
            - Checks for prohibited constructs (yield, relative imports)
            - Ensures all non-builtin names are imported within the function body

        Runtime Enforcement:
            - Executes function in controlled namespace via portal
            - Merges fixed kwargs with call-time arguments
            - Validates no overlap between fixed and call-time kwargs

    Partial Application:
        AutonomousFn supports partial application through fixed keyword arguments.
        This allows creating specialized versions of functions with some parameters
        pre-filled. Fixed kwargs are:
        - Stored alongside the function definition
        - Serialized in PackedKwArgs form for content-addressable storage
        - Automatically merged at execution time
        - Validated to prevent overlaps

    Design Rationale:
        Autonomy constraints enable functions to be safely:
        - Serialized and transmitted across processes/machines
        - Executed in isolated environments without setup
        - Cached and replayed deterministically
        - Composed and partially applied without side effects

    This is the foundation for Pythagoras' distributed computing and swarming capabilities.

    Attributes:
        _packed_fixed_kwargs: Serialized form of fixed arguments (for storage).
        _fixed_kwargs: Runtime dict of pre-bound keyword arguments (for execution).
    """

    _packed_fixed_kwargs: PackedKwArgs | None
    _fixed_kwargs: dict | None

    def __init__(self, fn: Callable|str|SafeFn
                 , fixed_kwargs: dict[str,Any]|None = None
                 , excessive_logging: bool|Joker|ReuseFlag = KEEP_CURRENT
                 , portal: AutonomousCodePortal|None|ReuseFlag = None):
        """Construct an AutonomousFn and validate autonomy constraints.

        Args:
            fn: The function object, a string with the function's source code,
                or an existing SafeFn to wrap. If an AutonomousFn is provided,
                fixed_kwargs are merged.
            fixed_kwargs: Keyword arguments to pre-bind (partially apply).
            excessive_logging: Controls verbose logging behavior. Can be:

                - True/False to explicitly enable/disable
                - KEEP_CURRENT to inherit from context
                - USE_FROM_OTHER to copy the setting from ``fn`` when ``fn``
                  is an existing AutonomousFn

            portal: Portal to use for autonomy checks. Can be:

                - An AutonomousCodePortal instance to link directly
                - USE_FROM_OTHER to inherit the portal from ``fn`` when ``fn``
                  is an existing AutonomousFn
                - None to infer a suitable portal when the function is called

        Raises:
            FunctionError: If static analysis detects violations of autonomy
                (nonlocal/global unbound names, missing imports, or yield usage).
        """
        super().__init__(fn=fn
            , portal = portal
            , excessive_logging = excessive_logging)

        self._packed_fixed_kwargs = None

        merged_kwargs = dict() if fixed_kwargs is None else fixed_kwargs
        if isinstance(fn, AutonomousFn):
            merged_kwargs = {**fn.fixed_kwargs, **merged_kwargs}
        self._fixed_kwargs = merged_kwargs

        fn_name = self.name

        analyzer = _analyze_names_in_function(self.source_code)
        normalized_source = analyzer["normalized_source"]
        analyzer = analyzer["analyzer"]
        if self.source_code != normalized_source:
            raise RuntimeError("Normalized source does not match original source for autonomous function")

        nonlocal_names = analyzer.names.explicitly_nonlocal_unbound_deep

        if len(nonlocal_names) != 0:
            raise FunctionError(
                f"Function {self.name} is not autonomous, it uses external nonlocal objects: {analyzer.names.explicitly_nonlocal_unbound_deep}")

        if analyzer.n_yelds != 0:
            raise FunctionError(f"Function {self.name} is not autonomous, it uses yield statements")

        if analyzer.names.has_relative_imports:
            raise FunctionError(
                f"Function {self.name} is not autonomous, it uses relative imports. "
                f"Relative imports (from . import x, from .. import y) depend on the function's "
                f"position in the package hierarchy and violate autonomy. "
                f"Please use absolute imports instead (e.g., 'from mypackage import x').")

        import_required = analyzer.names.explicitly_global_unbound_deep
        import_required |= analyzer.names.unclassified_deep
        builtin_names = set(dir(builtins))
        import_required -= builtin_names
        pth_names = set(self._available_names())
        import_required -= pth_names
        import_required -= {fn_name}

        if len(import_required) != 0:
            raise FunctionError(
                f"Function {self.name} is not autonomous, it uses global objects {import_required} without importing them inside the function body")


    @cached_property
    def fixed_kwargs(self) -> dict:
        """Dictionary of pre-bound keyword arguments for this function.

        Returns a copy of the fixed kwargs, unpacking them from storage if necessary.
        These are the parameters that were partially applied when the AutonomousFn
        was created or when fix_kwargs() was called.

        Returns:
            Dictionary mapping parameter names to their fixed values.

        Raises:
            RuntimeError: If neither packed nor unpacked fixed kwargs are available.
        """
        if self._fixed_kwargs is not None:
            return self._fixed_kwargs.copy()
        elif self._packed_fixed_kwargs is not None:
            return self._packed_fixed_kwargs.unpack()
        else:
            raise RuntimeError(f"No fixed kwargs stored for AutonomousFn {self.name}")


    @cached_property
    def packed_fixed_kwargs(self) -> PackedKwArgs:
        """Content-addressable serialized form of fixed keyword arguments.

        Returns the PackedKwArgs representation where all values are replaced by
        their ValueAddr references. This form is suitable for storage in the portal
        and enables deduplication across multiple function instances with identical
        fixed arguments.

        Returns:
            PackedKwArgs with all values converted to content-addressable references.

        Raises:
            RuntimeError: If neither packed nor unpacked fixed kwargs are available.
        """
        if self._packed_fixed_kwargs is not None:
            return self._packed_fixed_kwargs.copy()
        elif self._fixed_kwargs is not None:
            return KwArgs(**self._fixed_kwargs).pack()
        else:
            raise RuntimeError(f"No fixed kwargs stored for AutonomousFn {self.name}")


    def execute(self, **kwargs) -> Any:
        """Execute the function within the portal, applying fixed kwargs.

        Any kwargs provided here must not overlap with pre-bound fixed kwargs.

        Args:
            **kwargs: Call-time keyword arguments.

        Returns:
            Any: Result of the wrapped function call.

        Raises:
            ValueError: If provided kwargs overlap with fixed kwargs.
        """
        with self.portal:
            overlapping_keys = set(kwargs.keys()) & set(self.fixed_kwargs.keys())
            if len(overlapping_keys) != 0:
                raise ValueError(f"Overlapping kwargs with fixed kwargs: {sorted(overlapping_keys)}")
            call_kwargs = {**kwargs, **self.fixed_kwargs}
            return super().execute(**call_kwargs)


    def get_signature(self, arguments:dict) -> AutonomousFnCallSignature:
        """Build a call signature object for this function.

        Args:
            arguments: Mapping of argument names to values for this call.

        Returns:
            AutonomousFnCallSignature: The signature representing this call.
        """
        return AutonomousFnCallSignature(fn=self, arguments=arguments)


    def fix_kwargs(self, **kwargs) -> AutonomousFn:
        """Create a new autonomous function with some kwargs pre-filled.

        This is partial application: it creates a function with fewer parameters
        by fixing a subset of keyword arguments.

        Args:
            **kwargs: Keyword arguments to fix for the new function.

        Returns:
            AutonomousFn: A new wrapper that will always apply the provided
            keyword arguments in addition to already fixed ones.

        Raises:
            ValueError: If any of the provided kwargs overlap with already
                fixed kwargs.
        """

        overlapping_keys = set(kwargs.keys()) & set(self.fixed_kwargs.keys())
        if len(overlapping_keys) != 0:
            raise ValueError(f"Overlapping kwargs with fixed kwargs: {sorted(overlapping_keys)}")
        new_fixed_kwargs = {**self.fixed_kwargs, **kwargs}

        # Preserve portal and excessive_logging from parent

        new_fn = type(self)(fn=self,
            fixed_kwargs=new_fixed_kwargs,
            portal=self._linked_portal,
            excessive_logging=self.excessive_logging)

        return new_fn


    def _first_visit_to_portal(self, portal: AutonomousCodePortal) -> None:
        """Lifecycle hook invoked when the function first encounters a portal.

        Ensures that fixed kwargs are properly materialized in the portal's
        content-addressable storage.

        Args:
            portal: The data portal being visited for the first time.
        """
        super()._first_visit_to_portal(portal)
        with portal:
            if self._fixed_kwargs is not None:
                _ = KwArgs(**self._fixed_kwargs).pack()
            elif self._packed_fixed_kwargs is not None:
                _ = self._packed_fixed_kwargs.unpack()
        _visit_portal(self.packed_fixed_kwargs, portal=portal)


    def __getstate__(self):
        """This method is called when the object is pickled."""
        state = super().__getstate__()
        state["packed_fixed_kwargs"] = self.packed_fixed_kwargs
        return state


    def __setstate__(self, state):
        """This method is called when the object is unpickled."""
        super().__setstate__(state)
        self._packed_fixed_kwargs = state["packed_fixed_kwargs"]
        self._fixed_kwargs = None


    @property
    def portal(self) -> AutonomousCodePortal:
        """Return the autonomous portal associated with this function."""
        return super().portal

