from __future__ import annotations

import builtins
from typing import Callable, Any

from persidict import PersiDict, Joker, KEEP_CURRENT

from .._010_basic_portals import PortalAwareClass
from .._010_basic_portals.basic_portal_core_classes import _visit_portal
from .._020_ordinary_code_portals.code_normalizer import _pythagoras_decorator_names
from .._030_data_portals import DataPortal
from .._040_logging_code_portals import KwArgs

from .._060_autonomous_code_portals.names_usage_analyzer import (
    analyze_names_in_function)

from .._050_safe_code_portals.safe_portal_core_classes import (
    SafeFn, SafeCodePortal)

class AutonomousCodePortal(SafeCodePortal):
    
    def __init__(self
            , root_dict: PersiDict | str | None = None
            , p_consistency_checks: float | Joker = KEEP_CURRENT
            , excessive_logging: bool|Joker = KEEP_CURRENT
            ):
        SafeCodePortal.__init__(self
            , root_dict=root_dict
            , p_consistency_checks=p_consistency_checks
            , excessive_logging=excessive_logging)


class AutonomousFn(SafeFn):

    _fixed_kwargs_cache: KwArgs | None
    _fixed_kwargs_packed: KwArgs | None

    def __init__(self, fn: Callable|str|SafeFn
                 , fixed_kwargs: dict[str,Any]|None = None
                 , excessive_logging: bool|Joker = KEEP_CURRENT
                 , portal: AutonomousCodePortal|None = None):
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
        assert self.source_code == normalized_source

        nonlocal_names = analyzer.names.explicitly_nonlocal_unbound_deep
        all_decorators = _pythagoras_decorator_names
        # all_decorators = sys.modules["pythagoras"].all_decorators
        nonlocal_names -= set(all_decorators) #????????????

        assert len(nonlocal_names) == 0, (f"Function {self.name}"
            + f" is not autonomous, it uses external nonlocal"
            + f" objects: {analyzer.names.explicitly_nonlocal_unbound_deep}")

        assert analyzer.n_yelds == 0, (f"Function {self.name}"
            + f" is not autonomous, it uses yield statements")

        import_required = analyzer.names.explicitly_global_unbound_deep
        import_required |= analyzer.names.unclassified_deep
        # import_required -= set(pth.primary_decorators)
        import_required -= {"pure", "autonomous"}
        builtin_names = set(dir(builtins))
        import_required -= builtin_names
        pth_names = set(self._available_names())
        import_required -= pth_names
        import_required -= {fn_name}

        assert len(import_required) == 0, (f"Function {self.name}"
            + f" is not autonomous, it uses global"
            + f" objects {import_required}"
            + f" without importing them inside the function body")


    @property
    def fixed_kwargs(self) -> KwArgs:
        if not hasattr(self, "_fixed_kwargs_cache"):
            with self.portal:
                self._fixed_kwargs_cache = self._fixed_kwargs_packed.unpack()
        return self._fixed_kwargs_cache


    def execute(self, **kwargs) -> Any:
        with self.portal:
            overlapping_keys = set(kwargs.keys()) & set(self.fixed_kwargs.keys())
            assert len(overlapping_keys) == 0
            kwargs.update(self.fixed_kwargs)
            return super().execute(**kwargs)


    def fix_kwargs(self, **kwargs) -> AutonomousFn:
        """Create a new function by pre-filling some arguments.

        This is called a partial application in functional programming
        It allows creating specialized functions from general ones by
        transforming a function with multiple parameters
        into another function with fewer parameters by fixing some arguments.
        """

        overlapping_keys = set(kwargs.keys()) & set(self.fixed_kwargs.keys())
        assert len(overlapping_keys) == 0
        new_fixed_kwargs = {**self.fixed_kwargs,**kwargs}
        new_fn = type(self)(fn=self, fixed_kwargs=new_fixed_kwargs)
        return new_fn


    def _first_visit_to_portal(self, portal: DataPortal) -> None:
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
