from __future__ import annotations

import builtins

from .. import FunctionError
from .._020_ordinary_code_portals.code_normalizer import _pythagoras_decorator_names
from .._040_logging_code_portals import KwArgs

from .._060_autonomous_code_portals.names_usage_analyzer import (
    analyze_names_in_function)

from .._050_safe_code_portals.safe_portal_core_classes import *

class AutonomousCodePortal(SafeCodePortal):
    """Portal configured for enforcing autonomy constraints.

    This portal behaves like SafeCodePortal but is specialized for autonomous
    functions. It controls logging and consistency checks for operations related
    to AutonomousFn instances.
    """
    def __init__(self
            , root_dict: PersiDict | str | None = None
            , p_consistency_checks: float | Joker = KEEP_CURRENT
            , excessive_logging: bool|Joker = KEEP_CURRENT
            ):
        """Create an autonomous code portal.

        Args:
            root_dict: Persistence root backing the portal state. Can be a
                PersiDict instance, a path string, or None for defaults.
            p_consistency_checks: Probability [0..1] to run extra consistency
                checks on operations. KEEP_CURRENT uses the existing setting.
            excessive_logging: Whether to enable verbose logging. KEEP_CURRENT
                preserves the existing portal setting.
        """
        SafeCodePortal.__init__(self
            , root_dict=root_dict
            , p_consistency_checks=p_consistency_checks
            , excessive_logging=excessive_logging)


class AutonomousFnCallSignature(SafeFnCallSignature):
    """A signature of a call to an autonomous function.

    This extends SafeFnCallSignature to reference AutonomousFn instances.
    """
    _fn_cache: AutonomousFn | None

    def __init__(self, fn: AutonomousFn, arguments: dict):
        """Create a call signature for an autonomous function.

        Args:
            fn: The autonomous function being called.
            arguments: The call-time arguments mapping (already validated).
        """
        if not isinstance(fn, AutonomousFn):
            raise TypeError(f"fn must be AutonomousFn, got {type(fn).__name__}")
        if not isinstance(arguments, dict):
            raise TypeError(f"arguments must be dict, got {type(arguments).__name__}")
        super().__init__(fn, arguments)

    @property
    def fn(self) -> AutonomousFn:
        """Return the function object referenced by the signature."""
        return super().fn


