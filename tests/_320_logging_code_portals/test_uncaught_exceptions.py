"""Tests for system-wide uncaught exception handler registration and behavior.

This module tests the global exception handling infrastructure that captures
uncaught exceptions and logs them to the active LoggingCodePortal.
"""

import sys
from pythagoras._210_basic_portals import _PortalTester
from pythagoras._320_logging_code_portals import LoggingCodePortal
from pythagoras._320_logging_code_portals.uncaught_exceptions import (
    register_systemwide_uncaught_exception_handlers,
    unregister_systemwide_uncaught_exception_handlers,
    pth_excepthook,
)


def test_handler_registration_increments_counter():
    """Test that handler registration is reference-counted."""
    with _PortalTester(LoggingCodePortal) as tester:
        _portal = tester.portal

        # Handlers should be registered once during portal init
        from pythagoras._320_logging_code_portals.uncaught_exceptions import (
            _number_of_handlers_registrations
        )

        initial_count = _number_of_handlers_registrations

        # Register additional handlers
        register_systemwide_uncaught_exception_handlers()

        # Import again to get updated value
        from pythagoras._320_logging_code_portals.uncaught_exceptions import (
            _number_of_handlers_registrations as count_after
        )

        assert count_after == initial_count + 1


def test_handler_unregistration_decrements_counter():
    """Test that handler unregistration decrements the reference count."""
    with _PortalTester(LoggingCodePortal) as tester:
        _portal = tester.portal

        # Register an extra handler
        register_systemwide_uncaught_exception_handlers()

        from pythagoras._320_logging_code_portals.uncaught_exceptions import (
            _number_of_handlers_registrations
        )
        count_before = _number_of_handlers_registrations

        # Unregister
        unregister_systemwide_uncaught_exception_handlers()

        from pythagoras._320_logging_code_portals.uncaught_exceptions import (
            _number_of_handlers_registrations as count_after
        )

        assert count_after == count_before - 1


def test_pth_excepthook_logs_exception():
    """Test that pth_excepthook logs exceptions to the portal."""
    with _PortalTester(LoggingCodePortal) as tester:
        portal = tester.portal

        initial_crash_count = len(portal._crash_history)

        # Create an exception
        try:
            raise ValueError("Test exception for pth_excepthook")
        except ValueError:
            exc_type, exc_value, trace_back = sys.exc_info()

            # Call the hook directly
            with portal:
                pth_excepthook(exc_type, exc_value, trace_back)

        # Exception should be logged
        assert len(portal._crash_history) == initial_crash_count + 1


def test_pth_excepthook_with_none_exception_type():
    """Test that pth_excepthook handles None exception type gracefully."""
    with _PortalTester(LoggingCodePortal) as tester:
        portal = tester.portal

        initial_crash_count = len(portal._crash_history)

        # Call with None (simulating no exception)
        with portal:
            pth_excepthook(None, None, None)

        # Should not log anything
        assert len(portal._crash_history) == initial_crash_count


def test_exception_logged_once_when_already_processed():
    """Test that already-processed exceptions are not logged again."""
    with _PortalTester(LoggingCodePortal) as tester:
        portal = tester.portal

        initial_crash_count = len(portal._crash_history)

        # Create and mark an exception
        try:
            raise RuntimeError("Already processed exception")
        except RuntimeError:
            exc_type, exc_value, trace_back = sys.exc_info()

            # Log it once
            with portal:
                pth_excepthook(exc_type, exc_value, trace_back)

            # Try to log it again
            with portal:
                pth_excepthook(exc_type, exc_value, trace_back)

        # Should only be logged once
        assert len(portal._crash_history) == initial_crash_count + 1


def test_different_exception_types_logged_separately():
    """Test that different exception types are logged independently."""
    with _PortalTester(LoggingCodePortal) as tester:
        portal = tester.portal

        initial_crash_count = len(portal._crash_history)

        # Log ValueError
        try:
            raise ValueError("First exception")
        except ValueError:
            exc_type, exc_value, trace_back = sys.exc_info()
            with portal:
                pth_excepthook(exc_type, exc_value, trace_back)

        # Log TypeError
        try:
            raise TypeError("Second exception")
        except TypeError:
            exc_type, exc_value, trace_back = sys.exc_info()
            with portal:
                pth_excepthook(exc_type, exc_value, trace_back)

        # Both should be logged
        assert len(portal._crash_history) == initial_crash_count + 2


