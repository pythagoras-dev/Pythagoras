from __future__ import annotations

from copy import copy
from typing import Callable, Any, List

from persidict import PersiDict, Joker, KEEP_CURRENT

from .._040_logging_code_portals import KwArgs
from .._030_data_portals import ValueAddr
from .._840_work_with_collections.dict_sort import sort_dict_by_keys
from .._840_work_with_collections.list_flattener import flatten_list
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

    _guards: list[AutonomousFn] | None
    _validators: list[AutonomousFn] | None
    _guards_addrs: list[ValueAddr]
    _validators_addrs: list[ValueAddr]

    validators_arg_names = ["packed_kwargs", "fn_addr", "result"]
    guards_arg_names = ["packed_kwargs", "fn_addr"]

    def __init__(self, fn: Callable | str
                 , guards: list[AutonomousFn] | List[Callable] | None = None
                 , validators: list[AutonomousFn] | List[Callable] | None = None
                 , excessive_logging: bool|None = KEEP_CURRENT
                 , fixed_kwargs: dict | None = None
                 , portal: AutonomousCodePortal | None = None):
        AutonomousFn.__init__(self
            ,fn=fn
            , portal = portal
            , fixed_kwargs=fixed_kwargs
            , excessive_logging = excessive_logging)

        if isinstance(fn, ProtectedFn):
            assert guards is None
            assert validators is None
            return

        self._guards = self._normalize_protectors(
            guards, ProtectedFn.guards_arg_names)
        self._validators = self._normalize_protectors(
            validators, ProtectedFn.validators_arg_names)
        self._guards_addrs = [ValueAddr(g, portal = portal)
                              for g in self._guards]
        self._validators_addrs = [ValueAddr(v, portal = portal)
                                  for v in self._validators]


    def __getstate__(self):
        state = super().__getstate__()
        state["_guards_addrs"] = self._guards_addrs
        state["_validators_addrs"] = self._validators_addrs
        return state


    def __setstate__(self, state):
        self._invalidate_cache()
        super().__setstate__(state)
        self._guards_addrs = state["_guards_addrs"]
        self._validators_addrs = state["_validators_addrs"]


    @property
    def guards(self) -> list[AutonomousFn]:
        if not hasattr(self, "_guards") or self._guards is None:
            self._guards = [addr.get() for addr in self._guards_addrs]
        return self._guards


    @property
    def validators(self) -> list[AutonomousFn]:
        if not hasattr(self, "_validators") or self._validators is None:
            self._validators = [addr.get() for addr in self._validators_addrs]
        return self._validators


    def can_be_executed(self, kw_args: KwArgs) -> bool:
        with self.finally_bound_portal as portal:
            kw_args = kw_args.pack(portal)
            guards = copy(self.guards)
            portal.entropy_infuser.shuffle(guards)
            for guard in guards:
                if guard(packed_kwargs=kw_args, fn_addr = self.addr) is not OK:
                    return False
            return True


    def validate_result(self, kw_args: KwArgs,  result: Any) -> bool:
        with self.finally_bound_portal as portal:
            kw_args = kw_args.pack(portal)
            validators = copy(self.validators)
            portal.entropy_infuser.shuffle(validators)
            for validator in validators:
                if validator(packed_kwargs=kw_args, fn_addr = self.addr
                        , result=result) is not OK:
                    return False
            return True


    def execute(self, **kwargs) -> Any:
        with self.finally_bound_portal:
            kw_args = KwArgs(**kwargs)
            assert self.can_be_executed(kw_args)
            result = super().execute(**kwargs)
            assert self.validate_result(kw_args, result)
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
            protector = AutonomousFn(fn=protector, excessive_logging= None
                , portal=self.portal, fixed_kwargs=None)
            assert isinstance(protector, AutonomousFn)
            assert check_if_fn_accepts_args(
                required_arg_names, protector.source_code)
            new_protectors.append(protector)
        protectors = {f.hash_signature: f for f in new_protectors}
        protectors = sort_dict_by_keys(protectors)
        protectors = list(protectors.values())
        return protectors