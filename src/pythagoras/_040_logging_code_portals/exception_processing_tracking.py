def _exception_needs_to_be_processed(exc_type, exc_value, trace_back) -> bool:
    """Determine whether an exception should be logged by Pythagoras.

    Args:
        exc_type: The exception class (type of the raised exception). May be None.
        exc_value: The exception instance.
        trace_back: The traceback object associated with the exception.

    Returns:
        bool: True if the exception has not yet been marked as processed by
        Pythagoras and should be logged; False otherwise.

    Notes:
        Pythagoras marks exceptions it already handled to avoid duplicate
        logging. This function checks for such marks using either
        Exception.add_note (Python 3.11+) or a fallback attribute.
    """
    if exc_type is None:
        return False

    if hasattr(exc_value, "__notes__"):
        if "__suppress_pythagoras_logging__" in exc_value.__notes__:
            return False
        else:
            return True

    if hasattr(exc_value, "__suppress_pythagoras_logging__"):
        return False

    return True


def _mark_exception_as_processed(exc_type, exc_value, trace_back) -> None:
    """Mark an exception as already processed by Pythagoras.

    This mark prevents duplicate logging of the same exception by subsequent
    handlers.

    Args:
        exc_type: The exception class (type of the raised exception). Unused.
        exc_value: The exception instance to mark.
        trace_back: The traceback object associated with the exception. Unused.

    Side Effects:
        - Mutates the exception by adding a note (preferred) or by setting
          an attribute `__suppress_pythagoras_logging__ = True`.
    """
    if hasattr(exc_value, "add_note"):
        exc_value.add_note(
            "__suppress_pythagoras_logging__")
    else:
        exc_value.__suppress_pythagoras_logging__ = True