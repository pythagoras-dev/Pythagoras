"""Reuse flag definitions for sharing portal settings across functions."""

from __future__ import annotations

from typing import Final

from mixinforge import SingletonMixin


class ReuseFlag(SingletonMixin):
    """Singleton flag indicating to use settings from another function."""


USE_FROM_OTHER: Final[ReuseFlag] = ReuseFlag()
""" Flag indicating to use settings from another function. """