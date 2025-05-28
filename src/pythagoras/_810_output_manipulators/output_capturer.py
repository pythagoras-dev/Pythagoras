import sys, io, logging, traceback


# TODO: see if we can use https://capturer.readthedocs.io/en/latest/index.html
# TODO: see if we can use similar functionality from pytest

class OutputCapturer:
    """
    Captures all output sent to stdout, stderr, and the logging system
    into a single stream. This class is useful for testing and debugging,
    where capturing output is necessary. It ensures that logged messages are
    both captured and printed normally.
    """

    class _TeeStream:
        """An internal class that duplicates output.

        The output is duplicated to both a specified original stream
        and a StringIO buffer. Used for capturing stdout and stderr
        while allowing normal output.
        """
        def __init__(self, original, buffer):
            """
            Initialize the _TeeStream object.
            Args:
                original: The original stream (stdout or stderr) to duplicate.
                buffer: The StringIO buffer to capture the output.
            """
            self.original = original
            self.buffer = buffer

        def write(self, data):
            """
            Write data to both the original stream and the buffer.
            Args:
                data: The data to be written.
            """
            self.original.write(data)
            self.buffer.write(data)

        def flush(self):
            """Flush original stream and buffer to ensure all data is written.
            """
            self.original.flush()
            self.buffer.flush()

    class _CaptureHandler(logging.Handler):
        """  An internal logging handler that captures logging output.

        It also forwards log records to the original logging handlers
        to maintain normal logging behavior.
        """
        def __init__(self, buffer, original_handlers):
            """
            Initialize the _CaptureHandler object.
            Args:
                buffer: The StringIO buffer to capture the logging output.
                original_handlers: The original logging handlers to forward log records.
            """
            super().__init__()
            self.buffer = buffer
            self.original_handlers = original_handlers

        def emit(self, record):
            """
            Emit a log record to the buffer and the original handlers.
            Args:
                record: The log record to be captured and forwarded.
            """
            msg = self.format(record)
            self.buffer.write(msg + '\n')
            for handler in self.original_handlers:
                handler.emit(record)

    def __init__(self):
        """ Initialize the OutputCapturer object.

        Sets up tee streams for stdout and stderr,
        and a capture handler for logging.
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
        """Redirect stdout, stderr, and logging output to the capturer.
        """
        sys.stdout = self.tee_stdout
        sys.stderr = self.tee_stderr
        logging.root.handlers = [self.capture_handler]  # Temporarily replace existing handlers
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Restore stdout, stderr, and logging output to their original state.
        """
        if exc_type is not None:
            traceback.print_exc()
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        logging.root.handlers = self.original_log_handlers

    def get_output(self):
        """Retrieve the captured output from the buffer.

        Returns a string containing all the output captured
        during the lifetime of the capturer.
        """
        return self.captured_buffer.getvalue()