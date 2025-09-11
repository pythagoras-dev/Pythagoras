class PythagorasException(Exception):
    """Base exception class for all Pythagoras-related errors.

    This is the base class for all custom exceptions raised by the Pythagoras
    library. It provides a common interface and functionality for all
    Pythagoras-specific error conditions.

    Attributes:
        message: A human-readable description of the error.
    """

    def __init__(self, message):
        """Initialize the exception with an error message.

        Args:
            message: A string describing the error that occurred.
        """
        self.message = message


class NonCompliantFunction(PythagorasException):
    """Exception raised when a function does not comply with Pythagoras requirements.

    This exception is raised when a function fails to meet the compliance
    requirements for use within the Pythagoras framework. This typically
    occurs when functions cannot be properly serialized, analyzed, or
    executed within the portal environment.
    """

    def __init__(self, message):
        """Initialize the exception with an error message.

        Args:
            message: A string describing why the function is non-compliant.
        """
        PythagorasException.__init__(self, message)