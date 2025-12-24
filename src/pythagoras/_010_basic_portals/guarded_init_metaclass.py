"""Metaclass enforcing strict initialization and lifecycle hooks.

Ensures `_init_finished` becomes `True` only after `__init__` or `__setstate__`
complete (but before their respective post-hooks) .
"""
import functools
from abc import ABCMeta
from dataclasses import is_dataclass
from typing import Any, Type, TypeVar

T = TypeVar('T')


def _validate_pickle_state_integrity(state: Any, cls_name: str) -> None:
    """Ensure pickled state does not claim initialization is already finished."""
    candidate_dict, _ = _parse_pickle_state(state, cls_name)

    if candidate_dict is not None and candidate_dict.get("_init_finished") is True:
        raise RuntimeError(
            f"{cls_name} must not be pickled with _init_finished=True")


def _parse_pickle_state(state: Any, cls_name: str) -> tuple[dict | None, dict | None]:
    """Extract `__dict__` and `__slots__` state from the pickle data."""
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
    """Update instance `__dict__` with the restored state."""
    if hasattr(instance, "__dict__"):
        instance.__dict__.update(state_dict)
    else:
        raise RuntimeError(
            f"Cannot restore pickle state for {cls_name}: "
            f"instance has no __dict__ but state contains a dictionary.")


def _restore_slots_state(instance: Any, state_slots: dict) -> None:
    """Restore slot values using `setattr`."""
    for key, value in state_slots.items():
        setattr(instance, key, value)


def _invoke_post_setstate_hook(instance: Any) -> None:
    """Execute `__post_setstate__` if defined."""
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

    Contract:
    - `__init__` must set `self._init_finished = False` immediately.
    - The metaclass sets `self._init_finished = True` only after `__init__`
      return (before `__post_init__`, if any).
    - `__setstate__` is wrapped to ensure `_init_finished` becomes `True`
      only after full state restoration (and before `__post_setstate__`, if any).
    """

    def __init__(cls, name, bases, dct):
        """Inject lifecycle enforcement into `__setstate__`."""
        super().__init__(name, bases, dct)
        _raise_if_dataclass(cls)

        n_guarded_bases = sum(1 for base in bases if type(base) is GuardedInitMeta)
        if n_guarded_bases > 1:
            raise TypeError(f"Class {name} has {n_guarded_bases} GuardedInitMeta bases, "
                            "but only 1 is allowed.")

        if '__setstate__' in dct:
            original_setstate = dct['__setstate__']
        elif getattr(cls, '__setstate__', None) is not None:
            inherited = getattr(cls, '__setstate__')
            # Avoid re-wrapping.
            if getattr(inherited, "__guarded_init_meta_wrapped__", False):
                return
            # Inherited raw __setstate__.
            original_setstate = inherited
        else:
            # Use default restoration logic.
            original_setstate = None

        def setstate_wrapper(self, state):
            """Restores state, finalizes initialization, and calls hook."""
            _validate_pickle_state_integrity(state, type(self).__name__)

            if original_setstate is not None:
                original_setstate(self, state)
            else:
                # Handle dict and/or slots.
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
        """Creates instance, enforces initialization contract, and calls hook."""
        _raise_if_dataclass(cls)

        instance = super().__call__(*args, **kwargs)
        if not isinstance(instance, cls):
            return instance  # __new__ returned a different class; skip hooks.

        # Verify contract: __init__ must start with _init_finished=False.
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
    """Re-raise an exception with added context, preserving type if possible."""
    try:
        new_exc = type(exc)(f"Error in {hook_name}: {exc}")
    except Exception:  # pragma: no cover
        # Fallback if constructor signature mismatch.
        raise RuntimeError(
            f"Error in {hook_name} (original error: {type(exc).__name__}: {exc})"
        ) from exc
    
    raise new_exc from exc


def _raise_if_dataclass(cls: Type) -> None:
    """Forbid application to dataclasses (incompatible lifecycle)."""
    if is_dataclass(cls):
        raise TypeError(
            f"GuardedInitMeta cannot be used with dataclass class {cls.__name__} "
            "because dataclasses already manage __post_init__ with different "
            "object lifecycle assumptions.")