def test_exception_contains_environment_summary():
    """Test that logged exceptions include execution environment summary."""
    with _PortalTester(LoggingCodePortal) as tester:
        portal = tester.portal

        try:
            raise ValueError("Exception with context")
        except ValueError:
            exc_type, exc_value, trace_back = sys.exc_info()
            with portal:
                pth_excepthook(exc_type, exc_value, trace_back)

        # Get the logged exception
        crash_keys = list(portal._crash_history.keys())
        assert len(crash_keys) > 0

        latest_crash = portal._crash_history[crash_keys[-1]]

        # Should contain environment summary
        assert "execution_environment_summary" in latest_crash or any(
            "execution_environment_summary" in str(k) for k in latest_crash.keys()
        )


def test_multiple_portals_log_independently(tmpdir):
    """Test that multiple portals maintain independent crash histories."""
    with _PortalTester(LoggingCodePortal, tmpdir) as tester1:
        portal1 = tester1.portal

        # Create a second portal manually (can't nest PortalTester)
        portal2 = LoggingCodePortal(str(tmpdir) + "_portal2")

        # Log exception to portal1
        try:
            raise ValueError("Exception for portal1")
        except ValueError:
            exc_type, exc_value, trace_back = sys.exc_info()
            with portal1:
                pth_excepthook(exc_type, exc_value, trace_back)

        # Log different exception to portal2
        try:
            raise TypeError("Exception for portal2")
        except TypeError:
            exc_type, exc_value, trace_back = sys.exc_info()
            with portal2:
                pth_excepthook(exc_type, exc_value, trace_back)

        # Each portal should have exactly one exception
        assert len(portal1._crash_history) == 1
        assert len(portal2._crash_history) == 1


def test_chains_to_previous_excepthook():
    """Test that pth_excepthook chains to the previous handler."""
    from pythagoras._320_logging_code_portals import uncaught_exceptions

    # Reset global state for clean test
    original_count = uncaught_exceptions._number_of_handlers_registrations
    uncaught_exceptions._number_of_handlers_registrations = 0
    uncaught_exceptions._previous_excepthook = None
    original_hook = sys.excepthook

    call_log = []

    def custom_handler(exc_type, exc_value, trace_back):
        call_log.append("custom_handler_called")
        sys.__excepthook__(exc_type, exc_value, trace_back)

    try:
        # Install custom handler BEFORE Pythagoras
        sys.excepthook = custom_handler

        # Now register Pythagoras (should save custom_handler)
        register_systemwide_uncaught_exception_handlers()

        with _PortalTester(LoggingCodePortal) as tester:
            portal = tester.portal

            try:
                raise ValueError("Test chaining")
            except ValueError:
                exc_type, exc_value, trace_back = sys.exc_info()
                with portal:
                    pth_excepthook(exc_type, exc_value, trace_back)

            # Custom handler should have been called via chaining
            assert "custom_handler_called" in call_log
    finally:
        # Restore original state
        sys.excepthook = original_hook
        uncaught_exceptions._number_of_handlers_registrations = original_count
        uncaught_exceptions._previous_excepthook = None


def test_restores_previous_excepthook_on_unregister():
    """Test that unregistration restores the previous handler."""
    from pythagoras._320_logging_code_portals import uncaught_exceptions

    # Reset global state for clean test
    original_count = uncaught_exceptions._number_of_handlers_registrations
    uncaught_exceptions._number_of_handlers_registrations = 0
    uncaught_exceptions._previous_excepthook = None
    original_hook = sys.excepthook

    def custom_handler(exc_type, exc_value, trace_back):
        pass

    try:
        # Install custom handler
        sys.excepthook = custom_handler

        # Register Pythagoras handler (should save custom_handler)
        register_systemwide_uncaught_exception_handlers()

        # Pythagoras should be active
        assert sys.excepthook == pth_excepthook

        # Unregister
        unregister_systemwide_uncaught_exception_handlers()

        # Custom handler should be restored
        assert sys.excepthook == custom_handler
    finally:
        # Restore original state
        sys.excepthook = original_hook
        uncaught_exceptions._number_of_handlers_registrations = original_count
        uncaught_exceptions._previous_excepthook = None


def test_no_infinite_recursion_with_self_reference():
    """Test that chaining doesn't cause infinite recursion if previous is pth_excepthook."""
    from pythagoras._320_logging_code_portals import uncaught_exceptions

    original_prev = uncaught_exceptions._previous_excepthook

    try:
        # Artificially set previous to ourselves (shouldn't happen but defensive)
        uncaught_exceptions._previous_excepthook = pth_excepthook

        with _PortalTester(LoggingCodePortal) as tester:
            portal = tester.portal

            try:
                raise ValueError("Test self-reference")
            except ValueError:
                exc_type, exc_value, trace_back = sys.exc_info()
                with portal:
                    # Should not cause infinite recursion
                    pth_excepthook(exc_type, exc_value, trace_back)
    finally:
        uncaught_exceptions._previous_excepthook = original_prev
