"""Output capture utilities for function execution logging.

Provides OutputCapturer, a context manager that simultaneously captures and
displays stdout, stderr, and logging output. Uses a "tee" strategy where
output is duplicated: sent to both the original destination (for normal
display) and to an internal buffer (for storage in execution logs).

Design Rationale:
    Simple redirection (e.g., sys.stdout = StringIO()) would suppress output
    from the user's view. The tee approach preserves normal output behavior
    while also capturing it for later analysis, making it suitable for both
    interactive use and production logging.
"""

import sys, io, logging, traceback


# TODO: see if we can use https://capturer.readthedocs.io/en/latest/index.html
# TODO: see if we can use similar functionality from pytest

class OutputCapturer:
    """Context manager that captures stdout, stderr, and logging output.

    Uses a dual-stream "tee" approach: output is sent to both the original
    streams (preserving normal display) and to an internal buffer (enabling
    capture). This ensures users see output in real-time while also storing
    it for later retrieval via get_output().

    Example:
        >>> with OutputCapturer() as capturer:
        ...     print("Hello")  # Prints normally AND is captured
        ...     logging.info("Test")  # Logged normally AND is captured
        >>> output = capturer.get_output()
        >>> assert "Hello" in output
        >>> assert "Test" in output
    """

    class _TeeStream:
        """Internal stream that duplicates output to two destinations.

        Duplicates all write() calls to both the original stream (for normal
        display) and a StringIO buffer (for capture). This enables simultaneous
        capture and display of stdout/stderr.

        Args:
            original: The original stream (stdout or stderr) to preserve.
            buffer: The StringIO buffer to capture output.
        """
        def __init__(self, original, buffer):
            self.original = original
            self.buffer = buffer

        def write(self, data):
            """Write data to both the original stream and the capture buffer.

            Args:
                data: The data to be written.
            """
            self.original.write(data)
            self.buffer.write(data)

        def flush(self):
            """Flush both streams to ensure all data is written."""
            self.original.flush()
            self.buffer.flush()

    class _CaptureHandler(logging.Handler):
        """Internal logging handler that captures and forwards log records.

        Captures logging output to a buffer while also forwarding records to
        the original handlers, preserving normal logging behavior.

        Args:
            buffer: The StringIO buffer to capture logging output.
            original_handlers: The original logging handlers to forward records to.
        """
        def __init__(self, buffer, original_handlers):
            super().__init__()
            self.buffer = buffer
            self.original_handlers = original_handlers

        def emit(self, record):
            """Emit a log record to both the capture buffer and original handlers.

            Args:
                record: The log record to be captured and forwarded.
            """
            msg = self.format(record)
            self.buffer.write(msg + '\n')
            for handler in self.original_handlers:
                handler.emit(record)

    def __init__(self):
        """Initialize the OutputCapturer.

        Sets up tee streams for stdout and stderr, and a capture handler
        for the logging system. All three output channels will be captured
        and duplicated when the capturer is used as a context manager.
        """
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        self.original_log_handlers = logging.root.handlers[:]
        self.captured_buffer = io.StringIO()
        self.tee_stdout = self._TeeStream(
            self.original_stdout, self.captured_buffer)
        self.tee_stderr = self._TeeStream(
            self.original_stderr, self.captured_buffer)
        self.capture_handler = self._CaptureHandler(
            self.captured_buffer, self.original_log_handlers)

    def __enter__(self):
        """Start capturing stdout, stderr, and logging output.

        Returns:
            The OutputCapturer instance for use as a context variable.
        """
        sys.stdout = self.tee_stdout
        sys.stderr = self.tee_stderr
        logging.root.handlers = [self.capture_handler]  # Temporarily replace existing handlers
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop capturing and restore stdout, stderr, and logging to original state.

        Args:
            exc_type: Exception class if an exception occurred, None otherwise.
            exc_val: Exception instance if an exception occurred, None otherwise.
            exc_tb: Traceback if an exception occurred, None otherwise.
        """
        if exc_type is not None:
            traceback.print_exc()
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        logging.root.handlers = self.original_log_handlers

    def get_output(self) -> str:
        """Retrieve all captured output as a single string.

        Returns:
            Combined stdout, stderr, and logging output captured during the
            context manager's lifetime.
        """
        return self.captured_buffer.getvalue()