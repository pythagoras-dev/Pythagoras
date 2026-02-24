"""Classes and functions that allow guarded execution of code.

Guarded functions are functions that can be executed only if
certain conditions are met before the execution; also, certain conditions
must be met after the execution in order for the system to accept
and use execution results. These conditions are called extensions
(requirements and result checks). A guarded function can have many
requirements and result checks.

Requirements can be passive (e.g., check if the node has enough RAM)
or active (e.g., check if some external library is installed, and,
if not, try to install it). Result checks can be rather complex
(e.g., check if the result, returned by the function, is a valid image).
Under the hood, extensions are autonomous functions.
"""

from __future__ import annotations

from collections.abc import Iterable
from copy import copy
from typing import Final

from mixinforge import sort_dict_by_keys, flatten_nested_collection
from mixinforge.utility_functions import is_atomic_object

from .fn_arg_names_checker import check_if_fn_accepts_args
from .._220_data_portals.kw_args import _visit_portal
from .no_objections_const import NO_OBJECTIONS, NoObjectionsFlag

from .._220_data_portals import DataPortal
from .._340_autonomous_code_portals import *
from .._110_supporting_utilities import get_long_infoname

# Maximum number of requirement retry iterations before raising an error.
# This prevents infinite loops when requirements repeatedly return
# GuardedFnCallSignature objects without making progress.
MAX_REQUIREMENT_ITERATIONS: Final[int] = 10000


class GuardedCodePortal(AutonomousCodePortal):
    """Portal for guarded code execution.

    Specializes AutonomousCodePortal to coordinate execution of GuardedFn
    instances. Provides configuration and storage for extensions (e.g., retry
    throttling) and guarded function orchestration.

    Args:
        root_dict: Persistent dictionary or path to initialize portal storage.
            If None, uses default in-memory storage.
        verbose_logging: Enables verbose logging of portal and function
            operations. Use KEEP_CURRENT to inherit current setting.
    """

    def __init__(self
            , root_dict: PersiDict|str|None = None
            , verbose_logging: bool|Joker = KEEP_CURRENT
            ):
        """Initialize the portal."""
        super().__init__(root_dict=root_dict
            , verbose_logging=verbose_logging)


