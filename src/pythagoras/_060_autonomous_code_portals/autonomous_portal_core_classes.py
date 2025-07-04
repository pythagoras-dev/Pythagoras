from __future__ import annotations

import builtins
from typing import Callable, Any

from parameterizable import sort_dict_by_keys
from persidict import PersiDict, Joker, KEEP_CURRENT
from .._020_ordinary_code_portals.code_normalizer import _pythagoras_decorator_names
from .. import DataPortal
from .._040_logging_code_portals import KwArgs

from .._060_autonomous_code_portals.names_usage_analyzer import (
    analyze_names_in_function)

from .._050_safe_code_portals.safe_portal_core_classes import (
    SafeFn, SafeCodePortal)

import pythagoras as pth


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

    _fixed_kwargs_cached: KwArgs | None
    _fixed_kwargs_packed: KwArgs | None

    def __init__(self, fn: Callable|str|SafeFn
                 , fixed_kwargs: dict|None = None
                 , excessive_logging: bool|Joker = KEEP_CURRENT
                 , portal: AutonomousCodePortal|None = None):
        SafeFn.__init__(self
            ,fn=fn
            , portal = portal
            , excessive_logging = excessive_logging)

        fn_name = self.name

        fixed_kwargs = dict() if fixed_kwargs is None else fixed_kwargs
        self._fixed_kwargs_cached = KwArgs(**fixed_kwargs)
        self._fixed_kwargs_packed = self._fixed_kwargs_cached.pack(store=False)
        if hasattr(fn, "_fixed_kwargs_packed"):
            new_fixed_kwargs_packed =  KwArgs({**fn._fixed_kwargs_packed,**fn._fixed_kwargs_packed})

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
        if not hasattr(self, "_fixed_kwargs_cached"):
            self._fixed_kwargs_cached = self._fixed_kwargs_packed.unpack()
        return self._fixed_kwargs_cached


    def execute(self, **kwargs) -> Any:
        with self.portal:
            overlapping_keys = set(kwargs.keys()) & set(self.fixed_kwargs.keys())
            assert len(overlapping_keys) == 0
            kwargs.update(self.fixed_kwargs)
            return super().execute(**kwargs)


    def fix_kwargs(self, **kwargs) -> AutonomousFn:
        overlapping_keys = set(kwargs.keys()) & set(self.fixed_kwargs.keys())
        assert len(overlapping_keys) == 0
        new_fixed_kwargs = self.fixed_kwargs.copy()
        new_fixed_kwargs.update(kwargs)
        new_fn = AutonomousFn(self.source_code
              , fixed_kwargs=new_fixed_kwargs
              , portal=self._linked_portal)
        return new_fn


    def _first_visit_to_portal(self, portal: DataPortal) -> None:
        super()._first_visit_to_portal(portal)
        if hasattr(self,"_fixed_kwargs_cached"):
            with portal:
                _ = self._fixed_kwargs_cached.pack()


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
        return SafeFn.portal.__get__(self)


    def _invalidate_cache(self):
        super()._invalidate_cache()
        if hasattr(self, "_fixed_kwargs_cached"):
            del self._fixed_kwargs_cached


    # @portal.setter
    # def portal(self, new_portal: AutonomousCodePortal) -> None:
    #     if not isinstance(new_portal, AutonomousCodePortal):
    #         raise TypeError("portal must be a AutonomousCodePortal instance")
    #     SafeFn.portal.__set__(self, new_portal)
