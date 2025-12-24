"""Metaclass enforcing `_init_finished` guard and wiring post-creation hooks.

Mirrors the dataclass `__post_init__` pattern, extending it with `__post_setstate__`
for unpickling. Ensures objects are fully initialized before use.
"""
import functools
from abc import ABCMeta
from dataclasses import is_dataclass
from typing import Any, Type, TypeVar

T = TypeVar('T')

class GuardedInitMeta(ABCMeta):
    """Metaclass guarding initialization and wiring post-creation hooks.

    Requires `_init_finished = False` in `__init__`. Automatically:
    - Sets `_init_finished = True` after `__init__` / `__setstate__` completes
    - Calls `__post_init__` / `__post_setstate__` (if defined) afterwards

    Rejects pickles containing `_init_finished=True` to catch incorrect serialization.
    """

    def __init__(cls, name, bases, dct):
        """Install `__setstate__` wrapper to enforce the initialization guard."""
        super().__init__(name, bases, dct)
        if is_dataclass(cls):
            raise TypeError(
                f"GuardedInitMeta cannot be used with dataclass class {cls.__name__} "
                "because dataclasses already manage __post_init__ with different "
                "object lifecycle assumptions.")

        if '__setstate__' in dct:
            original_setstate = dct['__setstate__']
        elif getattr(cls, '__setstate__', None) is not None:
            inherited = getattr(cls, '__setstate__')
            # Already wrapped by GuardedInitMeta - no need to wrap again
            if getattr(inherited, "__guarded_init_meta_wrapped__", False):
                return
            # Inherited raw __setstate__ - must wrap to set _init_finished
            original_setstate = inherited
        else:
            # No __setstate__ - inject wrapper for default restore + flag
            original_setstate = None

        def setstate_wrapper(self, state):
            """Restore state, set `_init_finished=True`, call `__post_setstate__`."""
            # Validate before delegation - super().__setstate__() might set _init_finished
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
                # Default restore: handle dict, slots, or both
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
                        # Re-raise with context; fall back to RuntimeError if needed
                        try:
                            new_exc = type(e)(f"Error in __post_setstate__: {e}")
                        except Exception:
                            raise RuntimeError(
                                f"Error in __post_setstate__ (original error: {type(e).__name__}: {e})") from e

                        raise new_exc from e

        if original_setstate:
            setstate_wrapper = functools.wraps(original_setstate)(setstate_wrapper)

        setstate_wrapper.__guarded_init_meta_wrapped__ = True
        setstate_wrapper.__name__ = '__setstate__'
        setattr(cls, '__setstate__', setstate_wrapper)

    def __call__(cls: Type[T], *args: Any, **kwargs: Any) -> T:
        """Create instance, enforce init contract, set flag, call `__post_init__`."""
        if is_dataclass(cls):
            raise TypeError(
                f"GuardedInitMeta cannot be used with dataclass class {cls.__name__} "
                "because dataclasses already manage __post_init__ with different "
                "object lifecycle assumptions.")

        instance = super().__call__(*args, **kwargs)
        if not isinstance(instance, cls):
            return instance  # __new__ returned different class - skip hook

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
                # Re-raise with context; fall back to RuntimeError if needed
                try:
                    new_exc = type(e)(f"Error in __post_init__: {e}")
                except Exception:
                    raise RuntimeError(f"Error in __post_init__ (original error: {type(e).__name__}: {e})") from e

                raise new_exc from e

        return instance