class GuardedFn(AutonomousFn):
    """Function wrapper that enforces requirements/result checks around execution.

    Evaluates requirements before executing the underlying function and
    result checks after execution. If a requirement returns a
    GuardedFnCallSignature, that signature is executed first (allowing
    requirements to perform prerequisite actions) before re-attempting
    and execution.
    """

    _requirements_addrs: list[ValueAddr]
    _result_checks_addrs: list[ValueAddr]

    result_checks_arg_names = ["packed_kwargs", "fn_addr", "result"]
    requirements_arg_names = ["packed_kwargs", "fn_addr"]

    def __init__(self, fn: Callable | str
                 , requirements: list[ExtensionFn] | list[Callable] | ExtensionFn | Callable | None = None
                 , result_checks: list[ExtensionFn] | list[Callable] | ExtensionFn | Callable | None = None
                 , verbose_logging: bool | Joker | ReuseFlag = KEEP_CURRENT
                 , fixed_kwargs: dict[str,Any] | None = None
                 , portal: GuardedCodePortal | None | ReuseFlag = None):
        """Construct a GuardedFn.

        Args:
            fn: The underlying Python function or its source code string.
            requirements: Pre-execution requirements. Callables are wrapped into
                RequirementFn subclasses. Nested lists are flattened.
            result_checks: Post-execution result checks. Callables are wrapped
                into ResultCheckFn. Nested lists are flattened.
            verbose_logging: Controls verbose logging. Can be True/False,
                KEEP_CURRENT to inherit from context, or USE_FROM_OTHER to copy
                from fn when fn is an existing GuardedFn.
            fixed_kwargs: Keyword arguments bound for every execution.
            portal: Portal to bind this function to. Can be a GuardedCodePortal
                instance, USE_FROM_OTHER to inherit from fn when fn is an existing
                GuardedFn, or None to infer when executed.
        """
        super().__init__(fn=fn
            , portal = portal
            , fixed_kwargs=fixed_kwargs
            , verbose_logging = verbose_logging)

        if requirements is None:
            requirements = list()
        elif (isinstance(requirements, Iterable)
              and not is_atomic_object(requirements)):
            requirements = list(requirements)
        else:
            requirements = [requirements]

        if result_checks is None:
            result_checks = list()
        elif (isinstance(result_checks, Iterable)
              and not is_atomic_object(result_checks)):
            result_checks = list(result_checks)
        else:
            result_checks = [result_checks]

        if isinstance(fn, GuardedFn):
            requirements += fn.requirements
            result_checks += fn.result_checks

        requirements = self._normalize_extensions(
            requirements, RequirementFn)
        result_checks = self._normalize_extensions(
            result_checks, ResultCheckFn)
        self._set_cached_properties(requirements = requirements,
            result_checks = result_checks)

        self._requirements_addrs = [
            ValueAddr(g, store=False) for g in requirements]
        self._result_checks_addrs = [
            ValueAddr(v, store=False) for v in result_checks]


    def __getstate__(self):
        """Return state for pickling."""
        state = super().__getstate__()
        state["requirements_addrs"] = self._requirements_addrs
        state["result_checks_addrs"] = self._result_checks_addrs
        return state


    def __setstate__(self, state):
        """Restore state from unpickling."""
        super().__setstate__(state)
        self._requirements_addrs = state["requirements_addrs"]
        self._result_checks_addrs = state["result_checks_addrs"]


    def _first_visit_to_portal(self, portal: DataPortal) -> None:
        """Register this guarded function and its extensions in a new portal."""
        super()._first_visit_to_portal(portal)
        _visit_portal(self.requirements, portal)
        _visit_portal(self.result_checks, portal)


    @cached_property
    def requirements(self) -> list[AutonomousFn]:
        """Cached list of requirement functions for this guarded function."""
        return [address.get() for address in self._requirements_addrs]


    @cached_property
    def result_checks(self) -> list[AutonomousFn]:
        """Cached list of result check functions for this guarded function."""
        return [address.get() for address in self._result_checks_addrs]


    def can_be_executed(self
            , kw_args: KwArgs
            ) -> GuardedFnCallSignature|NoObjectionsFlag|None:
        """Run requirements to determine if execution can proceed.

        Requirements are shuffled by the portal to avoid order dependencies.
        If any requirement returns a GuardedFnCallSignature, that signature
        should be executed first to satisfy prerequisites (e.g., installing
        dependencies) before re-checking requirements.

        Args:
            kw_args: Arguments intended for the wrapped function.

        Returns:
            NO_OBJECTIONS if all requirements pass, a
            GuardedFnCallSignature to execute first if a requirement requests it,
            or None if a requirement fails.
        """
        with self.portal as portal:
            kw_args = kw_args.pack()
            requirements = copy(self.requirements)
            portal.entropy_infuser.shuffle(requirements)
            for requirement in requirements:
                if isinstance(requirement, SimpleRequirementFn):
                    requirement_result = requirement()
                else:
                    requirement_result = requirement(packed_kwargs=kw_args, fn_addr = self.addr)
                if isinstance(requirement_result, GuardedFnCallSignature):
                    return requirement_result
                elif requirement_result is not NO_OBJECTIONS:
                    return None
            return NO_OBJECTIONS


    def validate_execution_result(self
            , kw_args: KwArgs
            , result: Any) -> NoObjectionsFlag|None:
        """Run result checks to confirm the execution result is acceptable.

        Args:
            kw_args: Arguments that were passed to the guarded function.
            result: The value returned by the guarded function.

        Returns:
            NO_OBJECTIONS if all result checks pass, otherwise None.
        """
        with self.portal as portal:
            kw_args = kw_args.pack()
            result_checks = copy(self.result_checks)
            portal.entropy_infuser.shuffle(result_checks)
            for result_check in result_checks:
                if result_check(packed_kwargs=kw_args, fn_addr = self.addr
                        , result=result) is not NO_OBJECTIONS:
                    return None
            return NO_OBJECTIONS


    def execute(self, **kwargs) -> Any:
        """Execute the guarded function with requirements and result checks.

        Performs the execution loop:
        1. Run requirements; if one returns a GuardedFnCallSignature,
           execute it and retry (up to MAX_REQUIREMENT_ITERATIONS)
        2. Execute the wrapped function
        3. Run result checks and verify they all succeed

        Args:
            **kwargs: Keyword arguments to pass to the wrapped function.

        Returns:
            The result returned by the wrapped function.

        Raises:
            FunctionError: If requirements or result checks fail, or if the
                requirement loop exceeds MAX_REQUIREMENT_ITERATIONS.
        """
        with (self.portal):
            kw_args = KwArgs(**kwargs)
            for iteration in range(MAX_REQUIREMENT_ITERATIONS):
                validation_result = self.can_be_executed(kw_args)
                if isinstance(validation_result, GuardedFnCallSignature):
                    validation_result.execute()
                    continue
                elif validation_result is None:
                    raise FunctionError(f"Requirements failed "
                                        f"for function {self.name}")
                result = super().execute(**kwargs)

                if (self.validate_execution_result(kw_args, result)
                         is not NO_OBJECTIONS):
                    raise FunctionError(f"Result checks failed "
                                        f"for function {self.name}")
                return result
            raise FunctionError(
                f"Requirement loop exceeded {MAX_REQUIREMENT_ITERATIONS} "
                f"iterations for function {self.name}. This may indicate a "
                f"circular dependency between requirements or requirements that "
                f"never reach a successful state.")


    def _normalize_extensions(self
            , extensions: list[ExtensionFn] | ExtensionFn | None
            , extension_type: type
            ) -> list[ExtensionFn]:
        """Return list of extensions in normalized form.

        Wraps plain callables/strings into appropriate ExtensionFn subclasses,
        flattens nested lists, removes duplicates, and enforces deterministic
        ordering via sort_dict_by_keys.

        Args:
            extensions: Extensions in any supported representation (single,
                list, nested lists, etc.).
            extension_type: Either RequirementFn or ResultCheckFn.

        Returns:
            Sorted list of unique extension instances.

        Raises:
            TypeError: If extension_type is not RequirementFn or ResultCheckFn.
        """
        if extension_type not in {RequirementFn, ResultCheckFn}:
            raise TypeError(f"extension_type must be RequirementFn or ResultCheckFn, got {extension_type}")
        if extensions is None:
            return []
        if not isinstance(extensions, list):
            if (callable(extensions)
                    or isinstance(extensions, ExtensionFn)
                    or isinstance(extensions, str)):
                extensions = [extensions]
        if not isinstance(extensions, list):
            raise TypeError(f"extensions must be a list or compatible item(s); got type {get_long_infoname(extensions)}")
        extensions = list(flatten_nested_collection(extensions))
        new_extensions = []
        for extension in extensions:
            if not isinstance(extension, extension_type):
                if extension_type is RequirementFn:
                    try:
                        extension = ComplexRequirementFn(extension)
                    except Exception:
                        extension = SimpleRequirementFn(extension)
                elif extension_type is ResultCheckFn:
                    extension = ResultCheckFn(extension)
                else:
                    raise TypeError(f"Unknown type {extension_type}")
            new_extensions.append(extension)
        extensions = {f.hash_signature: f for f in new_extensions}
        extensions = sort_dict_by_keys(extensions)
        extensions = list(extensions.values())
        return extensions


    @property
    def portal(self) -> GuardedCodePortal:
        """The portal controlling execution context and storage for this function."""
        return super().portal


    def get_signature(self, arguments:dict) -> GuardedFnCallSignature:
        """Create a call signature for this guarded function.

        Args:
            arguments: Arguments to bind into the call signature.

        Returns:
            Signature object representing a particular call to this function.
        """
        return GuardedFnCallSignature(self, arguments)


