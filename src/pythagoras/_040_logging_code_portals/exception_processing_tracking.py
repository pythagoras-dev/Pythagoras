def _exception_needs_to_be_processed(exc_type, exc_value, trace_back) -> bool:
    if exc_type is None:
        return False

    if hasattr(exc_value, "__notes__"):
        if "__suppress_logging__" in exc_value.__notes__:
            return False
        else:
            return True

    if hasattr(exc_value, "__suppress_logging__"):
        return False

    return True


def _mark_exception_as_processed(exc_type, exc_value, trace_back) -> None:
    if hasattr(exc_value, "add_note"):
        exc_value.add_note(
            "__suppress_logging__")
    else:
        exc_value.__suppress_logging__ = True