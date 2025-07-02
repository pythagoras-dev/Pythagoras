from __future__ import annotations

from copy import copy
from typing import Callable, Any, List

from persidict import PersiDict, Joker, KEEP_CURRENT

from .._030_data_portals import DataPortal
from .._040_logging_code_portals import KwArgs
from .._030_data_portals import ValueAddr
from parameterizable import sort_dict_by_keys
from .list_flattener import flatten_list
from .OK_const import OK


from .._060_autonomous_code_portals import (
    AutonomousCodePortal, AutonomousFn)
from .fn_arg_names_checker import check_if_fn_accepts_args


class ProtectedCodePortal(AutonomousCodePortal):
    
    def __init__(self
            , root_dict: PersiDict|str|None = None
            , p_consistency_checks: float|Joker = KEEP_CURRENT
            , excessive_logging: bool|Joker = KEEP_CURRENT
            ):
        super().__init__(root_dict=root_dict
            , p_consistency_checks=p_consistency_checks
            , excessive_logging=excessive_logging)


class ProtectedFn(AutonomousFn):

    _pre_validators: list[AutonomousFn] | None
    _post_validators: list[AutonomousFn] | None
    _pre_validators_addrs: list[ValueAddr]
    _post_validators_addrs: list[ValueAddr]

    post_validators_arg_names = ["packed_kwargs", "fn_addr", "result"]
    pre_validators_arg_names = ["packed_kwargs", "fn_addr"]

    def __init__(self, fn: Callable | str
                 , pre_validators: list[AutonomousFn] | List[Callable] | None = None
                 , post_validators: list[AutonomousFn] | List[Callable] | None = None
                 , excessive_logging: bool|None = KEEP_CURRENT
                 , fixed_kwargs: dict | None = None
                 , portal: AutonomousCodePortal | None = None):
        AutonomousFn.__init__(self
            ,fn=fn
            , portal = portal
            , fixed_kwargs=fixed_kwargs
            , excessive_logging = excessive_logging)

        if isinstance(fn, ProtectedFn):
            assert pre_validators is None
            assert post_validators is None
            return

        self._pre_validators = self._normalize_protectors(
            pre_validators, ProtectedFn.pre_validators_arg_names)
        self._post_validators = self._normalize_protectors(
            post_validators, ProtectedFn.post_validators_arg_names)
        self._pre_validators_addrs = [ValueAddr(g, store=False) for g in self._pre_validators]
        self._post_validators_addrs = [ValueAddr(v, store=False) for v in self._post_validators]


    def __getstate__(self):
        """This method is called when the object is pickled."""
        state = super().__getstate__()
        state["pre_validators_addrs"] = self._pre_validators_addrs
        state["post_validators_addrs"] = self._post_validators_addrs
        return state


    def __setstate__(self, state):
        """This method is called when the object is unpickled."""
        self._invalidate_cache()
        super().__setstate__(state)
        self._pre_validators_addrs = state["pre_validators_addrs"]
        self._post_validators_addrs = state["post_validators_addrs"]


    def _first_visit_to_portal(self, portal: DataPortal) -> None:
        """Register an object in a portal that the object has not seen before."""
        super()._first_visit_to_portal(portal)
        with portal:
            if hasattr(self, "_pre_validators") and self._pre_validators is not None:
                new_pre_validators_addrs = [ValueAddr(g) for g in self._pre_validators]
                assert self._pre_validators_addrs == new_pre_validators_addrs
            if hasattr(self, "_post_validators") and self._post_validators is not None:
                new_post_validators_addrs = [ValueAddr(v) for v in self._post_validators]
                assert self._post_validators_addrs == new_post_validators_addrs


    @property
    def pre_validators(self) -> list[AutonomousFn]:
        if not hasattr(self, "_pre_validators") or self._pre_validators is None:
            self._pre_validators = [addr.get() for addr in self._pre_validators_addrs]
        return self._pre_validators


    @property
    def post_validators(self) -> list[AutonomousFn]:
        if not hasattr(self, "_post_validators") or self._post_validators is None:
            self._post_validators = [addr.get() for addr in self._post_validators_addrs]
        return self._post_validators


    def can_be_executed(self, kw_args: KwArgs) -> bool:
        with self.portal as portal:
            kw_args = kw_args.pack()
            pre_validators = copy(self.pre_validators)
            portal.entropy_infuser.shuffle(pre_validators)
            for pre_validator in pre_validators:
                if pre_validator(packed_kwargs=kw_args, fn_addr = self.addr) is not OK:
                    return False
            return True


    def validate_execution_result(self, kw_args: KwArgs, result: Any) -> bool:
        with self.portal as portal:
            kw_args = kw_args.pack()
            post_validators = copy(self.post_validators)
            portal.entropy_infuser.shuffle(post_validators)
            for post_validator in post_validators:
                if post_validator(packed_kwargs=kw_args, fn_addr = self.addr
                        , result=result) is not OK:
                    return False
            return True


    def execute(self, **kwargs) -> Any:
        with self.portal:
            kw_args = KwArgs(**kwargs)
            assert self.can_be_executed(kw_args)
            result = super().execute(**kwargs)
            assert self.validate_execution_result(kw_args, result)
            return result


    def _normalize_protectors(self
            , protectors: list[AutonomousFn] | None
            , required_arg_names: list[str]
            ) -> list[AutonomousFn]:
        """Return list of protectors in a normalized form.

        All the functions-protectors are converted to AutonomousFn objects,
        and returned as a list, sorted by functions' hash signatures.
        """
        if protectors is None:
            return []
        if not isinstance(protectors, list):
            if callable(protectors) or isinstance(protectors, str):
                protectors = [protectors]
        assert isinstance(protectors, list)
        protectors = flatten_list(protectors)
        new_protectors = []
        for protector in protectors:
            protector = AutonomousFn(fn=protector, excessive_logging= KEEP_CURRENT
                , portal=None, fixed_kwargs=None)
            assert isinstance(protector, AutonomousFn)
            assert check_if_fn_accepts_args(
                required_arg_names, protector.source_code)
            new_protectors.append(protector)
        protectors = {f.hash_signature: f for f in new_protectors}
        protectors = sort_dict_by_keys(protectors)
        protectors = list(protectors.values())
        return protectors


    @property
    def portal(self) -> ProtectedCodePortal:
        return AutonomousFn.portal.__get__(self)


    # @portal.setter
    # def portal(self, new_portal: ProtectedCodePortal) -> None:
    #     if not isinstance(new_portal, ProtectedCodePortal):
    #         raise TypeError("portal must be a ProtectedCodePortal instance")
    #     AutonomousFn.portal.__set__(self, new_portal)