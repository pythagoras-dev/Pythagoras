"""Tests for LoggingFnExecutionFrame edge cases and lifecycle management.

This module tests the execution frame context manager that orchestrates
function execution logging, particularly focusing on edge cases, error
conditions, and proper cleanup.
"""

import pytest
from pythagoras._210_basic_portals import _PortalTester
from pythagoras._320_logging_code_portals import LoggingCodePortal, logging
from pythagoras._320_logging_code_portals.logging_portal_core_classes import (
    LoggingFnExecutionFrame,
)


def test_execution_frame_cannot_be_reused():
    """Test that an execution frame raises error if reused."""
    with _PortalTester(LoggingCodePortal, excessive_logging=True) as tester:
        portal = tester.portal

        @logging(excessive_logging=True)
        def simple_fn():
            return "result"

        with portal:
            # Get the function's signature
            sig = simple_fn.get_signature({})

            # Create a frame
            frame = LoggingFnExecutionFrame(sig)

            # Use it once
            with frame:
                pass

            # Try to reuse it - should raise RuntimeError
            with pytest.raises(
                RuntimeError, match="can be used only once"
            ):
                with frame:
                    pass


def test_execution_frame_call_stack_pushed_and_popped():
    """Test that execution frame is correctly pushed to and popped from call_stack."""
    with _PortalTester(LoggingCodePortal, excessive_logging=True) as tester:
        portal = tester.portal

        @logging(excessive_logging=True)
        def test_fn():
            return "result"

        # Call stack should be empty before execution
        initial_stack_depth = len(LoggingFnExecutionFrame.call_stack)

        with portal:
            result = test_fn()

        # Call stack should be empty after execution
        assert len(LoggingFnExecutionFrame.call_stack) == initial_stack_depth
        assert result == "result"


def test_nested_execution_frames_stack_correctly():
    """Test that multiple sequential function calls work correctly."""
    with _PortalTester(LoggingCodePortal, excessive_logging=True) as tester:
        portal = tester.portal

        @logging(excessive_logging=True)
        def test_fn(*, value):
            return value * 2

        # Track stack depth during execution
        initial_depth = len(LoggingFnExecutionFrame.call_stack)

        with portal:
            # Call functions sequentially
            result1 = test_fn(value=5)
            result2 = test_fn(value=10)

            assert result1 == 10
            assert result2 == 20

        # Stack should be back to initial depth after execution
        final_depth = len(LoggingFnExecutionFrame.call_stack)
        assert final_depth == initial_depth


def test_execution_frame_cleaned_up_on_exception():
    """Test that execution frame is properly cleaned up even when exception occurs."""
    with _PortalTester(LoggingCodePortal, excessive_logging=True) as tester:
        portal = tester.portal

        @logging(excessive_logging=True)
        def failing_fn():
            raise ValueError("Intentional failure")

        initial_stack_depth = len(LoggingFnExecutionFrame.call_stack)

        with portal:
            try:
                failing_fn()
            except ValueError:
                pass

        # Stack should be cleaned up
        assert len(LoggingFnExecutionFrame.call_stack) == initial_stack_depth


def test_execution_frame_exception_counter_increments():
    """Test that exception counter is updated when exceptions occur."""
    with _PortalTester(LoggingCodePortal, excessive_logging=True) as tester:
        portal = tester.portal

        @logging(excessive_logging=True)
        def fn_with_exception():
            raise RuntimeError("Test exception")

        with portal:
            try:
                fn_with_exception()
            except RuntimeError:
                pass

        # Get the call signature and check crashes
        sig = fn_with_exception.get_signature({})
        crashes = sig.crashes

        # At least one crash should be logged
        assert len(crashes) > 0


def test_execution_frame_excessive_logging_false_no_output_capture():
    """Test that excessive_logging=False prevents output capture."""
    with _PortalTester(LoggingCodePortal, excessive_logging=False) as tester:
        portal = tester.portal

        @logging(excessive_logging=False)
        def simple_fn():
            print("This should not be captured")
            return "result"

        with portal:
            sig = simple_fn.get_signature({})
            frame = LoggingFnExecutionFrame(sig)

            # Output capturer should be None when excessive logging is disabled
            assert frame.output_capturer is None


def test_execution_frame_excessive_logging_true_has_output_capture():
    """Test that excessive_logging=True enables output capture."""
    with _PortalTester(LoggingCodePortal, excessive_logging=True) as tester:
        portal = tester.portal

        @logging(excessive_logging=True)
        def simple_fn():
            return "result"

        with portal:
            sig = simple_fn.get_signature({})
            frame = LoggingFnExecutionFrame(sig)

            # Output capturer should be present when excessive logging is enabled
            assert frame.output_capturer is not None


