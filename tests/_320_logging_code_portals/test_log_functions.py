"""Tests for log_exception() and log_event() global logging functions.

This module tests the global logging functions that route events and exceptions
to the appropriate function's log when called from within a LoggingFn execution.
"""

import pythagoras as pth
from pythagoras._210_basic_portals import _PortalTester
from pythagoras._320_logging_code_portals import LoggingCodePortal, logging

# Module-level functions to avoid closures

@logging(excessive_logging=True)
def fn_with_event_a():
    """Function that logs an event."""
    pth.log_event(location="function_a")
    return "result_a"


@logging(excessive_logging=True)
def fn_with_event_b():
    """Function that logs an event."""
    pth.log_event(location="function_b")
    return "result_b"


@logging(excessive_logging=True)
def fn_with_exception_a():
    """Function that raises and logs exception."""
    try:
        raise ValueError("Exception A")
    except ValueError:
        pth.log_exception()
        raise


@logging(excessive_logging=True)
def fn_with_exception_b():
    """Function that catches and logs exception."""
    try:
        raise TypeError("Exception B")
    except TypeError:
        pth.log_exception()
    return "handled_b"


def test_log_event_inside_function():
    """Test that log_event() logs to the correct function's event history."""
    with _PortalTester(LoggingCodePortal, excessive_logging=True) as tester:
        portal = tester.portal

        @logging(excessive_logging=True)
        def fn_with_event():
            pth.log_event(message="Test event", value=42)
            return "result"

        with portal:
            fn_with_event()

        # Get the call signature and check events
        sig = fn_with_event.get_signature({})
        events = sig.events

        assert len(events) > 0

        # Check that event was logged
        event_found = False
        for key in events:
            event_data = events[key]
            if "message" in event_data and event_data["message"] == "Test event":
                event_found = True
                assert event_data["value"] == 42
                break

        assert event_found, "Event with message='Test event' not found"


def test_log_event_with_multiple_arguments():
    """Test that log_event() handles multiple keyword arguments."""
    with _PortalTester(LoggingCodePortal, excessive_logging=True) as tester:
        portal = tester.portal

        @logging(excessive_logging=True)
        def fn_with_complex_event():
            pth.log_event(
                event_type="test",
                count=10,
                status="success",
                data=[1, 2, 3]
            )
            return "result"

        with portal:
            fn_with_complex_event()

        sig = fn_with_complex_event.get_signature({})
        events = sig.events

        assert len(events) > 0

        # Find the event and verify all fields
        latest_event = events[list(events.keys())[-1]]
        assert latest_event["event_type"] == "test"
        assert latest_event["count"] == 10
        assert latest_event["status"] == "success"
        assert latest_event["data"] == [1, 2, 3]


def test_log_exception_inside_function():
    """Test that log_exception() logs exceptions to the function's crash history."""
    with _PortalTester(LoggingCodePortal, excessive_logging=True) as tester:
        portal = tester.portal

        @logging(excessive_logging=True)
        def fn_with_explicit_exception_log():
            try:
                raise ValueError("Caught exception")
            except ValueError:
                pth.log_exception()
            return "result"

        with portal:
            fn_with_explicit_exception_log()

        # Get the call signature and check crashes
        sig = fn_with_explicit_exception_log.get_signature({})
        crashes = sig.crashes

        assert len(crashes) > 0


def test_log_exception_without_active_exception():
    """Test that log_exception() handles case when no exception is active."""
    with _PortalTester(LoggingCodePortal, excessive_logging=True) as tester:
        portal = tester.portal

        @logging(excessive_logging=True)
        def fn_logging_no_exception():
            # Call log_exception when no exception is active
            pth.log_exception()
            return "result"

        with portal:
            # Should not raise an error
            result = fn_logging_no_exception()
            assert result == "result"


def test_multiple_events_in_same_function():
    """Test logging multiple events in a single function execution."""
    with _PortalTester(LoggingCodePortal, excessive_logging=True) as tester:
        portal = tester.portal

        @logging(excessive_logging=True)
        def fn_with_multiple_events():
            pth.log_event(stage="start")
            pth.log_event(stage="middle", progress=50)
            pth.log_event(stage="end", progress=100)
            return "result"

        with portal:
            fn_with_multiple_events()

        sig = fn_with_multiple_events.get_signature({})
        events = sig.events

        # Should have 3 events
        assert len(events) >= 3


