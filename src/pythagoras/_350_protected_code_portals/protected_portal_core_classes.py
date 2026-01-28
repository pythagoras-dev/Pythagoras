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
from functools import cached_property
from typing import Callable, Any

from mixinforge import sort_dict_by_keys, flatten_nested_collection
from persidict import PersiDict, Joker, KEEP_CURRENT

from .fn_arg_names_checker import check_if_fn_accepts_args
from .._220_data_portals.kw_args import _visit_portal
from .validation_succesful_const import VALIDATION_SUCCESSFUL, ValidationSuccessFlag

from .._310_ordinary_code_portals import FunctionError
from .._220_data_portals import ValueAddr
from .._220_data_portals import DataPortal
from .._220_data_portals import KwArgs
from .._340_autonomous_code_portals import *
from .._110_supporting_utilities import get_long_infoname


class ProtectedCodePortal(AutonomousCodePortal):
    """Portal for protected code execution.

    Specializes AutonomousCodePortal to coordinate execution of ProtectedFn
    instances. Provides configuration and storage for validators (e.g., retry
    throttling) and protected function orchestration.

    Args:
        root_dict: Persistent dictionary or path to initialize portal storage.
            If None, uses default in-memory storage.
        excessive_logging: Enables verbose logging of portal and function
            operations. Use KEEP_CURRENT to inherit current setting.
    """

    def __init__(self
            , root_dict: PersiDict|str|None = None
            , excessive_logging: bool|Joker = KEEP_CURRENT
            ):
        """Initialize the portal.

        Args:
            root_dict: Backing storage or its path. If None, use default.
            excessive_logging: Verbose logging flag, or KEEP_CURRENT to inherit.
        """
        super().__init__(root_dict=root_dict
            , excessive_logging=excessive_logging)


