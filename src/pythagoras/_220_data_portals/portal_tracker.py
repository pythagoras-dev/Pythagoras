"""
runtime helper for tracking which portals already store a particular value.

The tracker behaves like a very small set wrapper:

* Accepts either `DataPortal` / `BasicPortal` instances or raw
  fingerprint strings for insertion.
* Internally stores **only** canonical `PortalStrFingerprint` values.
* Offers a minimal mutating API (`add`, `update`, `discard`).
* Presents a read-only, set-like querying interface.
* Inherits from `NotPicklableMixin` so that any direct pickling attempt
  fails immediately.

"""

from __future__ import annotations

from typing import Iterable, Iterator

from mixinforge import NotPicklableMixin

from .._210_basic_portals import get_portal_by_fingerprint
from .._210_basic_portals.basic_portal_core_classes import (
    PortalStrFingerprint,
    BasicPortal,
)


PortalLike = BasicPortal | PortalStrFingerprint


class PortalTracker(NotPicklableMixin):
    """A minimal, set-like container that remembers portal fingerprints."""

    __slots__ = ("_fingerprints",)

    # ------------------------------------------------------------------ #
    # Construction                                                       #
    # ------------------------------------------------------------------ #
    def __init__(self, initial: Iterable[PortalLike] | None = None) -> None:
        self._fingerprints: set[PortalStrFingerprint] = set()
        if initial is not None:
            self.update(initial)

    # ------------------------------------------------------------------ #
    # Canonicalisation helper                                            #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _to_fingerprint(item: PortalLike) -> PortalStrFingerprint:
        """Return a canonical `PortalStrFingerprint` for *item*."""
        if isinstance(item, str):
            return PortalStrFingerprint(item)
        if hasattr(item, "fingerprint"):  # DataPortal or BasicPortal
            return PortalStrFingerprint(item.fingerprint)  # type: ignore[arg-type]
        raise TypeError(
            "Expected DataPortal, BasicPortal or str, "
            f"but got {type(item).__name__}"
        )

    # ------------------------------------------------------------------ #
    # Mutating API                                                       #
    # ------------------------------------------------------------------ #
    def add(self, item: PortalLike) -> None:
        """Add a single portal identifier (idempotent)."""
        self._fingerprints.add(self._to_fingerprint(item))



    def update(self, items: Iterable[PortalLike]) -> None:
        """Add many identifiers at once."""
        for element in items:
            self.add(element)

    def discard(self, item: PortalLike) -> None:
        """Remove *item* if present; no error if absent (mirrors `set.discard`)."""
        self._fingerprints.discard(self._to_fingerprint(item))

    # ------------------------------------------------------------------ #
    # Read-only, set-like dunders                                        #
    # ------------------------------------------------------------------ #
    def __contains__(self, item: PortalLike) -> bool:  # type: ignore[override]
        return self._to_fingerprint(item) in self._fingerprints

    def __iter__(self) -> Iterator[BasicPortal]:
        """
        Yield **portal instances** corresponding to the stored fingerprints.

        Resolution is done lazily to avoid keeping strong references and
        to postpone the heavy `DataPortal` import until actually needed.
        """
        # Local import to avoid top-level cycles / heavy dependencies.
        from .data_portal_core_classes import get_data_portal_by_fingerprint

        for fingerprint in list(self._fingerprints):
            try:
                yield get_portal_by_fingerprint(fingerprint)
            except KeyError:
                # Portal may have been unregistered since the fingerprint
                # was stored.  Skip silently; callers can compare lengths
                # if stricter behaviour is required.
                continue

    def __len__(self) -> int:
        return len(self._fingerprints)

    # ------------------------------------------------------------------ #
    # Miscellaneous dunders                                              #
    # ------------------------------------------------------------------ #
    def __bool__(self) -> bool:
        return bool(self._fingerprints)

    def __repr__(self) -> str:  # pragma: no cover
        fingerprints_preview = ", ".join(sorted(self._fingerprints)) or "∅"
        return f"{self.__class__.__name__}({fingerprints_preview})"