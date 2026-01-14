# """Runtime helper for tracking which portals already store a particular value.
#
# The tracker behaves like a minimal set-like container for portal identifiers:
#
# * Accepts either BasicPortal instances or raw fingerprint strings for insertion
# * Internally stores only canonical PortalStrFingerprint values
# * Offers a minimal mutating API (add, update, discard)
# * Presents a read-only, set-like querying interface
# * Inherits from NotPicklableMixin so that any direct pickling attempt fails
#   immediately
# """
#
# from __future__ import annotations
#
# from typing import Iterable, Iterator
#
# from mixinforge import NotPicklableMixin, SingleThreadEnforcerMixin
#
# from .._210_basic_portals import get_portal_by_fingerprint
# from .._210_basic_portals.basic_portal_core_classes import (
#     PortalStrFingerprint,
#     BasicPortal,
# )
#
#
# PortalLike = BasicPortal | PortalStrFingerprint
#
#
# class PortalTracker(NotPicklableMixin, SingleThreadEnforcerMixin):
#     """A minimal, set-like container that tracks portal identifiers.
#
#     This class stores portal fingerprints efficiently to track which portals
#     already contain a particular value. It provides a set-like interface
#     while internally normalizing all portal references to fingerprint strings.
#
#     Attributes:
#         _fingerprints: The set of canonical portal fingerprints being tracked.
#     """
#
#     __slots__ = ("_fingerprints",)
#
#
#     def __init__(self, initial: Iterable[PortalLike] | None = None) -> None:
#         """Initialize the portal tracker.
#
#         Args:
#             initial: Optional collection of portal identifiers to add
#                 immediately.
#         """
#         self._fingerprints: set[PortalStrFingerprint] = set()
#         self._restrict_to_single_thread()
#         if initial is not None:
#             self.update(initial)
#
#
#     @staticmethod
#     def _to_fingerprint(item: PortalLike) -> PortalStrFingerprint:
#         """Convert a portal-like item to its canonical fingerprint.
#
#         Args:
#             item: A portal instance or fingerprint string to normalize.
#
#         Returns:
#             The canonical PortalStrFingerprint for the item.
#
#         Raises:
#             TypeError: If item is neither a BasicPortal nor a string.
#         """
#         if isinstance(item, str):
#             return PortalStrFingerprint(item)
#         elif isinstance(item, BasicPortal):
#             return item.fingerprint
#         else:
#             raise TypeError(
#                 "Expected BasicPortal or str, "
#                 f"but got {type(item).__name__}"
#             )
#
#
#     def add(self, item: PortalLike) -> None:
#         """Add a single portal identifier to the tracker.
#
#         This operation is idempotent; adding the same identifier multiple
#         times has no additional effect.
#
#         Args:
#             item: A portal instance or fingerprint string to track.
#         """
#         self._fingerprints.add(self._to_fingerprint(item))
#
#
#
#     def update(self, items: Iterable[PortalLike]) -> None:
#         """Add multiple portal identifiers to the tracker.
#
#         Args:
#             items: An iterable of portal instances or fingerprint strings.
#         """
#         for element in items:
#             self.add(element)
#
#     def discard(self, item: PortalLike) -> None:
#         """Remove a portal identifier if present.
#
#         This operation mirrors set.discard behavior: no error is raised if
#         the item is not currently tracked.
#
#         Args:
#             item: A portal instance or fingerprint string to remove.
#         """
#         self._fingerprints.discard(self._to_fingerprint(item))
#
#     def __contains__(self, item: PortalLike) -> bool:
#         """Check whether a portal is being tracked.
#
#         Args:
#             item: A portal instance or fingerprint string to check.
#
#         Returns:
#             True if the portal is tracked, False otherwise.
#         """
#         return self._to_fingerprint(item) in self._fingerprints
#
#     def __sub__(self, other: PortalTracker) -> PortalTracker:
#         """Return a new tracker with portals in self but not in other.
#
#         Args:
#             other: The tracker whose portals should be excluded.
#
#         Returns:
#             A new PortalTracker containing the set difference.
#         """
#         if isinstance(other, PortalTracker):
#             resulting_fingerprints = self._fingerprints - other._fingerprints
#             result = PortalTracker(resulting_fingerprints)
#             return result
#         else:
#             return NotImplemented
#
#     def __rsub__(self, other: PortalTracker) -> PortalTracker:
#         """Return a new tracker with portals in other but not in self.
#
#         Args:
#             other: The tracker to subtract from.
#
#         Returns:
#             A new PortalTracker containing the set difference.
#         """
#         if isinstance(other, PortalTracker):
#             return other - self
#         else:
#             return NotImplemented
#
#     def __eq__(self, other: PortalTracker) -> bool:
#         """Check equality based on tracked portal fingerprints.
#
#         Args:
#             other: The object to compare with.
#
#         Returns:
#             True if both trackers contain the same set of portal fingerprints,
#             False otherwise.
#         """
#         if not isinstance(other, PortalTracker):
#             return NotImplemented
#         return self._fingerprints == other._fingerprints
#
#     def __iter__(self) -> Iterator[BasicPortal]:
#         """Yield portal instances for all tracked fingerprints.
#
#         Returns:
#             An iterator over BasicPortal instances corresponding to the stored
#             fingerprints.
#
#         Raises:
#             KeyError: If a stored fingerprint no longer corresponds to a
#                 registered portal, such as when the portal was cleared or
#                 removed from the global registry.
#         """
#         for fingerprint in list(self._fingerprints):
#             yield get_portal_by_fingerprint(fingerprint)
#
#     def __len__(self) -> int:
#         """Return the number of tracked portals."""
#         return len(self._fingerprints)
#
#     def __bool__(self) -> bool:
#         """Return True if any portals are being tracked, False otherwise."""
#         return bool(self._fingerprints)
#
#     def __repr__(self) -> str:  # pragma: no cover
#         fingerprints_preview = ", ".join(sorted(self._fingerprints)) or "∅"
#         return f"{self.__class__.__name__}({fingerprints_preview})"