class ProtectedFn(AutonomousFn):
    """Function wrapper that enforces pre/post validation around execution.

    Evaluates pre-validators before executing the underlying function and
    post-validators after execution. If a pre-validator returns a
    ProtectedFnCallSignature, that signature is executed first (allowing
    validators to perform prerequisite actions) before re-attempting validation
    and execution.
    """

    _pre_validators_addrs: list[ValueAddr]
    _post_validators_addrs: list[ValueAddr]

    post_validators_arg_names = ["packed_kwargs", "fn_addr", "result"]
    pre_validators_arg_names = ["packed_kwargs", "fn_addr"]

    def __init__(self, fn: Callable | str
                 , pre_validators: list[ValidatorFn] | list[Callable] | ValidatorFn | Callable | None = None
                 , post_validators: list[ValidatorFn] | list[Callable] | ValidatorFn | Callable | None = None
                 , excessive_logging: bool | Joker | ReuseFlag = KEEP_CURRENT
                 , fixed_kwargs: dict[str,Any] | None = None
                 , portal: ProtectedCodePortal | None | ReuseFlag = None):
        """Construct a ProtectedFn.

        Args:
            fn: The underlying Python function or its source code string.
            pre_validators: Pre-execution validators. Callables are wrapped into
                PreValidatorFn subclasses. Nested lists are flattened.
            post_validators: Post-execution validators. Callables are wrapped
                into PostValidatorFn. Nested lists are flattened.
            excessive_logging: Controls verbose logging behavior. Can be:

                - True/False to explicitly enable/disable
                - KEEP_CURRENT to inherit from context
                - USE_FROM_OTHER to copy the setting from ``fn`` when ``fn``
                  is an existing ProtectedFn

            fixed_kwargs: Keyword arguments bound for every execution.
            portal: Portal to bind this function to. Can be:

                - A ProtectedCodePortal instance to link directly
                - USE_FROM_OTHER to inherit the portal from ``fn`` when ``fn``
                  is an existing ProtectedFn
                - None to infer a suitable portal when the function is executed
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
        self._set_cached_properties(pre_validators = pre_validators,
            post_validators = post_validators)

        self._pre_validators_addrs = [
            ValueAddr(g, store=False) for g in pre_validators]
        self._post_validators_addrs = [
            ValueAddr(v, store=False) for v in post_validators]


    def __getstate__(self):
        """Return state for pickling."""
        state = super().__getstate__()
        state["pre_validators_addrs"] = self._pre_validators_addrs
        state["post_validators_addrs"] = self._post_validators_addrs
        return state


    def __setstate__(self, state):
        """Restore state from unpickling."""
        super().__setstate__(state)
        self._pre_validators_addrs = state["pre_validators_addrs"]
        self._post_validators_addrs = state["post_validators_addrs"]


    def _first_visit_to_portal(self, portal: DataPortal) -> None:
        """Register this protected function and its validators in a new portal."""
        super()._first_visit_to_portal(portal)
        _visit_portal(self.pre_validators, portal)
        _visit_portal(self.post_validators, portal)


    @cached_property
    def pre_validators(self) -> list[AutonomousFn]:
        """Cached list of pre-validator functions for this protected function."""
        return [address.get() for address in self._pre_validators_addrs]


    @cached_property
    def post_validators(self) -> list[AutonomousFn]:
        """Cached list of post-validator functions for this protected function."""
        return [address.get() for address in self._post_validators_addrs]


    def can_be_executed(self
            , kw_args: KwArgs
            ) -> ProtectedFnCallSignature|ValidationSuccessFlag|None:
        """Run pre-validators to determine if execution can proceed.

        Pre-validators are shuffled by the portal to avoid order dependencies.
        If any validator returns a ProtectedFnCallSignature, that signature
        should be executed first to satisfy prerequisites (e.g., installing
        dependencies) before re-validating.

        Args:
            kw_args: Arguments intended for the wrapped function.

        Returns:
            VALIDATION_SUCCESSFUL if all validators pass, a
            ProtectedFnCallSignature to execute first if a validator requests it,
            or None if validation fails.
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
        """Run post-validators to confirm the execution result is acceptable.

        Args:
            kw_args: Arguments that were passed to the protected function.
            result: The value returned by the protected function.

        Returns:
            VALIDATION_SUCCESSFUL if all post-validators pass, otherwise None.
        """
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
        """Execute the protected function with validation.

        Performs validation and execution loop:
        1. Run pre-validators; if one returns a ProtectedFnCallSignature,
           execute it and retry validation
        2. Execute the wrapped function
        3. Run post-validators and verify they all succeed

        Args:
            **kwargs: Keyword arguments to pass to the wrapped function.

        Returns:
            The result returned by the wrapped function.

        Raises:
            FunctionError: If pre- or post-validation fails.
        """
        with (self.portal):
            kw_args = KwArgs(**kwargs)
            while True:
                validation_result = self.can_be_executed(kw_args)
                if isinstance(validation_result, ProtectedFnCallSignature):
                    validation_result.execute()
                    continue
                elif validation_result is None:
                    raise FunctionError(f"Pre-validators failed "
                                        f"for function {self.name}")
                result = super().execute(**kwargs)

                if (self.validate_execution_result(kw_args, result)
                         is not VALIDATION_SUCCESSFUL):
                    raise FunctionError(f"Post-validators failed "
                                        f"for function {self.name}")
                return result


    def _normalize_validators(self
            , validators: list[ValidatorFn] | ValidatorFn | None
            , validator_type: type
            ) -> list[ValidatorFn]:
        """Return list of validators in normalized form.

        Wraps plain callables/strings into appropriate ValidatorFn subclasses,
        flattens nested lists, removes duplicates, and enforces deterministic
        ordering via sort_dict_by_keys.

        Args:
            validators: Validators in any supported representation (single,
                list, nested lists, etc.).
            validator_type: Either PreValidatorFn or PostValidatorFn.

        Returns:
            Sorted list of unique validator instances.

        Raises:
            TypeError: If validator_type is not PreValidatorFn or PostValidatorFn.
        """
        if validator_type not in {PreValidatorFn, PostValidatorFn}:
            raise TypeError(f"validator_type must be PreValidatorFn or PostValidatorFn, got {validator_type}")
        if validators is None:
            return []
        if not isinstance(validators, list):
            if (callable(validators)
                    or isinstance(validators, ValidatorFn)
                    or isinstance(validators, str)):
                validators = [validators]
        if not isinstance(validators, list):
            raise TypeError(f"validators must be a list or compatible item(s); got type {get_long_infoname(validators)}")
        validators = list(flatten_nested_collection(validators))
        new_validators = []
        for validator in validators:
            if not isinstance(validator, validator_type):
                if validator_type is PreValidatorFn:
                    try:
                        validator = ComplexPreValidatorFn(validator)
                    except Exception:
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
        """The portal controlling execution context and storage for this function."""
        return super().portal


    def get_signature(self, arguments:dict) -> ProtectedFnCallSignature:
        """Create a call signature for this protected function.

        Args:
            arguments: Arguments to bind into the call signature.

        Returns:
            Signature object representing a particular call to this function.
        """
        return ProtectedFnCallSignature(self, arguments)