class GuardedFnCallSignature(AutonomousFnCallSignature):
    """Invocation signature for a guarded function.

    Encapsulates a GuardedFn reference and bound arguments for later execution.
    """

    def __init__(self, fn: GuardedFn, arguments: dict):
        """Initialize the signature.

        Args:
            fn: The guarded function to call.
            arguments: Keyword arguments to be passed at execution time.
        """
        if not isinstance(fn, GuardedFn):
            raise TypeError(f"fn must be a GuardedFn instance, got {get_long_infoname(fn)}")
        if not isinstance(arguments, dict):
            raise TypeError(f"arguments must be a dict, got {get_long_infoname(arguments)}")
        super().__init__(fn, arguments)

    @cached_property
    def fn(self) -> GuardedFn:
        """The guarded function object referenced by this signature."""
        return super().fn


class ExtensionFn(AutonomousFn):
    """Base class for extension function wrappers.

    Ensures the wrapped callable accepts exactly the keyword arguments declared
    by get_allowed_kwargs_names(). Subclasses define the specific interface for
    requirement and result check phases.
    """
    def __init__(self, fn: Callable | str | AutonomousFn
        , fixed_kwargs: dict | None = None
        , verbose_logging: bool | Joker = KEEP_CURRENT
        , portal: AutonomousCodePortal | None = None):
        """Initialize an extension function wrapper.

        Args:
            fn: The extension implementation or its source code.
            fixed_kwargs: Keyword arguments fixed for every call.
            verbose_logging: Controls verbose logging.
            portal: Optional portal binding.
        """
        super().__init__(
            fn=fn
            , fixed_kwargs=fixed_kwargs
            , verbose_logging=verbose_logging
            , portal=portal)

        allowed_kwargs = self.get_allowed_kwargs_names()
        if not check_if_fn_accepts_args(allowed_kwargs, self.source_code):
            raise ValueError(
                f"Extension {get_long_infoname(self)} does not accept required "
                f"kwargs {sorted(allowed_kwargs)}")


    @classmethod
    def get_allowed_kwargs_names(cls)->set[str]:
        """Return the exact set of allowed keyword argument names.

        Subclasses must override to declare their interface.

        Returns:
            Names of keyword arguments accepted by execute().
        """
        raise NotImplementedError("This method must be overridden")


    def execute(self,**kwargs
                ) -> GuardedFnCallSignature | NoObjectionsFlag | None:
        """Execute the extension after verifying keyword arguments.

        Args:
            **kwargs: Must exactly match get_allowed_kwargs_names().

        Returns:
            Depends on extension type and outcome: NO_OBJECTIONS,
            GuardedFnCallSignature, or any other value (e.g. None) for failure.
        """
        expected = self.get_allowed_kwargs_names()
        provided = set(kwargs)
        if provided != expected:
            raise ValueError(f"Invalid kwargs for {type(self).__name__}: expected {sorted(expected)}, got {sorted(provided)}")
        return super().execute(**kwargs)


