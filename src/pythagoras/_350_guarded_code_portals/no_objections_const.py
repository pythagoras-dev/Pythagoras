from typing import Final

from mixinforge import SingletonMixin


class NoObjectionsFlag(SingletonMixin):
    """Marker singleton indicating that an extension raised no objections.

    This lightweight class is used as a unique sentinel object that signals a
    successful outcome in guarded code portals. Using a singleton
    avoids ambiguity with other truthy values.
    """
    pass


# A canonical, importable singleton value representing a successful check.
# Use identity checks (``is NO_OBJECTIONS``) rather than equality.
NO_OBJECTIONS: Final[NoObjectionsFlag] = NoObjectionsFlag()