class ProtectedFnCallSignature(AutonomousFnCallSignature):
    """Invocation signature for a protected function.

    Encapsulates a ProtectedFn reference and bound arguments for later execution.
    """

    def __init__(self, fn: ProtectedFn, arguments: dict):
        """Initialize the signature.

        Args:
            fn: The protected function to call.
            arguments: Keyword arguments to be passed at execution time.
        """
        if not isinstance(fn, ProtectedFn):
            raise TypeError(f"fn must be a ProtectedFn instance, got {get_long_infoname(fn)}")
        if not isinstance(arguments, dict):
            raise TypeError(f"arguments must be a dict, got {get_long_infoname(arguments)}")
        super().__init__(fn, arguments)

    @cached_property
    def fn(self) -> ProtectedFn:
        """The protected function object referenced by this signature."""
        return super().fn


class ValidatorFn(AutonomousFn):
    """Base class for validator wrappers.

    Ensures the wrapped callable accepts exactly the keyword arguments declared
    by get_allowed_kwargs_names(). Subclasses define the specific interface for
    pre- and post-validation phases.
    """
    def __init__(self, fn: Callable | str | AutonomousFn
        , fixed_kwargs: dict | None = None
        , excessive_logging: bool | Joker = KEEP_CURRENT
        , portal: AutonomousCodePortal | None = None):
        """Initialize a validator function wrapper.

        Args:
            fn: The validator implementation or its source code.
            fixed_kwargs: Keyword arguments fixed for every validation call.
            excessive_logging: Controls verbose logging.
            portal: Optional portal binding.
        """
        super().__init__(
            fn=fn
            , fixed_kwargs=fixed_kwargs
            , excessive_logging=excessive_logging
            , portal=portal)

        check_if_fn_accepts_args(self.get_allowed_kwargs_names(), self.source_code)


    @classmethod
    def get_allowed_kwargs_names(cls)->set[str]:
        """Return the exact set of allowed keyword argument names.

        Subclasses must override to declare their interface.

        Returns:
            Names of keyword arguments accepted by execute().
        """
        raise NotImplementedError("This method must be overridden")


    def execute(self,**kwargs
                ) -> ProtectedFnCallSignature | ValidationSuccessFlag | None:
        """Execute the validator after verifying keyword arguments.

        Args:
            **kwargs: Must exactly match get_allowed_kwargs_names().

        Returns:
            Depends on validator type and outcome: VALIDATION_SUCCESSFUL,
            ProtectedFnCallSignature, or any other value (e.g. None) for failure.
        """
        expected = self.get_allowed_kwargs_names()
        provided = set(kwargs)
        if provided != expected:
            raise ValueError(f"Invalid kwargs for {type(self).__name__}: expected {sorted(expected)}, got {sorted(provided)}")
        return super().execute(**kwargs)


