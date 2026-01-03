from persidict.singletons import Singleton


class ValidationSuccessFlag(Singleton):
    """Marker singleton indicating that validation has succeeded.

    This lightweight class is used as a unique sentinel object that signals a
    successful validation outcome in protected code portals. Using a singleton
    avoids ambiguity with other truthy values.
    """
    pass


# A canonical, importable singleton value representing a successful validation.
# Use identity checks (``is VALIDATION_SUCCESSFUL``) rather than equality.
VALIDATION_SUCCESSFUL = ValidationSuccessFlag()