"""Metaclass providing a `__post_init__` hook for class initialization.

Enables classes to define a `__post_init__` method that runs automatically
after `__init__` completes, similar to dataclasses behavior.
"""

from abc import ABCMeta
from typing import Any, Type, TypeVar


class PostInitMeta(ABCMeta):
    """Metaclass that adds a `__post_init__` hook and initialization flags.

    If the created instance has a `__post_init__` method, it is called
    after `__init__` completes.

    Additionally, if the instance has `_init_finished` or `_post_init_finished`
    attributes, they are set to `True` at the appropriate stages of initialization.
    """

    T = TypeVar('T')

    def __call__(cls: Type[T], *args: Any, **kwargs: Any) -> T:
        """Create instance, run `__init__`, and optionally `__post_init__`.

        Also updates `_init_finished` and `_post_init_finished` flags if they
        are present on the instance.
        """
        instance = super().__call__(*args, **kwargs)
        if not isinstance(instance, cls):
            return instance

        if hasattr(instance, '_init_finished'):
            try:
                instance._init_finished = True
            except AttributeError:
                pass

        if hasattr(instance, '__post_init__'):
            if not callable(instance.__post_init__):
                raise TypeError("__post_init__() must be callable")
            try:
                instance.__post_init__()
            except Exception as e:
                raise type(e)(f"Error in __post_init__: {e}") from e

        if hasattr(instance, '_post_init_finished'):
            try:
                instance._post_init_finished = True
            except AttributeError:
                pass

        return instance