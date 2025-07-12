"""Classes and functions that allow protected execution of code.

Protected functions are functions that can be executed only if
certain conditions are met before the execution; also, certain conditions
must be met after the execution in order for the system to accept
and use execution results. These conditions are called validators
(pre-validators and post-validators). A protected function can have many
pre-validators and post-validators.

Validators can be passive (e.g., check if the node has enough RAM)
or active (e.g., check if some external library is installed, and,
if not, try to install it). Validators can be rather complex
(e.g., check if the result, returned by the function, is a valid image).
Under the hood, validators are autonomous functions.
"""

from __future__ import annotations

from copy import copy
from typing import Callable, Any

from persidict import PersiDict, Joker, KEEP_CURRENT

from .validator_fn_classes import *
from .._010_basic_portals.basic_portal_core_classes import _visit_portal
from .._030_data_portals import DataPortal
from .._040_logging_code_portals import KwArgs
from .._030_data_portals import ValueAddr
from parameterizable import sort_dict_by_keys
from .list_flattener import flatten_list
from .validation_succesful_const import VALIDATION_SUCCESSFUL


from .._060_autonomous_code_portals import (
    AutonomousCodePortal, AutonomousFn)


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

    _pre_validators_cache: list[ValidatorFn] | None
    _post_validators_cache: list[ValidatorFn] | None
    _pre_validators_addrs: list[ValueAddr]
    _post_validators_addrs: list[ValueAddr]

    post_validators_arg_names = ["packed_kwargs", "fn_addr", "result"]
    pre_validators_arg_names = ["packed_kwargs", "fn_addr"]

    def __init__(self, fn: Callable | str
                 , pre_validators: list[ValidatorFn] | list[Callable] | ValidatorFn | Callable | None = None
                 , post_validators: list[ValidatorFn] | list[Callable] | ValidatorFn | Callable | None = None
                 , excessive_logging: bool | Joker = KEEP_CURRENT
                 , fixed_kwargs: dict[str,Any] | None = None
                 , portal: ProtectedCodePortal | None = None):
        super().__init__(fn=fn
            , portal = portal
            , fixed_kwargs=fixed_kwargs
            , excessive_logging = excessive_logging)

        if pre_validators is None:
            pre_validators = list()
        else:
            pre_validators = copy(pre_validators)

        if post_validators is None:
            post_validators = list()
        else:
            post_validators = copy(post_validators)

        if isinstance(fn, ProtectedFn):
            pre_validators += fn.pre_validators
            post_validators += fn.post_validators

        pre_validators = self._normalize_validators(pre_validators, PreValidatorFn)
        post_validators = self._normalize_validators(post_validators, PostValidatorFn)

        self._pre_validators_cache = pre_validators
        self._post_validators_cache = post_validators
        self._pre_validators_addrs = [ValueAddr(g, store=False)
                                      for g in self._pre_validators_cache]
        self._post_validators_addrs = [ValueAddr(v, store=False)
                                       for v in self._post_validators_cache]


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
        _visit_portal(self.pre_validators, portal)
        _visit_portal(self.post_validators, portal)


    @property
    def pre_validators(self) -> list[AutonomousFn]:
        if not hasattr(self, "_pre_validators_cache"):
            self._pre_validators_cache = [addr.get() for addr in self._pre_validators_addrs]
        return self._pre_validators_cache


    @property
    def post_validators(self) -> list[AutonomousFn]:
        if not hasattr(self, "_post_validators_cache"):
            self._post_validators_cache = [addr.get() for addr in self._post_validators_addrs]
        return self._post_validators_cache


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
                if pre_validation_result is not VALIDATION_SUCCESSFUL:
                    return False
            return True


    def validate_execution_result(self, kw_args: KwArgs, result: Any) -> bool:
        with self.portal as portal:
            kw_args = kw_args.pack()
            post_validators = copy(self.post_validators)
            portal.entropy_infuser.shuffle(post_validators)
            for post_validator in post_validators:
                if post_validator(packed_kwargs=kw_args, fn_addr = self.addr
                        , result=result) is not VALIDATION_SUCCESSFUL:
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
            , validators: list[ValidatorFn] | ValidatorFn | None
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
        return super().portal


    def _invalidate_cache(self):
        """Invalidate the function's attribute cache.

        If the function's attribute named ATTR is cached,
        its cached value will be stored in an attribute named _ATTR_cache
        This method should delete all such attributes.
        """
        super()._invalidate_cache()
        if hasattr(self, "_post_validators_cached"):
            if not hasattr(self, "_post_validators_addrs"):
                raise AttributeError("Premature cache invalidation: "
                                     "_post_validators_addrs is missing.")
            del self._post_validators_cache
        if hasattr(self, "_pre_validators_cached"):
            if not hasattr(self, "_pre_validators_addrs"):
                raise AttributeError("Premature cache invalidation: "
                                     "_pre_validators_addrs is missing.")
            del self._pre_validators_cache