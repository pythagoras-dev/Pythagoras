class ValidationSuccessFlag:
    """Marker singleton indicating that validation has succeeded.

    This lightweight class is used as a unique sentinel object that signals a
    successful validation outcome in protected code portals. Using a singleton
    avoids ambiguity with other truthy values and enables identity checks
    (``is``) in callers.

    Examples:
        >>> from pythagoras._070_protected_code_portals.validation_succesful_const import VALIDATION_SUCCESSFUL
        >>> result = VALIDATION_SUCCESSFUL
        >>> result is VALIDATION_SUCCESSFUL
        True
    """

    _instance = None

    def __new__(cls):
        """Create or return the single shared instance of the class.

        Returns:
            ValidationSuccessFlag: The singleton instance.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

# A canonical, importable singleton value representing a successful validation.
# Use identity checks (``is VALIDATION_SUCCESSFUL``) rather than equality.
VALIDATION_SUCCESSFUL = ValidationSuccessFlag()