class RequirementFn(ExtensionFn):
    """Base class for pre-execution requirements.

    Requirements run before the guarded function and may return:
    - NO_OBJECTIONS to allow execution to proceed
    - GuardedFnCallSignature to request execution of a prerequisite action
      before re-checking requirements
    - None or other values to indicate failure

    Important:
        Do NOT return True/False, 1/0, strings, or other truthy/falsy values.
        These are treated as requirement FAILURE. Only NO_OBJECTIONS
        (the sentinel singleton) indicates success. The check uses identity
        comparison (is NO_OBJECTIONS), not truthiness.
    """
    def __init__(self, fn: Callable | str | AutonomousFn
        , fixed_kwargs: dict | None = None
        , verbose_logging: bool | Joker = KEEP_CURRENT
        , portal: AutonomousCodePortal | None = None):
        """Initialize a pre-execution requirement wrapper.

        Args:
            fn: The requirement implementation.
            fixed_kwargs: Keyword arguments fixed for every call.
            verbose_logging: Controls verbose logging.
            portal: Optional portal binding.
        """
        super().__init__(
            fn=fn
            , fixed_kwargs=fixed_kwargs
            , verbose_logging=verbose_logging
            , portal=portal)


class SimpleRequirementFn(RequirementFn):
    """A requirement that takes no runtime inputs.

    The wrapped callable must accept no parameters. Use fixed_kwargs for any
    configuration needed during the requirement check.
    """
    def __init__(self, fn: Callable | str | AutonomousFn
        , fixed_kwargs: dict | None = None
        , verbose_logging: bool | Joker = KEEP_CURRENT
        , portal: AutonomousCodePortal | None = None):
        """Initialize a simple requirement.

        Args:
            fn: The implementation.
            fixed_kwargs: Fixed keyword arguments, if any.
            verbose_logging: Controls verbose logging.
            portal: Optional portal binding.
        """
        super().__init__(
            fn=fn
            , fixed_kwargs=fixed_kwargs
            , verbose_logging=verbose_logging
            , portal=portal)


    @classmethod
    def get_allowed_kwargs_names(cls) -> set[str]:
        """Simple requirements do not take any inputs."""
        return set()


