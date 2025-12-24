"""Metaclass enforcing strict initialization and unpickling lifecycles.

Ensures objects are fully initialized (`_init_finished=True`) only after `__init__`
or `__setstate__` completes. Supports `__post_init__` and `__post_setstate__` hooks.
"""
import functools
from abc import ABCMeta
from dataclasses import is_dataclass
from typing import Any, Type, TypeVar

T = TypeVar('T')

class GuardedInitMeta(ABCMeta):
    """Enforces initialization consistency and executes lifecycle hooks.

    Contract:
    - Classes must set `_init_finished = False` at the start of `__init__`.
    - `_init_finished` is set to `True` only after `__init__` (and optional
      `__post_init__`) completes.
    - `__setstate__` is wrapped to ensure `_init_finished=True` is set only after
      state restoration (and optional `__post_setstate__`).

    Prevents access to partially initialized objects and validates pickle integrity.
    """

    def __init__(cls, name, bases, dct):
        """Wraps `__setstate__` to inject lifecycle enforcement during unpickling."""
        super().__init__(name, bases, dct)
        _raise_if_dataclass(cls)

        if '__setstate__' in dct:
            original_setstate = dct['__setstate__']
        elif getattr(cls, '__setstate__', None) is not None:
            inherited = getattr(cls, '__setstate__')
            # Avoid re-wrapping if the inherited method is already wrapped by this metaclass.
            if getattr(inherited, "__guarded_init_meta_wrapped__", False):
                return
            # Inherited raw __setstate__; must wrap to enforce contract.
            original_setstate = inherited
        else:
            # No __setstate__ defined; inject wrapper using default restoration logic.
            original_setstate = None

        def setstate_wrapper(self, state):
            """Restore state, set `_init_finished=True`, and call `__post_setstate__`."""
            # Prevent unpickling of objects that claim to be already initialized.
            candidate_dict = None
            if isinstance(state, dict):
                candidate_dict = state
            elif (isinstance(state, tuple) and len(state) == 2
                  and isinstance(state[0], dict)):
                candidate_dict = state[0]

            if candidate_dict is not None and candidate_dict.get("_init_finished") is True:
                raise RuntimeError(
                    f"{cls.__name__} must not be pickled with _init_finished=True")

            if original_setstate is not None:
                original_setstate(self, state)
            else:
                # Default restoration: handle dict state, slots, or both.
                state_dict: dict | None
                state_slots: dict | None

                if state is None:
                    state_dict, state_slots = None, None
                elif isinstance(state, dict):
                    state_dict, state_slots = state, None
                elif (isinstance(state, tuple) and len(state) == 2
                      and isinstance(state[0], dict)):
                    state_dict, state_slots = state
                else:
                    raise RuntimeError(
                        f"Unsupported pickle state for {cls.__name__}: {state!r}")

                if state_dict is not None:
                    if hasattr(self, "__dict__"):
                        self.__dict__.update(state_dict)
                    else:
                        raise RuntimeError(
                            f"Cannot restore pickle state for {cls.__name__}: "
                            f"instance has no __dict__ but state contains a dictionary.")

                if state_slots is not None:
                    for key, value in state_slots.items():
                        setattr(self, key, value)

            if isinstance(self, cls):
                self._init_finished = True

                post_setstate = getattr(self, "__post_setstate__", None)
                if post_setstate:
                    if not callable(post_setstate):
                        raise TypeError(f"__post_setstate__ must be callable, "
                                        f"got {self.__post_setstate__!r}")
                    try:
                        post_setstate()
                    except Exception as e:
                        _re_raise_with_context("__post_setstate__", e)

        if original_setstate:
            setstate_wrapper = functools.wraps(original_setstate)(setstate_wrapper)

        setstate_wrapper.__guarded_init_meta_wrapped__ = True
        setstate_wrapper.__name__ = '__setstate__'
        setattr(cls, '__setstate__', setstate_wrapper)

    def __call__(cls: Type[T], *args: Any, **kwargs: Any) -> T:
        """Create instance, enforce init contract, set flag, and call `__post_init__`."""
        _raise_if_dataclass(cls)

        instance = super().__call__(*args, **kwargs)
        if not isinstance(instance, cls):
            return instance  # __new__ returned a different class; skip hooks.

        # Verify that __init__ respected the contract (started by setting flag to False).
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
    """Re-raise *exc* adding context, preserving type if constructor allows."""
    try:
        new_exc = type(exc)(f"Error in {hook_name}: {exc}")
    except Exception:  # pragma: no cover
        # Fallback if the exception's constructor signature mismatches.
        raise RuntimeError(
            f"Error in {hook_name} (original error: {type(exc).__name__}: {exc})"
        ) from exc
    
    raise new_exc from exc


def _raise_if_dataclass(cls: Type) -> None:
    """Ensure `GuardedInitMeta` is not applied to a dataclass."""
    if is_dataclass(cls):
        raise TypeError(
            f"GuardedInitMeta cannot be used with dataclass class {cls.__name__} "
            "because dataclasses already manage __post_init__ with different "
            "object lifecycle assumptions.")