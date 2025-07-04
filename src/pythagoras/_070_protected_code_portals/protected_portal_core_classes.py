from __future__ import annotations

from copy import copy
from typing import Callable, Any, List

from persidict import PersiDict, Joker, KEEP_CURRENT

from .validator_fn_classes import ValidatorFn, PreValidatorFn, PostValidatorFn, SimplePreValidatorFn, \
    ComplexPreValidatorFn
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

    _pre_validators_cached: list[AutonomousFn] | None
    _post_validators_cached: list[AutonomousFn] | None
    _pre_validators_addrs: list[ValueAddr]
    _post_validators_addrs: list[ValueAddr]

    post_validators_arg_names = ["packed_kwargs", "fn_addr", "result"]
    pre_validators_arg_names = ["packed_kwargs", "fn_addr"]

    def __init__(self, fn: Callable | str
                 , pre_validators: list[AutonomousFn] | List[Callable] | None = None
                 , post_validators: list[AutonomousFn] | List[Callable] | None = None
                 , excessive_logging: bool|None = KEEP_CURRENT
                 , fixed_kwargs: dict | None = None
                 , portal: ProtectedCodePortal | None = None):
        super().__init__(fn=fn
            , portal = portal
            , fixed_kwargs=fixed_kwargs
            , excessive_logging = excessive_logging)

        pre_validators = self._normalize_validators(pre_validators, PreValidatorFn)
        post_validators = self._normalize_validators(post_validators, PostValidatorFn)

        if isinstance(fn, ProtectedFn):
            pre_validators += fn.pre_validators
            post_validators += fn.post_validators

        self._pre_validators_cached = self._normalize_validators(pre_validators, PreValidatorFn)
        self._post_validators_cached = self._normalize_validators(post_validators, PostValidatorFn)
        self._pre_validators_addrs = [ValueAddr(g, store=False) for g in self._pre_validators_cached]
        self._post_validators_addrs = [ValueAddr(v, store=False) for v in self._post_validators_cached]


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

        if hasattr(self,"_pre_validators_cached"):
            with portal:
                _ = [ValueAddr(g) for g in self._pre_validators_cached]

        if hasattr(self,"_post_validators_cached"):
            with portal:
                _ = [ValueAddr(g) for g in self._post_validators_cached]


    @property
    def pre_validators(self) -> list[AutonomousFn]:
        if not hasattr(self, "_pre_validators_cached"):
            self._pre_validators_cached = [addr.get() for addr in self._pre_validators_addrs]
        return self._pre_validators_cached


    @property
    def post_validators(self) -> list[AutonomousFn]:
        if not hasattr(self, "_post_validators_cached"):
            self._post_validators_cached = [addr.get() for addr in self._post_validators_addrs]
        return self._post_validators_cached


    def can_be_executed(self, kw_args: KwArgs) -> bool:
        with self.portal as portal:
            kw_args = kw_args.pack()
            pre_validators = copy(self.pre_validators)
            portal.entropy_infuser.shuffle(pre_validators)
            for pre_validator in pre_validators:
                pre_validation_result = None
                if isinstance(pre_validator, SimplePreValidatorFn):
                    pre_validation_result = pre_validator()
                else:
                    pre_validation_result = pre_validator(packed_kwargs=kw_args, fn_addr = self.addr)
                if pre_validation_result is not OK:
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


    def _normalize_validators(self
            , validators: list[ValidatorFn] | None
            , validator_type: type
            ) -> list[ValidatorFn]:
        """Return list of validators in a normalized form.

        All the functions-validators are converted to AutonomousFn objects,
        and returned as a list, sorted by functions' hash signatures.
        """
        assert validator_type in {PreValidatorFn, PostValidatorFn}
        if validators is None:
            return []
        if not isinstance(validators, list):
            if callable(validators) or isinstance(validators, ValidatorFn) or isinstance(validators, str):
                validators = [validators]
        assert isinstance(validators, list)
        validators = flatten_list(validators)
        new_validators = []
        for validator in validators:
            if not isinstance(validator, validator_type):
                if validator_type is PreValidatorFn:
                    try:
                        validator = ComplexPreValidatorFn(validator)
                    except:
                        validator = SimplePreValidatorFn(validator)
                elif validator_type is PostValidatorFn:
                    validator = PostValidatorFn(validator)
                else:
                    raise TypeError(f"Unknown type {validator_type}")
            new_validators.append(validator)
        validators = {f.hash_signature: f for f in new_validators}
        validators = sort_dict_by_keys(validators)
        validators = list(validators.values())
        return validators


    @property
    def portal(self) -> ProtectedCodePortal:
        return AutonomousFn.portal.__get__(self)


    def _invalidate_cache(self):
        super()._invalidate_cache()
        if hasattr(self, "_post_validators_cached"):
            assert hasattr(self, "_post_validators_addrs"), "Premature cache invalidation: _post_validators_addrs is missing."
            del self._post_validators_cached
        if hasattr(self, "_pre_validators_cached"):
            assert hasattr(self, "_pre_validators_addrs"), "Premature cache invalidation: _pre_validators_addrs is missing."
            del self._pre_validators_cached