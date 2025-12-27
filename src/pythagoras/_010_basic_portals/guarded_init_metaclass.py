"""Metaclass for strict initialization control and lifecycle hooks.

This module provides GuardedInitMeta, a metaclass that enforces a strict
initialization contract where _init_finished is set to True only after
complete initialization. It wraps __setstate__ to ensure proper state
restoration during unpickling and provides hooks for post-initialization
and post-unpickling tasks.
"""
import functools
from abc import ABCMeta
from dataclasses import is_dataclass
from typing import Any, Type, TypeVar

T = TypeVar('T')


def _validate_pickle_state_integrity(state: Any, cls_name: str) -> None:
    """Ensure pickled state does not claim initialization is finished.

    Args:
        state: The pickle state to validate.
        cls_name: Class name for error reporting.

    Raises:
        RuntimeError: If _init_finished is True in the pickled state.
    """
    candidate_dict, _ = _parse_pickle_state(state, cls_name)

    if candidate_dict is not None and candidate_dict.get("_init_finished") is True:
        raise RuntimeError(
            f"{cls_name} must not be pickled with _init_finished=True")


def _parse_pickle_state(state: Any, cls_name: str) -> tuple[dict | None, dict | None]:
    """Extract __dict__ and __slots__ state from pickle data.

    Args:
        state: The state object passed to __setstate__.
        cls_name: Class name for error reporting.

    Returns:
        A tuple (dict_state, slots_state) where each element is a dictionary or None.

    Raises:
        RuntimeError: If state format is unsupported.
    """
    if state is None:
        return None, None
    elif isinstance(state, dict):
        return state, None
    elif (isinstance(state, tuple) and len(state) == 2
          and (state[0] is None or isinstance(state[0], dict))
          and (state[1] is None or isinstance(state[1], dict))):
        return state
    else:
        raise RuntimeError(
            f"Unsupported pickle state for {cls_name}: {state!r}")


def _restore_dict_state(instance: Any, state_dict: dict, cls_name: str) -> None:
    """Update instance __dict__ with restored state.

    Args:
        instance: The object instance being restored.
        state_dict: Dictionary of attribute values to restore.
        cls_name: Class name for error reporting.

    Raises:
        RuntimeError: If instance has no __dict__ attribute.
    """
    if hasattr(instance, "__dict__"):
        instance.__dict__.update(state_dict)
    else:
        raise RuntimeError(
            f"Cannot restore pickle state for {cls_name}: "
            f"instance has no __dict__ but state contains a dictionary.")


def _restore_slots_state(instance: Any, state_slots: dict[str,Any]) -> None:
    """Restore slot values using setattr.

    Args:
        instance: The object instance being restored.
        state_slots: Dictionary mapping slot names to values.
    """
    for key, value in state_slots.items():
        setattr(instance, key, value)


def _invoke_post_setstate_hook(instance: Any) -> None:
    """Execute __post_setstate__ hook if defined.

    Args:
        instance: The object instance to invoke the hook on.

    Raises:
        TypeError: If __post_setstate__ is not callable.
    """
    post_setstate = getattr(instance, "__post_setstate__", None)
    if post_setstate:
        if not callable(post_setstate):
            raise TypeError(f"__post_setstate__ must be callable, "
                            f"got {instance.__post_setstate__!r}")
        try:
            post_setstate()
        except Exception as e:
            _re_raise_with_context("__post_setstate__", e)