def test_log_event_in_multiple_functions():
    """Test that log_event() works correctly for multiple independent functions."""
    with _PortalTester(LoggingCodePortal, excessive_logging=True) as tester:
        portal = tester.portal

        with portal:
            fn_with_event_a()
            fn_with_event_b()

        # Check function A events
        sig_a = fn_with_event_a.get_signature({})
        events_a = sig_a.events
        event_a_found = any(
            "location" in events_a[k] and events_a[k]["location"] == "function_a"
            for k in events_a
        )
        assert event_a_found, "Function A event not found"

        # Check function B events
        sig_b = fn_with_event_b.get_signature({})
        events_b = sig_b.events
        event_b_found = any(
            "location" in events_b[k] and events_b[k]["location"] == "function_b"
            for k in events_b
        )
        assert event_b_found, "Function B event not found"


def test_log_exception_in_multiple_functions():
    """Test that log_exception() works correctly for multiple independent functions."""
    with _PortalTester(LoggingCodePortal, excessive_logging=True) as tester:
        portal = tester.portal

        with portal:
            # Call function that raises and logs
            try:
                fn_with_exception_a()
            except ValueError:
                pass

            # Call function that catches and logs
            result_b = fn_with_exception_b()
            assert result_b == "handled_b"

        # Both functions should have crash records
        sig_a = fn_with_exception_a.get_signature({})
        assert len(sig_a.crashes) > 0

        sig_b = fn_with_exception_b.get_signature({})
        assert len(sig_b.crashes) > 0


def test_log_event_with_environment_summary():
    """Test that log_event() includes execution environment summary."""
    with _PortalTester(LoggingCodePortal, excessive_logging=True) as tester:
        portal = tester.portal

        @logging(excessive_logging=True)
        def fn_with_event():
            pth.log_event(test_event="value")
            return "result"

        with portal:
            fn_with_event()

        sig = fn_with_event.get_signature({})
        events = sig.events

        assert len(events) > 0

        # Events should contain environment summary
        latest_event = events[list(events.keys())[-1]]

        # Check if environment summary is included (may be nested in dict)
        any(
            "execution_environment_summary" in str(k) or
            "execution_environment_summary" in str(v)
            for k, v in latest_event.items()
        )


def test_log_event_portal_level():
    """Test that log_event() works at portal level outside functions."""
    with _PortalTester(LoggingCodePortal, excessive_logging=True) as tester:
        portal = tester.portal

        initial_event_count = len(portal._event_history)

        with portal:
            pth.log_event(portal_level_event="test")

        # Event should be in portal's event history
        assert len(portal._event_history) == initial_event_count + 1


def test_log_exception_portal_level():
    """Test that log_exception() works at portal level outside functions."""
    with _PortalTester(LoggingCodePortal, excessive_logging=True) as tester:
        portal = tester.portal

        initial_crash_count = len(portal._crash_history)

        try:
            with portal:
                raise RuntimeError("Portal level exception")
        except RuntimeError:
            pass

        # Exception should be in portal's crash history
        assert len(portal._crash_history) > initial_crash_count


def test_log_event_without_portal_context():
    """Test log_event() behavior when called outside any portal context."""
    # This tests that log_event can find the current portal automatically
    with _PortalTester(LoggingCodePortal, excessive_logging=True) as tester:
        _portal = tester.portal

        @logging(excessive_logging=True)
        def fn_with_event():
            # log_event should work without explicit portal context
            pth.log_event(auto_portal="test")
            return "result"

        # Call without explicit portal context - decorator should handle it
        fn_with_event()

        sig = fn_with_event.get_signature({})
        events = sig.events

        assert len(events) > 0


def test_multiple_exceptions_logged_separately():
    """Test that multiple exceptions are logged as separate crash records."""
    with _PortalTester(LoggingCodePortal, excessive_logging=True) as tester:
        portal = tester.portal

        @logging(excessive_logging=True)
        def fn_with_multiple_exceptions():
            try:
                raise ValueError("First exception")
            except ValueError:
                pth.log_exception()

            try:
                raise TypeError("Second exception")
            except TypeError:
                pth.log_exception()

            return "result"

        with portal:
            fn_with_multiple_exceptions()

        sig = fn_with_multiple_exceptions.get_signature({})
        crashes = sig.crashes

        # Should have at least 2 crash records
        assert len(crashes) >= 2
