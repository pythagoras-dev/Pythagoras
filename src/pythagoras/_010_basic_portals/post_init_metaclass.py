"""Metaclass that wires a `__post_init__` hook and enforces init completion.

It mirrors the dataclass pattern of running `__post_init__` after `__init__`,
while also managing an `_init_finished` guard across normal construction and
pickle restoration.
"""
import functools
from abc import ABCMeta
from dataclasses import is_dataclass
from typing import Any, Type, TypeVar

T = TypeVar('T')

class PostInitMeta(ABCMeta):
    """Run `__post_init__` after construction and guard `_init_finished`.

    Instances must set `_init_finished = False` in `__init__`; the metaclass
    flips it to `True` once construction (or unpickling) is complete and then
    invokes `__post_init__` if present. This ensures post-init logic always
    sees a fully initialized object and prevents persisting a completed flag
    into pickled state.
    """

    def __init__(cls, name, bases, dct):
        """Install `__setstate__` wrapper that restores `_init_finished` safely.

        The wrapper delegates to any existing `__setstate__`, applies default
        pickle restoration if absent, then marks the instance as fully
        initialized. It also rejects pickles that already contain
        `_init_finished=True` to catch incorrect serialization.
        """
        super().__init__(name, bases, dct)

        original_setstate = getattr(cls, '__setstate__', None)

        def setstate_wrapper(self, state):
            # Check for illegal state before delegation to avoid seeing the
            # side-effect of a super().__setstate__() call (which might set
            # _init_finished=True).
            candidate_dict = None
            if isinstance(state, dict):
                candidate_dict = state
            elif (isinstance(state, tuple) and len(state) == 2
                  and isinstance(state[0], dict)):
                candidate_dict = state[0]

            if candidate_dict is not None and candidate_dict.get("_init_finished") is True:
                raise RuntimeError(
                    f"{cls.__name__} must not be pickled with _init_finished=True")

            if original_setstate:
                original_setstate(self, state)
            else:
                # --------------------------------------------------------------
                # 3. Default restore path – gently handle the main permutations
                # --------------------------------------------------------------
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

                if state_dict is not None and hasattr(self, "__dict__"):
                    self.__dict__.update(state_dict)

                if state_slots is not None:
                    for key, value in state_slots.items():
                        setattr(self, key, value)

            self._init_finished = True

        if original_setstate:
            setstate_wrapper = functools.wraps(original_setstate)(setstate_wrapper)

        setstate_wrapper.__name__ = '__setstate__'
        setattr(cls, '__setstate__', setstate_wrapper)

    def __call__(cls: Type[T], *args: Any, **kwargs: Any) -> T:
        """Create instance, assert init contract, and run optional `__post_init__`.

        Requires `_init_finished` to be set to `False` during `__init__`, flips
        it to `True` afterwards, and re-raises any `__post_init__` errors with
        added context. If `__new__` returns a different class instance, the hook
        is skipped.
        """
        if is_dataclass(cls):
            raise TypeError(
                f"PostInitMeta cannot be used with dataclass class {cls.__name__} "
                "because dataclasses already manage __post_init__ with different "
                "object lifecycle assumptions.")

        instance = super().__call__(*args, **kwargs)
        if not isinstance(instance, cls):
            # Skip post-init if __new__ returns instance of different class
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
                # Re-raise with context; fall back to RuntimeError if exception type
                # doesn't accept a single string argument
                try:
                    new_exc = type(e)(f"Error in __post_init__: {e}")
                except Exception:
                    raise RuntimeError(f"Error in __post_init__ (original error: {type(e).__name__}: {e})") from e

                raise new_exc from e

        return instance