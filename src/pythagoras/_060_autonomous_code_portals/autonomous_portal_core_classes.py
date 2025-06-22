from __future__ import annotations

import builtins
from typing import Callable, Any

from persidict import PersiDict, Joker, KEEP_CURRENT

from .._040_logging_code_portals import KwArgs

from .._060_autonomous_code_portals.names_usage_analyzer import (
    analyze_names_in_function)

from .._050_safe_code_portals.safe_portal_core_classes import (
    SafeFn, SafeCodePortal)

from ... import pythagoras as pth


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

    _fixed_kwargs: KwArgs | None

    def __init__(self, fn: Callable|str|SafeFn
                 , fixed_kwargs: dict|None = None
                 , excessive_logging: bool|Joker = KEEP_CURRENT
                 , portal: AutonomousCodePortal|None = None):
        SafeFn.__init__(self
            ,fn=fn
            , portal = portal
            , excessive_logging = excessive_logging)

        if isinstance(fn, AutonomousFn):
            assert fixed_kwargs is None
            assert isinstance(self._fixed_kwargs, KwArgs)
            return

        fn_name = self.name

        fixed_kwargs = dict() if fixed_kwargs is None else fixed_kwargs
        self._fixed_kwargs = KwArgs(fixed_kwargs)

        analyzer = analyze_names_in_function(self.source_code)
        normalized_source = analyzer["normalized_source"]
        analyzer = analyzer["analyzer"]
        assert self.source_code == normalized_source

        nonlocal_names = analyzer.names.explicitly_nonlocal_unbound_deep
        all_decorators = pth.all_decorators
        # all_decorators = sys.modules["pythagoras"].all_decorators
        nonlocal_names -= set(all_decorators) #????????????

        assert len(nonlocal_names) == 0, (f"Function {self.name}"
            + f" is not autonomous, it uses external nonlocal"
            + f" objects: {analyzer.names.explicitly_nonlocal_unbound_deep}")

        assert analyzer.n_yelds == 0, (f"Function {self.name}"
            + f" is not autonomous, it uses yield statements")

        import_required = analyzer.names.explicitly_global_unbound_deep
        import_required |= analyzer.names.unclassified_deep
        import_required -= set(pth.primary_decorators)
        builtin_names = set(dir(builtins))
        import_required -= builtin_names
        pth_names = set(self._available_names())
        import_required -= pth_names
        import_required -= {fn_name}

        assert len(import_required) == 0, (f"Function {self.name}"
            + f" is not autonomous, it uses global"
            + f" objects {import_required}"
            + f" without importing them inside the function body")


    def execute(self, **kwargs) -> Any:
        with self.portal:
            overlapping_keys = set(kwargs.keys()) & set(self._fixed_kwargs.keys())
            assert len(overlapping_keys) == 0
            kwargs.update(self._fixed_kwargs)
            return SafeFn.execute(self, **kwargs)


    def fix_kwargs(self, **kwargs) -> AutonomousFn:
        overlapping_keys = set(kwargs.keys()) & set(self._fixed_kwargs.keys())
        assert len(overlapping_keys) == 0
        new_fixed_kwargs = self._fixed_kwargs.copy()
        new_fixed_kwargs.update(kwargs)
        new_fn = AutonomousFn(self.source_code
                              , fixed_kwargs=new_fixed_kwargs
                              , portal=self._linked_portal)
        return new_fn


    def __getstate__(self):
        state = super().__getstate__()
        state["_fixed_kwargs"] = self._fixed_kwargs
        return state

    def __setstate__(self, state):
        super().__setstate__(state)
        self._fixed_kwargs = state["_fixed_kwargs"]


    @property
    def portal(self) -> AutonomousCodePortal:
        return SafeFn.portal.__get__(self)


    # @portal.setter
    # def portal(self, new_portal: AutonomousCodePortal) -> None:
    #     if not isinstance(new_portal, AutonomousCodePortal):
    #         raise TypeError("portal must be a AutonomousCodePortal instance")
    #     SafeFn.portal.__set__(self, new_portal)
