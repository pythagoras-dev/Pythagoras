"""Tests for exception processing tracking and deduplication.

This module tests the exception marking mechanism that prevents the same
exception from being logged multiple times as it propagates through the
call stack or through multiple exception handlers.
"""

import sys
import pytest
from pythagoras._320_logging_code_portals.exception_processing_tracking import (
    _exception_needs_to_be_processed,
    _mark_exception_as_processed,
)


def test_fresh_exception_needs_processing():
    """Test that a fresh exception needs to be processed."""
    try:
        raise ValueError("Fresh exception")
    except ValueError:
        exc_type, exc_value, trace_back = sys.exc_info()
        assert _exception_needs_to_be_processed(exc_type, exc_value, trace_back) is True


def test_none_exception_does_not_need_processing():
    """Test that None exception type returns False."""
    assert _exception_needs_to_be_processed(None, None, None) is False


def test_marked_exception_does_not_need_processing_with_notes():
    """Test that exception marked with __notes__ is skipped."""
    try:
        raise RuntimeError("Exception with notes")
    except RuntimeError:
        exc_type, exc_value, trace_back = sys.exc_info()

        # Mark it
        _mark_exception_as_processed(exc_type, exc_value, trace_back)

        # Should not need processing anymore
        # Check if it has the suppression marker
        if hasattr(exc_value, "__notes__"):
            assert "__suppress_pythagoras_logging__" in exc_value.__notes__
            assert _exception_needs_to_be_processed(exc_type, exc_value, trace_back) is False
        else:
            # Fallback mechanism
            assert hasattr(exc_value, "__suppress_pythagoras_logging__")
            assert _exception_needs_to_be_processed(exc_type, exc_value, trace_back) is False


def test_mark_exception_adds_note_when_available():
    """Test that marking adds a note when add_note method is available."""
    try:
        raise ValueError("Exception for note test")
    except ValueError:
        exc_type, exc_value, trace_back = sys.exc_info()

        # Mark the exception
        _mark_exception_as_processed(exc_type, exc_value, trace_back)

        # Check the marking
        if hasattr(exc_value, "add_note"):
            # Python 3.11+ should use __notes__
            assert hasattr(exc_value, "__notes__")
            assert "__suppress_pythagoras_logging__" in exc_value.__notes__
        else:
            # Older Python should use attribute
            assert hasattr(exc_value, "__suppress_pythagoras_logging__")
            assert exc_value.__suppress_pythagoras_logging__ is True


def test_mark_exception_uses_fallback_attribute():
    """Test that marking uses fallback attribute when add_note is unavailable."""
    # Create a custom exception class without add_note
    class ExceptionWithoutAddNote(Exception):
        pass

    # Ensure it doesn't have add_note
    if hasattr(ExceptionWithoutAddNote, "add_note"):
        # Skip this test on Python 3.11+ where we can't easily remove add_note
        pytest.skip("Cannot test fallback on Python 3.11+ where add_note is always present")

    try:
        raise ExceptionWithoutAddNote("Exception for fallback test")
    except ExceptionWithoutAddNote:
        exc_type, exc_value, trace_back = sys.exc_info()

        # Mark the exception
        _mark_exception_as_processed(exc_type, exc_value, trace_back)

        # Should use fallback attribute
        assert hasattr(exc_value, "__suppress_pythagoras_logging__")
        assert exc_value.__suppress_pythagoras_logging__ is True

        # Should be skipped
        assert _exception_needs_to_be_processed(exc_type, exc_value, trace_back) is False


def test_multiple_markings_are_idempotent():
    """Test that marking an exception multiple times is safe."""
    try:
        raise RuntimeError("Exception for idempotency test")
    except RuntimeError:
        exc_type, exc_value, trace_back = sys.exc_info()

        # Mark it twice
        _mark_exception_as_processed(exc_type, exc_value, trace_back)
        _mark_exception_as_processed(exc_type, exc_value, trace_back)

        # Should still be marked
        assert _exception_needs_to_be_processed(exc_type, exc_value, trace_back) is False


def test_different_exceptions_tracked_independently():
    """Test that different exception instances are tracked independently."""
    try:
        raise ValueError("First exception")
    except ValueError:
        exc_type1, exc_value1, trace_back1 = sys.exc_info()

    try:
        raise ValueError("Second exception")
    except ValueError:
        exc_type2, exc_value2, trace_back2 = sys.exc_info()

    # Mark first exception
    _mark_exception_as_processed(exc_type1, exc_value1, trace_back1)

    # First should be marked
    assert _exception_needs_to_be_processed(exc_type1, exc_value1, trace_back1) is False

    # Second should still need processing
    assert _exception_needs_to_be_processed(exc_type2, exc_value2, trace_back2) is True


def test_exception_with_existing_notes_preserved():
    """Test that existing notes are preserved when adding suppression marker."""
    try:
        exc = ValueError("Exception with existing notes")
        if hasattr(exc, "add_note"):
            exc.add_note("Existing note 1")
            exc.add_note("Existing note 2")
        raise exc
    except ValueError:
        exc_type, exc_value, trace_back = sys.exc_info()

        # Mark it
        _mark_exception_as_processed(exc_type, exc_value, trace_back)

        # Check that suppression marker was added
        if hasattr(exc_value, "__notes__"):
            assert "__suppress_pythagoras_logging__" in exc_value.__notes__
            # Original notes should still be there
            assert "Existing note 1" in exc_value.__notes__
            assert "Existing note 2" in exc_value.__notes__


def test_base_exception_subclasses_handled():
    """Test that BaseException subclasses (not just Exception) are handled."""
    try:
        raise KeyboardInterrupt("User interrupted")
    except KeyboardInterrupt:
        exc_type, exc_value, trace_back = sys.exc_info()

        # Fresh KeyboardInterrupt should need processing
        assert _exception_needs_to_be_processed(exc_type, exc_value, trace_back) is True

        # Mark it
        _mark_exception_as_processed(exc_type, exc_value, trace_back)

        # Should be marked
        assert _exception_needs_to_be_processed(exc_type, exc_value, trace_back) is False