class AutonomousFn(SafeFn):
    """A SafeFn wrapper that enforces function autonomy rules.

    AutonomousFn performs static validation at construction time to ensure that
    the wrapped function uses only built-ins or names imported inside its body,
    has no yield statements, and does not reference nonlocal variables.
    It also supports partial application via fixed keyword arguments.
    """
    _fixed_kwargs_cache: KwArgs | None
    _fixed_kwargs_packed: KwArgs | None

    def __init__(self, fn: Callable|str|SafeFn
                 , fixed_kwargs: dict[str,Any]|None = None
                 , excessive_logging: bool|Joker = KEEP_CURRENT
                 , portal: AutonomousCodePortal|None = None):
        """Construct an AutonomousFn and validate autonomy constraints.

        Args:
            fn: The function object, a string with the function's source code,
                or an existing SafeFn to wrap. If an AutonomousFn is provided,
                fixed_kwargs are merged.
            fixed_kwargs: Keyword arguments to pre-bind (partially apply).
            excessive_logging: Verbose logging flag or KEEP_CURRENT.
            portal: AutonomousCodePortal to use; may be None to defer.

        Raises:
            FunctionError: If static analysis detects violations of autonomy
                (nonlocal/global unbound names, missing imports, or yield usage).
        """
        super().__init__(fn=fn
            , portal = portal
            , excessive_logging = excessive_logging)

        fixed_kwargs = dict() if fixed_kwargs is None else fixed_kwargs
        fixed_kwargs = KwArgs(**fixed_kwargs)
        fixed_kwargs_packed = fixed_kwargs.pack(store=False)

        if isinstance(fn, AutonomousFn):
            self._fixed_kwargs_packed.update(fixed_kwargs_packed)
            self._fixed_kwargs_cache = KwArgs(**{**fn.fixed_kwargs, **fixed_kwargs})
        else:
            self._fixed_kwargs_cache = fixed_kwargs
            self._fixed_kwargs_packed = fixed_kwargs_packed

        fn_name = self.name

        analyzer = analyze_names_in_function(self.source_code)
        normalized_source = analyzer["normalized_source"]
        analyzer = analyzer["analyzer"]
        if self.source_code != normalized_source:
            raise RuntimeError("Normalized source does not match original source for autonomous function")

        nonlocal_names = analyzer.names.explicitly_nonlocal_unbound_deep
        all_decorators = _pythagoras_decorator_names
        # all_decorators = sys.modules["pythagoras"].all_decorators
        nonlocal_names -= set(all_decorators) #????????????

        if len(nonlocal_names) != 0:
            raise FunctionError(
                f"Function {self.name} is not autonomous, it uses external nonlocal objects: {analyzer.names.explicitly_nonlocal_unbound_deep}")

        if analyzer.n_yelds != 0:
            raise FunctionError(f"Function {self.name} is not autonomous, it uses yield statements")

        import_required = analyzer.names.explicitly_global_unbound_deep
        import_required |= analyzer.names.unclassified_deep
        # import_required -= set(pth.primary_decorators)
        import_required -= {"pure", "autonomous"}
        builtin_names = set(dir(builtins))
        import_required -= builtin_names
        pth_names = set(self._available_names())
        import_required -= pth_names
        import_required -= {fn_name}

        if len(import_required) != 0:
            raise FunctionError(
                f"Function {self.name} is not autonomous, it uses global objects {import_required} without importing them inside the function body")


    @property
    def fixed_kwargs(self) -> KwArgs:
        """KwArgs of pre-bound keyword arguments for this function.

        Returns:
            KwArgs: The fixed keyword arguments.
        """
        if not hasattr(self, "_fixed_kwargs_cache"):
            with self.portal:
                self._fixed_kwargs_cache = self._fixed_kwargs_packed.unpack()
        return self._fixed_kwargs_cache


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
            kwargs.update(self.fixed_kwargs)
            return super().execute(**kwargs)


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
        new_fixed_kwargs = {**self.fixed_kwargs,**kwargs}
        new_fn = type(self)(fn=self, fixed_kwargs=new_fixed_kwargs)
        return new_fn


    def _first_visit_to_portal(self, portal: DataPortal) -> None:
        """Hook called on the first visit to a data portal.

        Ensures that fixed kwargs are materialized (packed) within the portal.

        Args:
            portal: The data portal being visited for the first time.
        """
        super()._first_visit_to_portal(portal)
        with portal:
            _ = self.fixed_kwargs.pack()


    def __getstate__(self):
        """This method is called when the object is pickled."""
        state = super().__getstate__()
        state["fixed_kwargs_packed"] = self._fixed_kwargs_packed
        return state


    def __setstate__(self, state):
        """This method is called when the object is unpickled."""
        super().__setstate__(state)
        self._fixed_kwargs_packed = state["fixed_kwargs_packed"]


    @property
    def portal(self) -> AutonomousCodePortal:
        """Return the autonomous portal associated with this function."""
        return super().portal


    def _invalidate_cache(self):
        """Invalidate the function's attribute cache.

        If the function's attribute named ATTR is cached,
        its cached value will be stored in an attribute named _ATTR_cache
        This method should delete all such attributes.
        """
        super()._invalidate_cache()
        if hasattr(self, "_fixed_kwargs_cache"):
            if not hasattr(self, "_fixed_kwargs_packed"):
                raise AttributeError("Premature cache invalidation: "
                                     "fixed_kwargs_packed is missing.")
            del self._fixed_kwargs_cache
