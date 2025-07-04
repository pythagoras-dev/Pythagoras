from typing import Callable

from persidict import KEEP_CURRENT, Joker

from pythagoras._060_autonomous_code_portals import AutonomousFn, AutonomousCodePortal
from .fn_arg_names_checker import check_if_fn_accepts_args


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


    def execute(self,**kwargs):
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