class ComplexRequirementFn(RequirementFn):
    """A requirement that can inspect the function and its inputs.

    The callable must accept keyword arguments packed_kwargs and fn_addr,
    enabling context-aware requirement decisions.
    """
    def __init__(self, fn: Callable | str | AutonomousFn
        , fixed_kwargs: dict | None = None
        , verbose_logging: bool | Joker = KEEP_CURRENT
        , portal: AutonomousCodePortal | None = None):
        """Initialize a complex requirement.

        Args:
            fn: The implementation.
            fixed_kwargs: Fixed keyword arguments, if any.
            verbose_logging: Controls verbose logging.
            portal: Optional portal binding.
        """
        super().__init__(
            fn=fn
            , fixed_kwargs=fixed_kwargs
            , verbose_logging=verbose_logging
            , portal=portal)


    @classmethod
    def get_allowed_kwargs_names(cls) -> set[str]:
        """Complex requirements receive function metadata and input arguments."""
        return {"packed_kwargs", "fn_addr"}


class ResultCheckFn(ExtensionFn):
    """Post-execution result check wrapper.

    Result checks run after the guarded function to validate its result.
    They must return:
    - NO_OBJECTIONS to accept the result
    - None (or any other value) to reject the result

    Important:
        ANY other return value (including True, False, 1, 0, strings, etc.) is
        treated as failure. Do NOT return boolean True/False; use
        NO_OBJECTIONS or None instead. The check is identity-based
        (is NO_OBJECTIONS), not truthiness-based.

    The callable must accept packed_kwargs, fn_addr, and result.
    """
    def __init__(self, fn: Callable | str | AutonomousFn
        , fixed_kwargs: dict | None = None
        , verbose_logging: bool | Joker = KEEP_CURRENT
        , portal: AutonomousCodePortal | None = None):
        """Initialize a post-execution result check.

        Args:
            fn: The implementation.
            fixed_kwargs: Fixed keyword arguments, if any.
            verbose_logging: Controls verbose logging.
            portal: Optional portal binding.
        """
        super().__init__(
            fn=fn
            , fixed_kwargs=fixed_kwargs
            , verbose_logging=verbose_logging
            , portal=portal)

    @classmethod
    def get_allowed_kwargs_names(cls) -> set[str]:
        """Result checks receive function metadata, inputs, and the result."""
        return {"packed_kwargs", "fn_addr", "result" }