class PreValidatorFn(ValidatorFn):
    """Base class for pre-execution validators.

    Pre-validators run before the protected function and may return:
    - VALIDATION_SUCCESSFUL to allow execution to proceed
    - ProtectedFnCallSignature to request execution of a prerequisite action
      before re-validating
    - None or other values to indicate failure

    Important:
        Do NOT return True/False, 1/0, strings, or other truthy/falsy values.
        These are treated as validation FAILURE. Only VALIDATION_SUCCESSFUL
        (the sentinel singleton) indicates success. The check uses identity
        comparison (is VALIDATION_SUCCESSFUL), not truthiness.
    """
    def __init__(self, fn: Callable | str | AutonomousFn
        , fixed_kwargs: dict | None = None
        , excessive_logging: bool | Joker = KEEP_CURRENT
        , portal: AutonomousCodePortal | None = None):
        """Initialize a pre-execution validator wrapper.

        Args:
            fn: The pre-validator implementation.
            fixed_kwargs: Keyword arguments fixed for every call.
            excessive_logging: Controls verbose logging.
            portal: Optional portal binding.
        """
        super().__init__(
            fn=fn
            , fixed_kwargs=fixed_kwargs
            , excessive_logging=excessive_logging
            , portal=portal)


class SimplePreValidatorFn(PreValidatorFn):
    """A pre-validator that takes no runtime inputs.

    The wrapped callable must accept no parameters. Use fixed_kwargs for any
    configuration needed during validation.
    """
    def __init__(self, fn: Callable | str | AutonomousFn
        , fixed_kwargs: dict | None = None
        , excessive_logging: bool | Joker = KEEP_CURRENT
        , portal: AutonomousCodePortal | None = None):
        """Initialize a simple pre-validator.

        Args:
            fn: The implementation.
            fixed_kwargs: Fixed keyword arguments, if any.
            excessive_logging: Controls verbose logging.
            portal: Optional portal binding.
        """
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
    """A pre-validator that can inspect the function and its inputs.

    The callable must accept keyword arguments packed_kwargs and fn_addr,
    enabling context-aware validation decisions.
    """
    def __init__(self, fn: Callable | str | AutonomousFn
        , fixed_kwargs: dict | None = None
        , excessive_logging: bool | Joker = KEEP_CURRENT
        , portal: AutonomousCodePortal | None = None):
        """Initialize a complex pre-validator.

        Args:
            fn: The implementation.
            fixed_kwargs: Fixed keyword arguments, if any.
            excessive_logging: Controls verbose logging.
            portal: Optional portal binding.
        """
        super().__init__(
            fn=fn
            , fixed_kwargs=fixed_kwargs
            , excessive_logging=excessive_logging
            , portal=portal)


    @classmethod
    def get_allowed_kwargs_names(cls) -> set[str]:
        """Complex pre-validators receive function metadata and input arguments."""
        return {"packed_kwargs", "fn_addr"}


class PostValidatorFn(ValidatorFn):
    """Post-execution validator wrapper.

    Post-validators run after the protected function to validate its result.
    They must return:
    - VALIDATION_SUCCESSFUL to accept the result
    - None (or any other value) to reject the result

    Important:
        ANY other return value (including True, False, 1, 0, strings, etc.) is
        treated as validation failure. Do NOT return boolean True/False; use
        VALIDATION_SUCCESSFUL or None instead. The check is identity-based
        (is VALIDATION_SUCCESSFUL), not truthiness-based.

    The callable must accept packed_kwargs, fn_addr, and result.
    """
    def __init__(self, fn: Callable | str | AutonomousFn
        , fixed_kwargs: dict | None = None
        , excessive_logging: bool | Joker = KEEP_CURRENT
        , portal: AutonomousCodePortal | None = None):
        """Initialize a post-execution validator.

        Args:
            fn: The implementation.
            fixed_kwargs: Fixed keyword arguments, if any.
            excessive_logging: Controls verbose logging.
            portal: Optional portal binding.
        """
        super().__init__(
            fn=fn
            , fixed_kwargs=fixed_kwargs
            , excessive_logging=excessive_logging
            , portal=portal)

    @classmethod
    def get_allowed_kwargs_names(cls) -> set[str]:
        """Post-validators receive function metadata, inputs, and the result."""
        return {"packed_kwargs", "fn_addr", "result" }
