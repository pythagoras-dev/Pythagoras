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
from typing import Any, Callable
from parameterizable import sort_dict_by_keys
from persidict import PersiDict, Joker, KEEP_CURRENT

from .fn_arg_names_checker import check_if_fn_accepts_args
from .._010_basic_portals.basic_portal_core_classes import _visit_portal
from .list_flattener import flatten_list
from .validation_succesful_const import VALIDATION_SUCCESSFUL, ValidationSuccessFlag

from .._060_autonomous_code_portals import *


class ProtectedCodePortal(AutonomousCodePortal):
    """Portal for protected code execution.

    This portal specializes the AutonomousCodePortal to coordinate execution of
    ProtectedFn instances. It carries configuration and storage
    required by validators (e.g., retry throttling) and by protected function
    orchestration.

    Args:
        root_dict (PersiDict | str | None): Optional persistent dictionary or a
            path/identifier to initialize the portal's storage. If None, a
            default in-memory storage may be used.
        p_consistency_checks (float | Joker): Probability or flag controlling
            internal consistency checks performed by the portal. Use
            KEEP_CURRENT to inherit the current setting.
        excessive_logging (bool | Joker): Enables verbose logging of portal and
            function operations. Use KEEP_CURRENT to inherit the current
            setting.
    """
    
    def __init__(self
            , root_dict: PersiDict|str|None = None
            , p_consistency_checks: float|Joker = KEEP_CURRENT
            , excessive_logging: bool|Joker = KEEP_CURRENT
            ):
        super().__init__(root_dict=root_dict
            , p_consistency_checks=p_consistency_checks
            , excessive_logging=excessive_logging)


class ProtectedFn(AutonomousFn):
    """Function wrapper that enforces pre/post validation around execution.

    A ProtectedFn evaluates a sequence of pre-validators before executing the
    underlying function and a sequence of post-validators after execution. If a
    pre-validator returns a ProtectedFnCallSignature, that signature will be
    executed first (allowing validators to perform prerequisite actions) before
    re-attempting the validation/execution loop.
    """

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
        """Construct a ProtectedFn.

        Args:
            fn (Callable | str): The underlying Python function or its source
                code string.
            pre_validators (list[ValidatorFn] | list[Callable] | ValidatorFn | Callable | None):
                Pre-execution validators. Callables are wrapped into
                PreValidatorFn. Lists can be nested and will
                be flattened.
            post_validators (list[ValidatorFn] | list[Callable] | ValidatorFn | Callable | None):
                Post-execution validators. Callables are wrapped into
                PostValidatorFn. Lists can be nested and will be flattened.
            excessive_logging (bool | Joker): Enable verbose logging or inherit
                current setting with KEEP_CURRENT.
            fixed_kwargs (dict[str, Any] | None): Keyword arguments to be fixed
                (bound) for every execution of the function.
            portal (ProtectedCodePortal | None): Portal instance to bind the
                function to.
        """
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

        pre_validators = self._normalize_validators(
            pre_validators, PreValidatorFn)
        post_validators = self._normalize_validators(
            post_validators, PostValidatorFn)

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
        """List of pre-validator functions for this protected function.

        Returns:
            list[AutonomousFn]: A cached list of PreValidatorFn instances.
        """
        if not hasattr(self, "_pre_validators_cache"):
            self._pre_validators_cache = [
                addr.get() for addr in self._pre_validators_addrs]
        return self._pre_validators_cache


    @property
    def post_validators(self) -> list[AutonomousFn]:
        """List of post-validator functions for this protected function.

        Returns:
            list[AutonomousFn]: A cached list of PostValidatorFn instances.
        """
        if not hasattr(self, "_post_validators_cache"):
            self._post_validators_cache = [
                addr.get() for addr in self._post_validators_addrs]
        return self._post_validators_cache


    def can_be_executed(self
            , kw_args: KwArgs
            ) -> ProtectedFnCallSignature|ValidationSuccessFlag|None:
        """Run pre-validators to determine if execution can proceed.

        The portal will shuffle the order of pre-validators. If any validator
        returns a ProtectedFnCallSignature, that signature should be executed by
        the caller prior to executing the protected function (this method simply
        returns it). If any validator fails, None is returned. If all succeed,
        VALIDATION_SUCCESSFUL is returned.

        Args:
            kw_args (KwArgs): Arguments intended for the wrapped function.

        Returns:
            ProtectedFnCallSignature | ValidationSuccessFlag | None: Either a
            signature to execute first, the success flag, or None on failure.
        """
        with self.portal as portal:
            kw_args = kw_args.pack()
            pre_validators = copy(self.pre_validators)
            portal.entropy_infuser.shuffle(pre_validators)
            for pre_validator in pre_validators:
                if isinstance(pre_validator, SimplePreValidatorFn):
                    pre_validation_result = pre_validator()
                else:
                    pre_validation_result = pre_validator(packed_kwargs=kw_args, fn_addr = self.addr)
                if isinstance(pre_validation_result, ProtectedFnCallSignature):
                    return pre_validation_result
                elif pre_validation_result is not VALIDATION_SUCCESSFUL:
                    return None
            return VALIDATION_SUCCESSFUL


    def validate_execution_result(self
            , kw_args: KwArgs
            , result: Any) -> ValidationSuccessFlag|None:
        with self.portal as portal:
            kw_args = kw_args.pack()
            post_validators = copy(self.post_validators)
            portal.entropy_infuser.shuffle(post_validators)
            for post_validator in post_validators:
                if post_validator(packed_kwargs=kw_args, fn_addr = self.addr
                        , result=result) is not VALIDATION_SUCCESSFUL:
                    return None
            return VALIDATION_SUCCESSFUL


    def execute(self, **kwargs) -> Any:
        with (self.portal):
            kw_args = KwArgs(**kwargs)
            while True:
                validation_result = self.can_be_executed(kw_args)
                if isinstance(validation_result, ProtectedFnCallSignature):
                    validation_result.execute()
                    continue
                elif validation_result is None:
                    assert False, (f"Pre-validators failed for function {self.name}")
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
            if (callable(validators)
                    or isinstance(validators, ValidatorFn)
                    or isinstance(validators, str)):
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


    def get_signature(self, arguments:dict) -> ProtectedFnCallSignature:
        return ProtectedFnCallSignature(self, arguments)