class GuardedInitMeta(ABCMeta):
    """Metaclass for strict initialization control and lifecycle hooks.

    Enforces a contract where _init_finished is False during initialization
    and only becomes True after all initialization code completes. This ensures
    that properties and methods can reliably check initialization state.

    The metaclass automatically wraps __setstate__ to maintain the same
    contract during unpickling, and invokes __post_init__ and __post_setstate__
    hooks when defined.

    Contract:
        - __init__ must set self._init_finished = False immediately.
        - The metaclass sets self._init_finished = True after __init__ returns
          (but before __post_init__, if defined).
        - __setstate__ is wrapped to ensure _init_finished becomes True after
          full state restoration (but before __post_setstate__, if defined).
    """

    def __init__(cls, name, bases, dct):
        """Initialize the class and inject lifecycle enforcement.

        Args:
            name: The class name.
            bases: Base classes.
            dct: Class dictionary.

        Raises:
            TypeError: If class is a dataclass or has multiple GuardedInitMeta bases.
        """
        super().__init__(name, bases, dct)
        _raise_if_dataclass(cls)

        n_guarded_bases = sum(1 for base in bases if isinstance(base, GuardedInitMeta))
        if n_guarded_bases > 1:
            raise TypeError(f"Class {name} has {n_guarded_bases} GuardedInitMeta bases, "
                            "but only 1 is allowed.")

        if '__setstate__' in dct:
            original_setstate = dct['__setstate__']
        elif getattr(cls, '__setstate__', None) is not None:
            inherited = getattr(cls, '__setstate__')
            if getattr(inherited, "__guarded_init_meta_wrapped__", False):
                return
            original_setstate = inherited
        else:
            original_setstate = None

        def setstate_wrapper(self, state):
            """Restore state, finalize initialization, and invoke hook."""
            _validate_pickle_state_integrity(state, type(self).__name__)

            if original_setstate is not None:
                original_setstate(self, state)
            else:
                state_dict, state_slots = _parse_pickle_state(state, type(self).__name__)

                if state_dict is not None:
                    _restore_dict_state(self, state_dict, type(self).__name__)

                if state_slots is not None:
                    _restore_slots_state(self, state_slots)

            if isinstance(self, cls):
                self._init_finished = True
                _invoke_post_setstate_hook(self)

        if original_setstate:
            setstate_wrapper = functools.wraps(original_setstate)(setstate_wrapper)

        setstate_wrapper.__guarded_init_meta_wrapped__ = True
        setstate_wrapper.__name__ = '__setstate__'
        setattr(cls, '__setstate__', setstate_wrapper)

    def __call__(cls: Type[T], *args: Any, **kwargs: Any) -> T:
        """Create instance, enforce initialization contract, and invoke hook.

        Args:
            *args: Positional arguments for __init__.
            **kwargs: Keyword arguments for __init__.

        Returns:
            The initialized instance.

        Raises:
            RuntimeError: If _init_finished is not False after __init__.
            TypeError: If __post_init__ is not callable.
        """
        _raise_if_dataclass(cls)

        instance = super().__call__(*args, **kwargs)
        if not isinstance(instance, cls):
            return instance

        if not hasattr(instance, '_init_finished') or instance._init_finished:
            raise RuntimeError(f"Class {cls.__name__} must set attribute "
                               "_init_finished to False in __init__")

        instance._init_finished = True

        post_init = getattr(instance, "__post_init__", None)
        if post_init:
            if not callable(post_init):
                raise TypeError(f"__post_init__ must be callable, "
                                f"got {instance.__post_init__!r}")
            try:
                post_init()
            except Exception as e:
                _re_raise_with_context("__post_init__", e)

        return instance


def _re_raise_with_context(hook_name: str, exc: Exception) -> None:
    """Re-raise an exception with added context about the hook.

    Args:
        hook_name: The hook name where the error occurred (e.g., "__post_init__").
        exc: The original exception caught during hook execution.

    Raises:
        RuntimeError: If the exception constructor is incompatible.
        Exception: The augmented exception with added context.
    """
    try:
        new_exc = type(exc)(f"Error in {hook_name}: {exc}")
    except Exception:
        raise RuntimeError(
            f"Error in {hook_name} (original error: {type(exc).__name__}: {exc})"
        ) from exc

    raise new_exc from exc


def _raise_if_dataclass(cls: Type) -> None:
    """Forbid GuardedInitMeta on dataclasses due to incompatible lifecycle.

    This check runs in two places:
    1. In GuardedInitMeta.__init__ - catches inheritance from dataclasses.
    2. In GuardedInitMeta.__call__ - catches @dataclass decorator on the class itself.

    Args:
        cls: The class to check.

    Raises:
        TypeError: If the class is a dataclass.
    """
    if is_dataclass(cls):
        raise TypeError(
            f"GuardedInitMeta cannot be used with dataclass class {cls.__name__} "
            "because dataclasses already manage __post_init__ with different "
            "object lifecycle assumptions.")