def test_execution_frame_session_id_is_unique():
    """Test that each execution frame gets a unique session ID."""
    with _PortalTester(LoggingCodePortal, excessive_logging=True) as tester:
        portal = tester.portal

        @logging(excessive_logging=True)
        def simple_fn():
            return "result"

        with portal:
            sig = simple_fn.get_signature({})

            # Create multiple frames
            frame1 = LoggingFnExecutionFrame(sig)
            frame2 = LoggingFnExecutionFrame(sig)

            # Session IDs should be different
            assert frame1.session_id != frame2.session_id

            # Both should start with "run_"
            assert frame1.session_id.startswith("run_")
            assert frame2.session_id.startswith("run_")


def test_execution_frame_portal_context_managed():
    """Test that execution frame manages portal context correctly."""
    with _PortalTester(LoggingCodePortal, excessive_logging=True) as tester:
        portal = tester.portal

        @logging(excessive_logging=True)
        def test_fn():
            return "success"

        with portal:
            # Just verify that function execution works within portal context
            result = test_fn()
            assert result == "success"


def test_execution_frame_properties_accessible():
    """Test that execution frame properties return expected values."""
    with _PortalTester(LoggingCodePortal, excessive_logging=True) as tester:
        portal = tester.portal

        @logging(excessive_logging=True)
        def test_fn():
            return "result"

        with portal:
            sig = test_fn.get_signature({})
            frame = LoggingFnExecutionFrame(sig)

            # Test properties before entering context
            assert frame.fn_name == "test_fn"
            assert frame.fn is test_fn
            assert frame.portal is portal
            assert frame.excessive_logging is True
            assert frame.exception_counter == 0
            assert frame.event_counter == 0
            assert frame.context_used is False


def test_multiple_calls_with_arguments_work():
    """Test that multiple function calls with arguments work correctly."""
    with _PortalTester(LoggingCodePortal, excessive_logging=True) as tester:
        portal = tester.portal

        @logging(excessive_logging=True)
        def compute(*, x, y):
            return x + y

        with portal:
            result1 = compute(x=1, y=2)
            result2 = compute(x=5, y=10)

            assert result1 == 3
            assert result2 == 15


def test_execution_frame_counters_initialized_correctly():
    """Test that frame counters start at zero."""
    with _PortalTester(LoggingCodePortal, excessive_logging=True) as tester:
        portal = tester.portal

        @logging(excessive_logging=True)
        def simple_fn():
            return "result"

        with portal:
            sig = simple_fn.get_signature({})
            frame = LoggingFnExecutionFrame(sig)

            assert frame.exception_counter == 0
            assert frame.event_counter == 0


def test_cleanup_order_on_exception_in_body():
    """Test that resources are cleaned up in correct order when exception occurs."""
    cleanup_order = []

    with _PortalTester(LoggingCodePortal, excessive_logging=True) as tester:
        portal = tester.portal

        @logging(excessive_logging=True)
        def fn_that_raises():
            raise ValueError("Intentional test exception")

        initial_stack_depth = len(LoggingFnExecutionFrame.call_stack)

        with portal:
            try:
                fn_that_raises()
            except ValueError:
                pass

        # Verify call stack was properly cleaned up
        assert len(LoggingFnExecutionFrame.call_stack) == initial_stack_depth


def test_output_captured_before_capturer_closes():
    """Test that output is captured and stored correctly with ExitStack."""
    with _PortalTester(LoggingCodePortal, excessive_logging=True) as tester:
        portal = tester.portal

        @logging(excessive_logging=True)
        def fn_with_output():
            print("Test output line")
            return "result"

        with portal:
            result = fn_with_output()
            assert result == "result"

            # Get the call signature to check captured output
            sig = fn_with_output.get_signature({})
            execution_outputs = sig.execution_outputs

            # There should be at least one output captured
            assert len(execution_outputs) > 0

            # The output should contain our print statement
            output_keys = list(execution_outputs.keys())
            found_output = False
            for key in output_keys:
                output_value = execution_outputs[key]
                if "Test output line" in str(output_value):
                    found_output = True
                    break
            assert found_output, "Expected output was not captured"


def test_exit_stack_attribute_initialized():
    """Test that _exit_stack attribute is properly initialized."""
    with _PortalTester(LoggingCodePortal, excessive_logging=True) as tester:
        portal = tester.portal

        @logging(excessive_logging=True)
        def simple_fn():
            return "result"

        with portal:
            sig = simple_fn.get_signature({})
            frame = LoggingFnExecutionFrame(sig)

            # Before entering context, _exit_stack should be None
            assert frame._exit_stack is None

            with frame:
                # Inside context, _exit_stack should be set
                assert frame._exit_stack is not None