class ProtectedFnCallSignature(AutonomousFnCallSignature):
    """A signature of a call to a pure function"""
    _fn_cache: ProtectedFn | None

    def __init__(self, fn: ProtectedFn, arguments: dict):
        assert isinstance(fn, ProtectedFn)
        assert isinstance(arguments, dict)
        super().__init__(fn, arguments)

    @property
    def fn(self) -> ProtectedFn:
        """Return the function object referenced by the signature."""
        return super().fn


class ValidatorFn(AutonomousFn):
    def __init__(self, fn: Callable | str | AutonomousFn
        , fixed_kwargs: dict | None = None
        , excessive_logging: bool | Joker = KEEP_CURRENT
        , portal: AutonomousCodePortal | None = None):
        super().__init__(
            fn=fn
            , fixed_kwargs=fixed_kwargs
            , excessive_logging=excessive_logging
            , portal=portal)

        check_if_fn_accepts_args(self.get_allowed_kwargs_names(), self.source_code)


    @classmethod
    def get_allowed_kwargs_names(cls)->set[str]:
        raise NotImplementedError("This method must be overridden")


    def execute(self,**kwargs) \
            -> ProtectedFnCallSignature | ValidationSuccessFlag | None:
        assert set(kwargs) == self.get_allowed_kwargs_names()
        return super().execute(**kwargs)


class PreValidatorFn(ValidatorFn):
    def __init__(self, fn: Callable | str | AutonomousFn
        , fixed_kwargs: dict | None = None
        , excessive_logging: bool | Joker = KEEP_CURRENT
        , portal: AutonomousCodePortal | None = None):
        super().__init__(
            fn=fn
            , fixed_kwargs=fixed_kwargs
            , excessive_logging=excessive_logging
            , portal=portal)


class SimplePreValidatorFn(PreValidatorFn):
    def __init__(self, fn: Callable | str | AutonomousFn
        , fixed_kwargs: dict | None = None
        , excessive_logging: bool | Joker = KEEP_CURRENT
        , portal: AutonomousCodePortal | None = None):
        super().__init__(
            fn=fn
            , fixed_kwargs=fixed_kwargs
            , excessive_logging=excessive_logging
            , portal=portal)


    @classmethod
    def get_allowed_kwargs_names(cls) -> set[str]:
        """Simple pre-validators do not take any inputs."""
        return set()


class ComplexPreValidatorFn(PreValidatorFn):
    def __init__(self, fn: Callable | str | AutonomousFn
        , fixed_kwargs: dict | None = None
        , excessive_logging: bool | Joker = KEEP_CURRENT
        , portal: AutonomousCodePortal | None = None):
        super().__init__(
            fn=fn
            , fixed_kwargs=fixed_kwargs
            , excessive_logging=excessive_logging
            , portal=portal)


    @classmethod
    def get_allowed_kwargs_names(cls) -> set[str]:
        """Complex pre-validators use info about the function and its input arguments."""
        return {"packed_kwargs", "fn_addr"}


class PostValidatorFn(ValidatorFn):
    def __init__(self, fn: Callable | str | AutonomousFn
        , fixed_kwargs: dict | None = None
        , excessive_logging: bool | Joker = KEEP_CURRENT
        , portal: AutonomousCodePortal | None = None):
        super().__init__(
            fn=fn
            , fixed_kwargs=fixed_kwargs
            , excessive_logging=excessive_logging
            , portal=portal)

    @classmethod
    def get_allowed_kwargs_names(cls) -> set[str]:
        """Post-validators use info about the function, its input arguments and returned value."""
        return {"packed_kwargs", "fn_addr", "result" }
